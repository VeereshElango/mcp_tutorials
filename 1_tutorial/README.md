# Tutorial 1 — Math MCP Server & UI 🧮

A minimal example showing how an LLM can **plan** math operations and then **execute** them via an **MCP (Model Context Protocol) server**.  
You’ll run a small FastMCP server exposing `add`, `subtract`, `multiply`, and `divide`, and a Streamlit UI that asks an LLM to produce a JSON plan of tool calls.

---

## What you’ll learn

- How to expose functions as MCP **tools** over HTTP.
- How to have an LLM **plan** a chain of tool calls (no math done by the LLM itself).
- How to call those tools from a **Streamlit** client app.

---

## Folder contents

```
1_tutorial/
├── README.md              # This file
├── math_mcp_server.py     # FastMCP server exposing math tools
└── ui.py                  # Streamlit app that plans + executes tool calls
```

---

## Prerequisites

- **Python**: recommended 3.12
- **Dependencies**: installed at the repo root via `requirements.txt`
- **OpenAI API key** (for the planning step in the UI)

> If you use `uv`:
> - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
> - Windows (PowerShell): `iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex`

---
## Run

Open **two terminals**.

### Terminal 1 — start the MCP server
```bash
# Activate virtual environment 
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Navigate to tutorial directory
cd 1_tutorial

python math_mcp_server.py
```
- Starts FastMCP on `http://0.0.0.0:8000/mcp` (listening on port **8000**).

### Terminal 2 — start the UI
```bash
# Activate virtual environment 
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

cd 1_tutorial
streamlit run ui.py
```
- Opens a local web UI.
- The app uses `OPENAI_API_KEY` and defaults to:
  - **Model**: `"gpt-3.5-turbo"` (change inside `ui.py` or via a text input in the sidebar)
  - **MCP base URL**: `http://127.0.0.1:8000/mcp`  
    (override by setting `MCP_BASE_URL` before launch if needed)

---

## How it works (quick)

1. You type a natural-language math question, e.g.  
   “What is **(12 + 8) \* 8**?”
2. The LLM replies with a **JSON array** describing tool calls, e.g.
   ```json
   [
     {"func": "add", "a": 12, "b": 8},
     {"func": "multiply", "a": "RESULT_1", "b": 8}
   ]
   ```
   - `RESULT_1` means “use the output of step 1”.
3. The UI **executes** each step against the MCP server and displays the outputs.

---

## Tool contract (server)

The server exposes four tools:

```text
add(a: float, b: float) -> float
subtract(a: float, b: float) -> float      # returns a - b
multiply(a: float, b: float) -> float
divide(a: float, b: float) -> float        # b ≠ 0
```

- All tools return a `float`.
- `divide` raises an error on division by zero (the UI will display it).

---


## Try these sample prompts

- `What is (15 - 3) * (4 + 2) / 3?`
- `Add 12.5 and 7.25, then divide by 2`
- `Compute 2 * 3 * 4 using a chain of steps`

Tip: The UI shows the **planned steps** JSON and the **executed outputs** per step.

---

## Troubleshooting

- **UI says “OpenAI API key is not set”**  
  Ensure `OPENAI_API_KEY` is exported **in the same shell** you start Streamlit from.

- **Can’t connect to MCP / connection refused**  
  Make sure the server is running in Terminal 1 and that `MCP_BASE_URL` matches  
  (default: `http://127.0.0.1:8000/mcp`).

- **Port 8000 already in use**  
  Stop the conflicting process or change the server port in `math_mcp_server.py` and update `MCP_BASE_URL`.

- **Division by zero error**  
  This is expected behavior from the `divide` tool; adjust your input.

---

## Extend the tutorial (ideas)

- Add a `power(a, b)` tool and teach the planner to use it.
- Add **input validation** in the UI (numeric checks, max chain length).
- Log each tool call with timing and present an execution timeline.
- Swap models (e.g., a cheaper planner) via the UI sidebar.

---

## License

MIT — please use and adapt freely.
