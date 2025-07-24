from fastmcp import FastMCP

# Initialize FastMCP
# This instance will be used as a decorator (@mcp.expose()) to register
# FastAPI endpoints as callable tools for the Gemini model.
mcp = FastMCP()
