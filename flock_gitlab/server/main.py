from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from flock_gitlab.agents.orchestrator import orchestrator


app = FastAPI(
    title="Flock GitLab Tool",
    description="A reimagined GitLab tool using flock-core and specialized agents.",
    version="0.1.0",
)

class ToolInfo(BaseModel):
    name: str
    description: str
    version: str

@app.get("/")
async def get_tool_info():
    """
    Returns basic information about the tool.
    """
    return {
        "name": "Flock GitLab Tool",
        "description": "A reimagined GitLab tool using flock-core and specialized agents.",
        "version": "0.1.0",
        "status": "running"
    }

# Returns the Open WebUI tool spec
@app.get("/tools")
async def get_tools():
    """
    Returns the list of available tools (agents).
    This is dynamically populated by the agent orchestrator.
    """
    return {"tools": orchestrator.get_all_tool_defs()}


class ToolCall(BaseModel):
    tool: str
    params: dict

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, params: dict):
    """
    Executes a specific tool (agent).
    """
    try:
        # The `confirmed` flag is a simple way to handle the second step of an approval flow.
        confirmed = params.pop("confirmed", False)
        
        result = await orchestrator.dispatch(tool_name, **params)

        # If the result indicates that approval is required, return it directly.
        # The client (e.g., Open WebUI) would then need to handle this and allow the user to confirm.
        if result.get("requires_approval") and not confirmed:
            return result

        # If confirmation is received, re-dispatch without the approval check.
        # This is a simplified simulation. A real implementation would be more robust.
        if confirmed:
             agent = orchestrator.agents[tool_name]
             return await agent.execute(**params)

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
