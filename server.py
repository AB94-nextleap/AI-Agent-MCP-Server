import asyncio
import sys
import json
import os
from fastapi import FastAPI, HTTPException, status, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from auth import get_google_credentials
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

app = FastAPI(title="Google Workspace MCP Server")

# Request Schemas
class DocAppendPayload(BaseModel):
    doc_id: str
    content: str

class EmailDraftPayload(BaseModel):
    to: List[str]
    subject: str
    body: Optional[str] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None

def prompt_approval(action_name: str, payload: dict) -> bool:
    """
    Console approval gate. Prints action details and waits for user terminal input.
    """
    print("\n" + "=" * 50)
    print(f"ACTION REQUESTED: {action_name}")
    print("PAYLOAD:")
    
    # Print trimmed values to console to avoid page-long HTML logs
    trimmed_payload = {}
    for k, v in payload.items():
        if isinstance(v, str) and len(v) > 300:
            trimmed_payload[k] = v[:300] + " ... [TRUNCATED]"
        else:
            trimmed_payload[k] = v
            
    print(json.dumps(trimmed_payload, indent=2))
    print("=" * 50)
    
    sys.stdout.flush()
    try:
        # Prompt user in terminal
        ans = input("Approve? (y/n): ").strip().lower()
        return ans in ['y', 'yes']
    except Exception as e:
        print(f"Error reading approval: {e}")
        return False

async def get_user_approval(action_name: str, payload: dict) -> bool:
    """Runs the blocking terminal prompt in a separate thread."""
    return await asyncio.to_thread(prompt_approval, action_name, payload)

def verify_api_key(x_api_key: str = Header(...)):
    expected_key = os.environ.get("API_KEY")
    if not expected_key:
        if os.environ.get("ENV") == "production":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Production environment requires the API_KEY variable to be set."
            )
        return
    if x_api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key.")

@app.post("/append_to_doc", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def api_append_to_doc(payload: DocAppendPayload):
    # 1. Ask for user approval in terminal (skip in production)
    if os.environ.get("ENV") != "production":
        approved = await get_user_approval("append_to_doc", payload.model_dump())
        if not approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Action rejected by user."
            )
        
    # 2. Execute Doc write
    try:
        creds = get_google_credentials()
        result = append_to_doc(payload.doc_id, payload.content, creds)
        return {"status": "success", "result": result}
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=500, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Docs API error: {str(e)}")

@app.post("/create_email_draft", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def api_create_email_draft(payload: EmailDraftPayload):
    # 1. Ask for user approval in terminal (skip in production)
    if os.environ.get("ENV") != "production":
        approved = await get_user_approval("create_email_draft", payload.model_dump())
        if not approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Action rejected by user."
            )
        
    # 2. Execute Gmail Draft creation
    try:
        creds = get_google_credentials()
        result = create_email_draft(
            to=payload.to,
            subject=payload.subject,
            body=payload.body,
            html_body=payload.html_body,
            text_body=payload.text_body,
            creds=creds
        )
        return {"status": "success", "result": result}
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=500, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Google Workspace MCP server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
