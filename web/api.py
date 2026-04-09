import json
from collections.abc import Generator
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from service.api_service import (
    get_options,
    list_styles,
    reset_session,
    question_bank_tree,
    get_progress,
)
from service.config import InterviewConfig
from service.dual_agent_service import (
    prepare_dual_interview_start,
    prepare_dual_interview_chat,
    stream_interview_reply,
    finalize_interview,
)
from service.tutor_service import (
    prepare_tutor_start,
    prepare_tutor_chat,
    stream_tutor_reply,
    finalize_tutor,
    end_tutor_session,
)

app = FastAPI(title="Interview Agent API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class ResetRequest(BaseModel):
    session_id: str


class TutorStartRequest(BaseModel):
    session_id: str
    question: str
    tech_stack: str
    difficulty: str = "medium"


class TutorChatRequest(BaseModel):
    tutor_session_id: str
    message: str


class TutorEndRequest(BaseModel):
    tutor_session_id: str


def _sse_event(event_type: str, data: dict | None = None) -> str:
    payload = data if data is not None else {}
    payload["type"] = event_type
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_interview_session(
    prepare_result: dict,
) -> Generator[str]:
    if prepare_result["action"] == "complete":
        result = prepare_result["result"]
        yield _sse_event("session", {
            "session_id": result.get("session_id", ""),
            "current_stage": result.get("current_stage", ""),
            "stage_name": result.get("stage_name", ""),
        })
        yield _sse_event("chunk", {"content": result.get("reply", "")})
        yield _sse_event("done")
        return

    if prepare_result["action"] == "await":
        yield _sse_event("session", {
            "session_id": prepare_result["session_id"],
            "current_stage": prepare_result.get("current_stage", ""),
            "stage_name": prepare_result.get("stage_name", ""),
        })
        yield _sse_event("await", {"message": prepare_result["message"]})
        yield _sse_event("done")
        return

    stream_params = prepare_result["stream_params"]
    session_id = prepare_result["session_id"]

    yield _sse_event("session", {
        "session_id": session_id,
        "current_stage": prepare_result.get("current_stage", ""),
        "stage_name": prepare_result.get("stage_name", ""),
    })

    full_reply = ""
    try:
        for chunk in stream_interview_reply(stream_params):
            full_reply += chunk
            yield _sse_event("chunk", {"content": chunk})
    except Exception as exc:
        if full_reply:
            yield _sse_event("chunk", {"content": full_reply})
        yield _sse_event("error", {"message": str(exc)})
        yield _sse_event("done")
        return

    finalize_interview(session_id, full_reply, stream_params)
    yield _sse_event("done")


def _stream_tutor_reply_generator(
    meta: dict,
    stream_params: dict,
) -> Generator[str]:
    yield _sse_event("session", {
        "tutor_session_id": meta["tutor_session_id"],
        "question": meta.get("question", ""),
    })

    full_reply = ""
    try:
        for chunk in stream_tutor_reply(stream_params):
            full_reply += chunk
            yield _sse_event("chunk", {"content": chunk})
    except Exception as exc:
        if full_reply:
            yield _sse_event("chunk", {"content": full_reply})
        yield _sse_event("error", {"message": str(exc)})
        yield _sse_event("done")
        return

    suggestions = finalize_tutor(meta["tutor_session_id"], full_reply)
    if suggestions:
        yield _sse_event("suggestions", {"items": suggestions})
    yield _sse_event("done")


@app.get("/")
def root():
    return {"message": "Interview Agent API is running"}


@app.get("/options")
def get_options_view():
    return get_options()


@app.get("/styles")
def list_styles_view():
    return list_styles()


@app.post("/interview")
def interview_session_view(req: SessionRequest):
    try:
        if req.session_id:
            prepare_result = prepare_dual_interview_chat(req.session_id, req.message)
        else:
            config = InterviewConfig(
                tech_stack=req.tech_stack or ["Python", "Django", "MySQL", "Redis"],
                position=req.position or "后端开发工程师",
                interview_style=req.style or "professional",
                difficulty=req.difficulty or "medium",
                mode=req.mode or "dual_agent",
                candidate_id=req.candidate_id,
                job_id=req.job_id,
                resume_info=req.resume_info,
            )
            meta, stream_params = prepare_dual_interview_start(config)
            prepare_result = {
                "action": "interview",
                "stream_params": stream_params,
                "session_id": meta["session_id"],
                "current_stage": meta["current_stage"],
                "stage_name": meta["stage_name"],
            }

        return StreamingResponse(
            _stream_interview_session(prepare_result),
            media_type="text/event-stream",
        )
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


@app.post("/tutor/start")
def tutor_start_view(req: TutorStartRequest):
    try:
        meta, stream_params = prepare_tutor_start(
            question=req.question,
            tech_stack=req.tech_stack,
            difficulty=req.difficulty,
            session_id=req.session_id,
        )
        return StreamingResponse(
            _stream_tutor_reply_generator(meta, stream_params),
            media_type="text/event-stream",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/tutor/chat")
def tutor_chat_view(req: TutorChatRequest):
    try:
        meta, stream_params = prepare_tutor_chat(
            tutor_session_id=req.tutor_session_id,
            message=req.message,
        )
        return StreamingResponse(
            _stream_tutor_reply_generator(meta, stream_params),
            media_type="text/event-stream",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/tutor/end")
def tutor_end_view(req: TutorEndRequest):
    try:
        end_tutor_session(req.tutor_session_id)
        return {"message": "Session ended"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
