import inspect
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from mcp_server.tools import TOOL_REGISTRY

router = APIRouter()


@router.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    if tool_name not in TOOL_REGISTRY:
        return JSONResponse(
            status_code=404,
            content={
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(TOOL_REGISTRY.keys()),
            },
        )

    body = await request.json()
    fn = TOOL_REGISTRY[tool_name]

    sig = inspect.signature(fn)
    valid_params = set(sig.parameters.keys())
    kwargs = {k: v for k, v in body.items() if k in valid_params}

    try:
        result = await fn(**kwargs)
        return {"tool": tool_name, "result": result}
    except TypeError as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid arguments: {str(e)}", "tool": tool_name},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Tool execution failed: {str(e)}", "tool": tool_name},
        )


@router.get("/tools")
async def list_tools():
    tools = []
    for name, fn in TOOL_REGISTRY.items():
        sig = inspect.signature(fn)
        params = {
            pname: str(p.annotation) if p.annotation != inspect.Parameter.empty else "any"
            for pname, p in sig.parameters.items()
        }
        tools.append({"name": name, "parameters": params})
    return {"tools": tools}
