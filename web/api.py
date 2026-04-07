from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from service.api_service import (
    get_options,
    list_styles,
    interview_session,
    reset_session,
    question_bank_tree,
    get_progress,
)

app = FastAPI(title="Interview Agent API", version="0.1.0")


class SessionRequest(BaseModel):
    message: str = ""
    session_id: Optional[str] = None
    tech_stack: Optional[list[str]] = ["Python", "Django", "MySQL", "Redis"]
    position: Optional[str] = "后端开发工程师"
    style: Optional[str] = "professional"
    difficulty: Optional[str] = "medium"
    mode: Optional[str] = "dual_agent"
    ui_mode: Optional[str] = None
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    resume_info: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    action: str = "interview"
    reply: str
    message_to_user: Optional[str] = None
    current_stage: Optional[str] = None
    stage_name: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str


@app.get("/")
def root():
    return {"message": "Interview Agent API is running"}


@app.get("/options")
def get_options_view():
    return get_options()


@app.get("/styles")
def list_styles_view():
    return list_styles()


@app.post("/interview", response_model=SessionResponse)
def interview_session_view(req: SessionRequest):
    try:
        result = interview_session(
            message=req.message,
            session_id=req.session_id,
            tech_stack=req.tech_stack,
            position=req.position,
            style=req.style,
            difficulty=req.difficulty,
            mode=req.mode,
            candidate_id=req.candidate_id,
            job_id=req.job_id,
            resume_info=req.resume_info,
        )
        return SessionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/session/reset")
def reset_session_view(req: ResetRequest):
    try:
        return reset_session(req.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/question-bank/tree")
def question_bank_tree_view():
    try:
        return question_bank_tree()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/session/{session_id}/progress")
def get_progress_view(session_id: str):
    try:
        return get_progress(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
