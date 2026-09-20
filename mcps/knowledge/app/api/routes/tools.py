from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.schemas.knowledge import LookupQuery
from app.tools import university_knowledge_lookup as lookup_tool

router = APIRouter(prefix="/v1")

class CallRequest(BaseModel):
    name: str
    arguments: dict = {}

TOOL_SCHEMA = lookup_tool.TOOL_SCHEMA

@router.get("/tools")
def list_tools():
    return {"tools": [TOOL_SCHEMA]}

@router.post("/tools/call")
def call_tool(req: CallRequest):
    if req.name == "university_knowledge_lookup":
        args_dict = req.arguments if isinstance(req.arguments, dict) else {}
        # Normalize string arguments to keyword
        if isinstance(args_dict, str):
            args_dict = {"keyword": args_dict}
        try:
            args = LookupQuery.model_validate(args_dict)
        except Exception:
            args = LookupQuery()
        result = lookup_tool.execute(
            domain=args.domain or "",
            keyword=args.keyword or "",
            faculty=args.faculty or "",
        )
        return {
            "status": "success",
            "query": req.name,
            "arguments": args_dict,
            "data": result,
        }
    raise HTTPException(status_code=404, detail=f"Tool {req.name} not found")
