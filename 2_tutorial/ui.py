"""
Workshop: LLM + Streamable HTTP MCP (Weather Tools) with Streamlit
==================================================================

This app shows how to:
  1) Ask an LLM to *plan* weather queries as a chain of tool calls
     (get_current_weather, get_daily_forecast), and
  2) Execute those tool calls against an MCP server that exposes the weather tools over HTTP.

Prerequisites
-------------
- Python 3.9+
- `pip install streamlit openai fastmcp pandas`
- A Weather MCP server running locally with tools:
    - get_current_weather(city, country_code?, state?, units?, lang?)
    - get_daily_forecast(city, days, country_code?, state?, units?, lang?)
  For example: http://127.0.0.1:8000/mcp
- An OpenAI API key (set OPENAI_API_KEY in env or Streamlit secrets).

Run
---
1) Start your Weather MCP server.
2) Export your key: `export OPENAI_API_KEY=sk-...`
3) `streamlit run workshop_weather_app.py`

Notes
-----
- The LLM only *plans* the steps. All data comes from the MCP tools.
- Output must be a JSON array like:
  [
    {"func": "get_current_weather", "city": "Södertälje", "country_code": "SE", "units": "metric"},
    {"func": "get_daily_forecast", "city": "Södertälje", "country_code": "SE", "days": 5}
  ]
- Later steps may reference earlier outputs as RESULT_N (1-based), though this app
  will simply pass the entire referenced object if used.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List

import streamlit as st
from fastmcp import Client
from openai import OpenAI

try:
    import pandas as pd
except Exception:
    pd = None  # We’ll gracefully fall back to JSON display if pandas is missing.

# -----------------------------------------------------------------------------
# Configuration & constants
# -----------------------------------------------------------------------------
ALLOWED_FUNCS = {"get_current_weather", "get_daily_forecast"}
DEFAULT_MODEL = "gpt-3.5-turbo"  # Any chat-completions-capable model works
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000/mcp")

DEFAULT_UNITS = os.getenv("WEATHER_DEFAULT_UNITS", "metric")  # metric | imperial
DEFAULT_LANG = os.getenv("WEATHER_DEFAULT_LANG", "en")
DEFAULT_FC_DAYS = int(os.getenv("WEATHER_DEFAULT_DAYS", "5"))

SYSTEM_PROMPT = (
    "You are a weather tool-calling assistant. "
    "Given a user request, output a JSON array of tool calls in execution order. "
    "Allowed tools:\n"
    " - get_current_weather(city, country_code?, state?, units?, lang?)\n"
    " - get_daily_forecast(city, days, country_code?, state?, units?, lang?)\n"
    "Rules:\n"
    " - Output ONLY a valid JSON array, no commentary.\n"
    " - Include parameters using the exact names above.\n"
    " - If units are not specified by the user, prefer 'metric'.\n"
    " - If language not specified, prefer 'en'.\n"
    " - If user asks for a multi-day outlook, use get_daily_forecast with an integer 'days'.\n"
    " - Later steps may refer to prior outputs as RESULT_N (1-based).\n"
    "Examples:\n"
    "Q: What's the weather in Södertälje right now?\n"
    "[{\"func\":\"get_current_weather\",\"city\":\"Södertälje\",\"country_code\":\"SE\",\"units\":\"metric\"}]\n"
    "Q: Weather in London today and 5-day forecast.\n"
    "[{\"func\":\"get_current_weather\",\"city\":\"London\",\"country_code\":\"GB\",\"units\":\"metric\"},"
    " {\"func\":\"get_daily_forecast\",\"city\":\"London\",\"country_code\":\"GB\",\"days\":5,\"units\":\"metric\"}]"
)

# -----------------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------------
@dataclass
class ToolCall:
    """Represents a single tool call planned by the LLM."""
    func: str
    args: Dict[str, Any]

    @classmethod
    def from_obj(cls, obj: Dict[str, Any]) -> "ToolCall":
        if not isinstance(obj, dict):
            raise ValueError("Step is not an object")
        func = obj.get("func")
        if func not in ALLOWED_FUNCS:
            raise ValueError(f"Invalid func '{func}'. Allowed: {sorted(ALLOWED_FUNCS)}")
        # Copy all remaining keys except 'func' as arguments
        args = {k: v for k, v in obj.items() if k != "func"}
        return cls(func=func, args=args)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
_code_fence_pattern = re.compile(r"^```[a-zA-Z0-9]*\n|\n```$", re.MULTILINE)

def strip_code_fences(text: str) -> str:
    """Remove Markdown code fences if the model wrapped JSON."""
    return _code_fence_pattern.sub("", text).strip()

def resolve_result_refs(value: Any, prior: Dict[int, Any]) -> Any:
    """Replace 'RESULT_N' with the actual prior output object."""
    if isinstance(value, str) and value.startswith("RESULT_"):
        try:
            idx = int(value.split("_", 1)[1])
            return prior[idx]
        except Exception:
            raise ValueError(f"Bad result reference: {value}")
    return value

def apply_defaults(func: str, args: Dict[str, Any], units_default: str, lang_default: str, fc_default_days: int) -> Dict[str, Any]:
    """Fill in sensible defaults if the LLM omits them."""
    out = dict(args)
    if func in {"get_current_weather", "get_daily_forecast"}:
        out.setdefault("units", units_default)
        out.setdefault("lang", lang_default)
    if func == "get_daily_forecast":
        out.setdefault("days", fc_default_days)
    return out

# -----------------------------------------------------------------------------
# LLM planning
# -----------------------------------------------------------------------------
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)

def plan_tool_chain(question: str, model: str = DEFAULT_MODEL) -> List[ToolCall]:
    """Ask the LLM to produce a JSON array of tool calls for the weather question."""
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
# MCP execution
# -----------------------------------------------------------------------------
async def execute_chain_via_mcp(steps: List[ToolCall], units_default: str, lang_default: str, fc_default_days: int) -> List[Dict[str, Any]]:
    """Execute each planned step against the MCP server.

    Returns a list of dicts with keys: func, args, output, error (optional).
    Stops on the first tool error.
    """
    results: List[Dict[str, Any]] = []
    prior_outputs: Dict[int, Any] = {}

    client = Client(MCP_BASE_URL)

    async with client:
        for i, step in enumerate(steps, start=1):
            # Fill in defaults, then resolve RESULT_N references inside arg values.
            prepared_args = apply_defaults(step.func, step.args, units_default, lang_default, fc_default_days)
            for k, v in list(prepared_args.items()):
                prepared_args[k] = resolve_result_refs(v, prior_outputs)

            step_view = {"func": step.func, "args": {"func": step.func, **prepared_args}}

            try:
                result = await client.call_tool(step.func, prepared_args, raise_on_error=False)
                output = result.data if result.data is not None else "<no output>"
                step_view["output"] = output
                results.append(step_view)

                if getattr(result, "is_error", False):
                    step_view["error"] = "Tool error"
                    break

                prior_outputs[i] = output

            except Exception as e:
                step_view["error"] = f"Execution error: {e}"
                results.append(step_view)
                break

    return results

# -----------------------------------------------------------------------------
# Presentation helpers
# -----------------------------------------------------------------------------
def render_current(block: Dict[str, Any]) -> None:
    loc = block.get("location", {}) or {}
    cur = block.get("current", {}) or {}

    st.markdown(f"**{loc.get('name', 'Location')}** — {loc.get('country','')}  \n"
                f"Timezone: {loc.get('timezone','?')}  \n"
                f"Coords: {loc.get('latitude','?')}, {loc.get('longitude','?')}")
    cols = st.columns(3)
    cols[0].metric("Temperature", f"{cur.get('temperature','?')} {cur.get('temperature_unit','')}")
    cols[1].metric("Humidity", f"{cur.get('relative_humidity','?')}%")
    cols[2].metric("Wind", f"{cur.get('wind_speed','?')} (dir {cur.get('wind_direction','?')}°)")
    st.write(f"**Conditions:** {cur.get('weather_description','Unknown')} • Observed at: {cur.get('observed_at','?')}")

def render_forecast(block: Dict[str, Any]) -> None:
    loc = block.get("location", {}) or {}
    days = block.get("daily", []) or []
    st.markdown(f"**Forecast for {loc.get('name','Location')}** — {loc.get('country','')}")
    if not days:
        st.info("No daily forecast data.")
        return
    if pd:
        df = pd.DataFrame(days)
        # Reorder columns if present
        cols = [c for c in ["date","weather_description","temp_min","temp_max","precipitation_sum","wind_speed_max"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True)
        # Optional quick chart if temp columns exist
        if {"date","temp_min","temp_max"}.issubset(df.columns):
            st.line_chart(df.set_index("date")[["temp_min","temp_max"]])
    else:
        st.json(days)

def pretty_render_step(step: Dict[str, Any]) -> None:
    """Pretty-print a single executed step with custom formatting for known tools."""
    st.markdown(f"**Tool:** `{step.get('func','')}`")
    st.json(step.get("args", {}))
    if "output" in step:
        out = step["output"]
        if isinstance(out, dict) and step.get("func") == "get_current_weather":
            render_current(out)
        elif isinstance(out, dict) and step.get("func") == "get_daily_forecast":
            render_forecast(out)
        else:
            st.json(out)
    if "error" in step:
        st.error(step["error"])

# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="LLM + MCP: Weather Tools", page_icon="⛅")
    st.title("Weather with LLM + Streamable HTTP MCP")

    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key is not set. Please set OPENAI_API_KEY in your environment or Streamlit secrets.")
        st.stop()

    with st.sidebar:
        st.header("Settings")
        st.caption("These are read at runtime.")
        st.text_input("MCP base URL", value=MCP_BASE_URL, disabled=True, help="Set MCP_BASE_URL env var to change.")
        model = st.text_input("OpenAI model", value=DEFAULT_MODEL, help="Any chat-completions-capable model.")
        st.divider()
        units_default = st.selectbox("Default units", ["metric", "imperial"], index=0 if DEFAULT_UNITS=="metric" else 1)
        lang_default = st.text_input("Default language (IETF code)", value=DEFAULT_LANG)
        fc_default_days = st.slider("Default forecast days (if omitted by LLM)", min_value=1, max_value=16, value=DEFAULT_FC_DAYS)

    st.write("Enter a natural-language weather question. The LLM will plan tool calls; the MCP tools will fetch the data.")

    with st.form("weather", clear_on_submit=False):
        question = st.text_input("Weather question", placeholder="Weather in Södertälje now and 5-day forecast?")
        submitted = st.form_submit_button("Get Weather")

    if not submitted or not question:
        st.stop()

    with st.status("Planning with LLM…", expanded=False):
        try:
            steps = plan_tool_chain(question, model=model)
        except Exception as e:
            st.error(str(e))
            return

    st.subheader("Planned steps (from LLM)")
    st.json([{"func": s.func, **s.args} for s in steps])

    st.subheader("Executing against MCP tools")
    with st.status("Calling tools…", expanded=True):
        run = asyncio.run(execute_chain_via_mcp(steps, units_default, lang_default, fc_default_days))

    for step in run:
        pretty_render_step(step)
        if "error" in step:
            break

    st.caption("Try: “Give me the current weather in Stockholm and a 3-day forecast in imperial units.”")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
