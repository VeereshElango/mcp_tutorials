# math_mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP(name="Math MCP Server", instructions="Provides basic math tools.")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a"""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b"""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b

if __name__ == "__main__":
    # Run the server over HTTP transport with streaming support
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
