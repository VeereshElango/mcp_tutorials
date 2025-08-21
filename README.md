# MCP Tutorials

This repository contains tutorials and example projects for Model Context Protocol (MCP) servers and related UI applications. It is organized into multiple folders, each demonstrating different features and use cases.

## Structure

- `main.py`: Entry point or utility script.
- `1_tutorial/`: Contains math MCP server and UI example.
- `2_tutorial/`: Contains weather MCP server and UI example.
- `requirements.txt`: Python dependencies for all tutorials.
- `pyproject.toml`: Project metadata and configuration.

---

## VS Code Setup

1. **Install VS Code**: Download and install [Visual Studio Code](https://code.visualstudio.com/).
2. **Recommended Extensions**:
	 - Python (ms-python.python)
	 - Pylance (ms-python.vscode-pylance)
	 - Jupyter (ms-toolsai.jupyter)
	 - Streamlit (streamlit.streamlit)
3. **Open the project folder**: Use `File > Open Folder...` and select the repository root.

---

## Setup `uv` Package

[`uv`](https://github.com/astral-sh/uv) is a fast Python package manager and virtual environment tool.

### Install `uv`

Open a terminal and run:

```cmd
pip install uv
```

---

## Using `uv` to Setup Virtual Environment and Install Requirements


### 1. Create a virtual environment

**Windows:**
```cmd
uv venv .venv
```

**Mac/Linux:**
```bash
uv venv .venv
```

### 2. Activate the virtual environment

**Windows (cmd):**
```cmd
.venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies from `requirements.txt`

**All platforms:**
```bash
uv pip install -r requirements.txt
```

---

## Additional `uv` Commands

- Upgrade all packages:
	```cmd
	uv pip install --upgrade -r requirements.txt
	```
- List installed packages:
	```cmd
	uv pip list
	```

---

## Getting Started


---

## Setting Your OpenAI API Key

Some tutorials require an OpenAI API key for access to language models. You can set this key as an environment variable.

### 1. Obtain your API key

Get your key from https://platform.openai.com/account/api-keys

### 2. Set the environment variable

**Windows (cmd):**
```cmd
set OPENAI_API_KEY=your-key-here
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-key-here"
```

**Mac/Linux:**
```bash
export OPENAI_API_KEY=your-key-here
```

### 3. Test if the key is set correctly

**Windows (cmd):**
```cmd
echo %OPENAI_API_KEY%
```

**Windows (PowerShell):**
```powershell
echo $env:OPENAI_API_KEY
```

**Mac/Linux:**
```bash
echo $OPENAI_API_KEY
```

If your key is displayed, the environment variable is set correctly.

---

After setting up the environment and API key, you can run the tutorials or servers as described in each folder's README or script comments.
