"""
Workshop: LLM + Streamable HTTP MCP (Math Tools) with Streamlit
================================================================

This app shows how to:
  1) Ask an LLM to *plan* a math calculation as a chain of tool calls (add, subtract, multiply, divide), and
  2) Execute those tool calls against an MCP server that exposes the math tools over HTTP.

Prerequisites
-------------
- Python 3.9+
- `pip install streamlit openai fastmcp`
- An MCP server running locally that exposes tools named: `add`, `subtract`, `multiply`, `divide`.
  For example, a server listening at `http://127.0.0.1:8000/mcp`.
- An OpenAI API key (set `OPENAI_API_KEY` in your environment or Streamlit secrets).

Run
---
1) Make sure your MCP server is running.
2) Export your key: `export OPENAI_API_KEY=sk-...` (or use Streamlit secrets).
3) Start the app: `streamlit run workshop_app.py`

Notes
-----
- The LLM only *plans* the steps. It never computes directly; all math is done by the MCP tools.
- The LLM is instructed to output a JSON array with steps like:
  [{"func":"add","a":12,"b":8}, {"func":"multiply","a":"RESULT_1","b":8}]
- A later step can refer to an earlier output as `RESULT_N` (1-based).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import streamlit as st
from fastmcp import Client
from openai import OpenAI

# -----------------------------------------------------------------------------
# Configuration & constants
# -----------------------------------------------------------------------------
ALLOWED_FUNCS = {"add", "subtract", "multiply", "divide"}
DEFAULT_MODEL = "gpt-3.5-turbo"  # Use any chat-completions-capable model you prefer
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000/mcp")

SYSTEM_PROMPT = (
    "You are a math tool-calling assistant. "
    "Given a user question, break it into a step-by-step chain of JSON tool calls. "
    "Allowed tools: add, subtract, multiply, divide. "
    "Each tool call should be a JSON object: {\"func\":..., \"a\":..., \"b\":...}. "
    "Output a JSON array in correct calculation order. "
    "Use the result of a previous step as \"a\" or \"b\" in later steps as needed, by referring to it as RESULT_N where N is the 1-based step index.\n"
    "Example: What is (12 + 8) * 8?\n"
    "[{\"func\":\"add\",\"a\":12,\"b\":8}, {\"func\":\"multiply\",\"a\":\"RESULT_1\",\"b\":8}]\n"
)

# -----------------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------------
@dataclass
class ToolCall:
    """Represents a single tool call planned by the LLM."""
    func: str
    a: Any
    b: Any

    @classmethod
    def from_obj(cls, obj: Dict[str, Any]) -> "ToolCall":
        if not isinstance(obj, dict):
            raise ValueError("Step is not an object")
        func = obj.get("func")
        a = obj.get("a")
        b = obj.get("b")
        if func not in ALLOWED_FUNCS:
            raise ValueError(f"Invalid func '{func}'. Allowed: {sorted(ALLOWED_FUNCS)}")
        return cls(func=func, a=a, b=b)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
_code_fence_pattern = re.compile(r"^```[a-zA-Z0-9]*\n|\n```$", re.MULTILINE)


def strip_code_fences(text: str) -> str:
    """Remove Markdown code fences if the model wrapped JSON in ``` blocks."""
    return _code_fence_pattern.sub("", text).strip()


def coerce_number(x: Any) -> Any:
    """Coerce numeric-looking strings to int/float. Leaves other types unchanged."""
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        try:
            if "." in x:
                return float(x)
            return int(x)
        except ValueError:
            return x
    return x


def resolve_result_refs(value: Any, prior: Dict[int, Any]) -> Any:
    """Replace 'RESULT_N' references with the actual numeric output from step N."""
    if isinstance(value, str) and value.startswith("RESULT_"):
        try:
            idx = int(value.split("_", 1)[1])
            return prior[idx]
        except Exception:
            raise ValueError(f"Bad result reference: {value}")
    return value

# -----------------------------------------------------------------------------
# LLM planning step
# -----------------------------------------------------------------------------

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def plan_tool_chain(question: str, model: str = DEFAULT_MODEL) -> List[ToolCall]:
    """Ask the LLM to produce a JSON array of tool calls for the math question."""
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    raw = resp.choices[0].message.content or ""
    logging.info("LLM raw response: %s", raw)
    cleaned = strip_code_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON tool chain: {e}\nRaw: {raw}") from e
    if not isinstance(parsed, list):
        raise ValueError("Expected a JSON array of tool calls")

    steps: List[ToolCall] = []
    for i, obj in enumerate(parsed, start=1):
        try:
            steps.append(ToolCall.from_obj(obj))
        except Exception as e:
            raise ValueError(f"Invalid step {i}: {e}") from e
    if not steps:
        raise ValueError("No steps generated by the LLM")
    return steps

# -----------------------------------------------------------------------------
# MCP execution step
# -----------------------------------------------------------------------------
async def execute_chain_via_mcp(steps: List[ToolCall]) -> List[Dict[str, Any]]:
    """Execute each planned step against the MCP server.

    Returns a list of dicts with keys: func, args, output, error (optional).
    Stops on the first tool error and includes the error in the corresponding step.
    """
    results: List[Dict[str, Any]] = []
    prior_outputs: Dict[int, Any] = {}

    client = Client(MCP_BASE_URL)

    async with client:
        for i, step in enumerate(steps, start=1):
            # Resolve RESULT_N references and coerce numeric strings
            a = coerce_number(resolve_result_refs(step.a, prior_outputs))
            b = coerce_number(resolve_result_refs(step.b, prior_outputs))

            step_view = {"func": step.func, "args": {"func": step.func, "a": a, "b": b}}

            try:
                result = await client.call_tool(step.func, {"a": a, "b": b}, raise_on_error=False)
                output = result.data if result.data is not None else "<no output>"

                step_view["output"] = output
                results.append(step_view)

                if getattr(result, "is_error", False):
                    # Preserve an error marker and stop executing further steps
                    step_view["error"] = "Tool error"
                    break

                # Save output for RESULT_N references in later steps
                prior_outputs[i] = output

            except Exception as e:  # Network errors, timeouts, etc.
                step_view["error"] = f"Execution error: {e}"
                results.append(step_view)
                break

    return results

# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="LLM + MCP: Math Tools", page_icon="🧮")
    st.title("Math with LLM + Streamable HTTP MCP (with call info)")

    # Early key check with a friendly message
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key is not set. Please set OPENAI_API_KEY in your environment or Streamlit secrets.")
        st.stop()

    with st.sidebar:
        st.header("Settings")
        st.caption("These are read at runtime.")
        st.text_input("MCP base URL", value=MCP_BASE_URL, disabled=True, help="Set MCP_BASE_URL env var to change.")
        model = st.text_input("OpenAI model", value=DEFAULT_MODEL, help="Any chat-completions-capable model.")

    st.write("Enter a plain-English math question. The LLM will plan the steps; the MCP tools will compute them.")

    with st.form("solver", clear_on_submit=False):
        question = st.text_input("Math question", placeholder="What is (12 + 8) * 8?")
        submitted = st.form_submit_button("Solve")

    if not submitted or not question:
        st.stop()

    with st.status("Planning with LLM…", expanded=False):
        try:
            steps = plan_tool_chain(question, model=model)
        except Exception as e:
            st.error(str(e))
            return

    st.subheader("Planned steps (from LLM)")
    st.json([step.__dict__ for step in steps])

    st.subheader("Executing against MCP tools")
    with st.status("Calling tools…", expanded=True):
        run = asyncio.run(execute_chain_via_mcp(steps))

    # Pretty print each step result
    for idx, step in enumerate(run, start=1):
        st.markdown(f"**Step {idx}:** `{step.get('func', '')}`")
        st.json(step.get("args", {}))
        if "output" in step:
            st.success(f"Output: {step['output']}")
        if "error" in step:
            st.error(step["error"])
            break

    st.caption("Tip: Try a multi-step question such as 'Compute (15 - 3) * (4 + 2) / 3'.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
