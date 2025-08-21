# 1_tutorial: Math MCP Server & UI

This tutorial demonstrates how to set up and run a simple Model Context Protocol (MCP) server for math operations, along with a Streamlit-based UI to interact with the server.

## Introduction

- The MCP server provides math-related APIs.
- The Streamlit UI allows users to interact with the MCP server through a web interface.

## How to Run


### 0. Change Directory

Open a terminal and navigate to the tutorial folder:

```cmd
cd 1_tutorial
```

### 1. Start the MCP Server

In the same terminal, run:

```cmd
python math_mcp_server.py
```

The server will start and listen for requests.

### 2. Start the Streamlit UI

Open a second terminal, navigate to the same folder, and run:

```cmd
cd 1_tutorial
```

If you haven't already activated your virtual environment, do so now:

```cmd
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

Then run the Streamlit UI:

```cmd
streamlit run ui.py
```

This will launch the UI in your browser, allowing you to interact with the MCP server.

---

## Notes

- Ensure your virtual environment is activated and dependencies are installed before running the scripts.
- The MCP server and UI should be run in separate terminal windows.
- For more details, refer to the main project README.
