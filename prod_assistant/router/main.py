import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
import asyncio

from prod_assistant.workflow.agentic_rag_workflow_with_mcp import AgenticRAG

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- FastAPI Endpoints ----------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/get", response_class=HTMLResponse)
async def chat(msg: str = Form(...)):
    """Call the Agentic RAG workflow."""
    rag_agent = await AgenticRAG.async_init()
    answer = await rag_agent.run(msg)   # run() already returns final answer string
    print(f"Agentic Response: {answer}")
    return answer


def run_server():
    """Entry point for the ecomm-assistant command."""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4, reload=True)


if __name__ == "__main__":
    run_server()