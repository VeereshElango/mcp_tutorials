# Tutorial 3 — Excel-powered MCP Challenge 🧩

## Why do this?
- Turn a plain **Excel** file into an **LLM-queryable dataset** using **MCP**.  
- Practice building a **tool-calling UI** that answers natural-language questions.  
- Learn to handle **live data changes** (reload on file edits) without restarting apps.

---

## Goal (concise)
Build an **MCP server** + **Streamlit UI** that lets users query the Excel file for:
- **Teams** (members, counts, ownership)
- **Projects** (by name, team, owner)
- **Status** (Active/On hold/Done, blockers, due dates)
- **Other attributes** (priority, tags, milestones, etc.)

…and while the app is running, the user can **edit the Excel file** and **re-run a query** to see changes reflected immediately.

---

## Dataset
- File: `3_challenge/SmartFactory_Team_Projects_detailed.xlsx`  
- Treat the **first sheet** as canonical. Use the **header row** as column names.  
- Detect columns **dynamically** (do not hardcode names).

> ⚠️ Install the Excel engine: `uv pip install openpyxl` (or add to `requirements.txt`).

---

## Requirements
1. **MCP Server** (you create it, e.g., `excel_mcp_server.py`)
   - Reads the Excel **fresh** for every request (or reloads on file mtime change).

2. **UI** (you create it, e.g., `ui.py` with Streamlit)
   - Accepts **natural-language prompts** (e.g., “Show active projects for Team Alpha due this month”).

3. **Live edit flow**
   - With the server and UI running:
     1) User edits the Excel file (adds/updates a project row).  
     2) User submits a **new query**.  
     3) Results **reflect the changes** (no server/UI restart).

---
