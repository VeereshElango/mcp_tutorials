# MCP Tutorials 🚀

This repository contains **hands-on tutorials and example projects** for learning the **Model Context Protocol (MCP)**.  
MCP is an open protocol for connecting Large Language Models (LLMs) to external tools, data sources, and applications in a standardized way.

Each tutorial shows how to build and run an MCP server and connect it to a **Streamlit UI** that uses an LLM to **plan tool calls** and then **execute them via MCP**.

---

## 📂 Repository Structure

```bash
mcp_tutorials/
├── README.md              # General repo guide (this file)
├── main.py                # Simple entry script placeholder
├── pyproject.toml         # Project metadata (PEP 621)
├── requirements.txt       # Dependency pins for tutorials
├── .python-version        # Suggested Python version
│
├── 1_tutorial/            # Math MCP Server + UI
│   ├── README.md
│   ├── math_mcp_server.py
│   └── ui.py
│
└── 2_tutorial/            # Weather MCP Server + UI
    ├── README.md
    ├── weather_mcp_server.py
    └── ui.py
```

- **1_tutorial/** → Basic math tools (add, subtract, multiply, divide) exposed via MCP.  
- **2_tutorial/** → Weather server that queries the Open-Meteo API and presents results in a Streamlit UI.

---

## ⚙️ Prerequisites

- **Python** → Recommended **3.12** (or the latest stable supported by Streamlit and the OpenAI SDK).  
- **uv** → Fast Python package manager (optional but recommended).  
- **OpenAI API key** → Required for the LLM planning step.

> Install **uv** 
>
> - macOS/Linux:
>   ```bash
>   curl -LsSf https://astral.sh/uv/install.sh | sh
>   ```
> - Windows (PowerShell):
>   ```powershell
>   iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
>   ```

> Follow the official installation guide: https://docs.astral.sh/uv/getting-started/installation/


## 🚀 Setup

### 1) Clone the repo
```bash
git clone https://github.com/VeereshElango/mcp_tutorials.git
cd mcp_tutorials
```

### 2) Create & activate a virtual environment
Using **uv** (recommended):
```bash
uv venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (cmd)
.venv\Scripts\activate
```

### 3) Install dependencies
```bash
uv pip install -r requirements.txt
```

---

## 🔑 Set OpenAI API Key

Get your key from https://platform.openai.com/account/api-keys and set it as an environment variable:

**macOS/Linux**
```bash
export OPENAI_API_KEY=your-key-here
```

**Windows (PowerShell)**
```powershell
$env:OPENAI_API_KEY="your-key-here"
```

**Windows (Command Prompt)**
```cmd
setx OPENAI_API_KEY "your-key-here"
```
> **Note:** After using `setx`, restart your command prompt or IDE for the environment variable to take effect.
---

## ▶️ Run the Tutorials

### 🧮 Tutorial 1 — Math MCP Server

**Terminal 1: start the server**
```bash
cd 1_tutorial
python math_mcp_server.py
```

**Terminal 2: start the UI**
```bash
cd 1_tutorial
streamlit run ui.py
```

---

### ⛅ Tutorial 2 — Weather MCP Server

**Terminal 1: start the server**
```bash
cd 2_tutorial
python weather_mcp_server.py
```

**Terminal 2: start the UI**
```bash
cd 2_tutorial
streamlit run ui.py
```

---

## ❓ Troubleshooting

- **Port in use (8000)** → Stop other services or export a different `PORT` and update your client base URL.  
- **OPENAI_API_KEY missing** → Ensure the variable is set in the same shell before launching Streamlit.  
- **SSL/Proxy issues** → Try from a clean network or set system proxy variables if required.

---

## 🌍 Learn More

- Official docs: https://modelcontextprotocol.io/docs/getting-started/intro  
- Intro video: https://www.youtube.com/watch?v=N3vHJcHBS-w  
- MCP vs APIs vs RAG: https://medium.com/nane-limon/mcp-model-context-protocol-mcp-vs-traditional-apis-rag-81eebff65111  
- Decision framework: https://blog.stackademic.com/mcp-vs-fine-tuning-vs-rag-the-developers-decision-framework-a410df615a14

---

## 📜 License

MIT — feel free to use and adapt these tutorials.
