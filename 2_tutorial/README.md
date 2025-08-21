# 2_tutorial: Weather MCP Server & UI

This tutorial guides you through launching a Model Context Protocol (MCP) server for weather data and a Streamlit UI to interact with it.

## Overview

- The MCP server exposes weather-related APIs.
- The Streamlit UI provides a user-friendly interface to communicate with the MCP server.

## Steps to Run

### 0. Navigate to the Tutorial Directory

Open a terminal and move to the tutorial folder:

```cmd
cd 2_tutorial
```

### 1. Launch the MCP Server

In the terminal, start the server:

```cmd
python weather_mcp_server.py
```

The server will begin running and accept requests.

### 2. Start the Streamlit UI

Open a second terminal, change to the same directory, and execute:

```cmd
streamlit run ui.py
```

This will open the UI in your browser, enabling you to interact with the weather MCP server.

---

## Notes

- Activate your virtual environment and install dependencies before running the scripts.
- Run the MCP server and UI in separate terminal windows.
- For more details, refer to the main project README.

---

## Notes

- Ensure your virtual environment is activated and dependencies are installed before running the scripts.
- The MCP server and UI should be run in separate terminal windows.
- For more details, refer to the main project README.
