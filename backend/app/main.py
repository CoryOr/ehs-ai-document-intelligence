# main.py
"""API for uploading, questioning, reviewing and reporting on EHS documents."""
from __future__ import annotations

from io import BytesIO
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .reports import build_report
from .services import MAX_BYTES, answer_question, index_document, list_documents

from .agent import run_agent

load_dotenv()  # Load repo-root .env when launched from repo root or backend dir.
app = FastAPI(title="EHS Document Intelligence", version="0.1.0")


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1500)


class Review(BaseModel):
    focus: str = Field(default="Review the available safety policies and incident records for potential gaps.", max_length=1500)


class Source(BaseModel):
    marker: str
    filename: str
    locator: str
    excerpt: str


class ExportRequest(BaseModel):
    title: str = Field(default="EHS Document Intelligence Report", max_length=120)
    answer: str = Field(min_length=1, max_length=30000)
    sources: list[Source] = Field(default_factory=list, max_length=12)
    format: Literal["pdf", "docx", "xlsx"]

class AgentRequest(BaseModel):
    request: str = Field(min_length=3, max_length=1500)


@app.post("/api/agent")
def agent_request(payload: AgentRequest) -> dict:
    try:
        return run_agent(payload.request)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent failed: {type(exc).__name__}"
        ) from exc


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/documents")
def documents() -> dict:
    return {"documents": list_documents()}


@app.post("/api/upload")
async def upload(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Choose a file")
    try:
        data = await file.read(MAX_BYTES + 1)
        result = index_document(data, file.filename)
        return {"document": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Document indexing failed: {type(exc).__name__}") from exc
    finally:
        await file.close()


@app.post("/api/chat")
def chat(payload: Question) -> dict:
    try:
        return answer_question(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {type(exc).__name__}") from exc


@app.post("/api/analyze")
def analyze(payload: Review) -> dict:
    try:
        return answer_question(payload.focus, review=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {type(exc).__name__}") from exc


@app.post("/api/export")
def export(payload: ExportRequest):
    data, mime, extension = build_report(payload.title, payload.answer, [x.model_dump() for x in payload.sources], payload.format)
    return StreamingResponse(
        BytesIO(data), media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="ehs-analysis.{extension}"'},
    )
