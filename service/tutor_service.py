import time
from threading import Lock
from uuid import uuid4

from agents.tutor_agent import TUTOR_SYSTEM_PROMPT, invoke_tutor, parse_suggestions, stream_tutor
from service.dual_agent_service import get_current_question, get_session_info

_tutor_sessions: dict[str, dict] = {}
_tutor_sessions_lock = Lock()

_SESSION_TTL_SECONDS = 30 * 60


def _cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [
        sid
        for sid, sess in _tutor_sessions.items()
        if now - sess["created_at"] > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _tutor_sessions.pop(sid, None)


def start_tutor_session(
    question: str,
    tech_stack: str,
    difficulty: str,
    session_id: str = "",
) -> dict:
    with _tutor_sessions_lock:
        _cleanup_expired_sessions()

    if not question and session_id:
        question = get_current_question(session_id) or ""

    if not tech_stack and session_id:
        info = get_session_info(session_id)
        if info:
            tech_stack = info.get("tech_stack", tech_stack)
            difficulty = info.get("mode", difficulty)

    tutor_session_id = str(uuid4())

    session = {
        "tutor_session_id": tutor_session_id,
        "question": question,
        "tech_stack": tech_stack,
        "difficulty": difficulty,
        "messages": [],
        "created_at": time.time(),
    }

    user_message = (
        f"我正在准备技术面试，遇到了以下面试问题：\n\n{question}\n\n"
        f"技术栈：{tech_stack}，难度：{difficulty}\n\n"
        f"请帮我深入讲解这道面试题涉及的知识点。"
    )

    reply = invoke_tutor(
        system_prompt=TUTOR_SYSTEM_PROMPT,
        user_message=user_message,
    )

    explanation, suggested_questions = parse_suggestions(reply)

    session["messages"].append({"role": "user", "content": user_message})
    session["messages"].append({"role": "assistant", "content": reply})

    with _tutor_sessions_lock:
        _tutor_sessions[tutor_session_id] = session

    return {
        "tutor_session_id": tutor_session_id,
        "explanation": explanation,
        "suggested_questions": suggested_questions,
        "question": question,
    }


def chat_tutor_session(tutor_session_id: str, message: str) -> dict:
    with _tutor_sessions_lock:
        session = _tutor_sessions.get(tutor_session_id)

    if not session:
        raise ValueError(f"Tutor 会话不存在: {tutor_session_id}")

    session["messages"].append({"role": "user", "content": message})

    history = [
        {"role": m["role"], "content": m["content"]} for m in session["messages"][:-1]
    ]

    reply = invoke_tutor(
        system_prompt=TUTOR_SYSTEM_PROMPT,
        user_message=message,
        conversation_history=history,
    )

    explanation, suggested_questions = parse_suggestions(reply)

    session["messages"].append({"role": "assistant", "content": reply})

    return {
        "tutor_session_id": tutor_session_id,
        "explanation": explanation,
        "suggested_questions": suggested_questions,
    }


def end_tutor_session(tutor_session_id: str) -> None:
    with _tutor_sessions_lock:
        _tutor_sessions.pop(tutor_session_id, None)


# ── Streaming prepare / stream / finalize ──────────────────────────


def prepare_tutor_start(
    question: str,
    tech_stack: str,
    difficulty: str,
    session_id: str = "",
) -> tuple[dict, dict]:
    with _tutor_sessions_lock:
        _cleanup_expired_sessions()

    if not question and session_id:
        question = get_current_question(session_id) or ""

    if not tech_stack and session_id:
        info = get_session_info(session_id)
        if info:
            tech_stack = info.get("tech_stack", tech_stack)
            difficulty = info.get("mode", difficulty)

    tutor_session_id = str(uuid4())

    session = {
        "tutor_session_id": tutor_session_id,
        "question": question,
        "tech_stack": tech_stack,
        "difficulty": difficulty,
        "messages": [],
        "created_at": time.time(),
    }

    user_message = (
        f"我正在准备技术面试，遇到了以下面试问题：\n\n{question}\n\n"
        f"技术栈：{tech_stack}，难度：{difficulty}\n\n"
        f"请帮我深入讲解这道面试题涉及的知识点。"
    )

    session["messages"].append({"role": "user", "content": user_message})

    with _tutor_sessions_lock:
        _tutor_sessions[tutor_session_id] = session

    meta = {
        "tutor_session_id": tutor_session_id,
        "question": question,
    }
    stream_params = {
        "system_prompt": TUTOR_SYSTEM_PROMPT,
        "user_message": user_message,
        "conversation_history": None,
        "tutor_session_id": tutor_session_id,
        "context": "start",
    }
    return meta, stream_params


def prepare_tutor_chat(tutor_session_id: str, message: str) -> tuple[dict, dict]:
    with _tutor_sessions_lock:
        session = _tutor_sessions.get(tutor_session_id)

    if not session:
        raise ValueError(f"Tutor 会话不存在: {tutor_session_id}")

    session["messages"].append({"role": "user", "content": message})

    history = [
        {"role": m["role"], "content": m["content"]} for m in session["messages"][:-1]
    ]

    meta = {"tutor_session_id": tutor_session_id}
    stream_params = {
        "system_prompt": TUTOR_SYSTEM_PROMPT,
        "user_message": message,
        "conversation_history": history,
        "tutor_session_id": tutor_session_id,
        "context": "chat",
    }
    return meta, stream_params


def stream_tutor_reply(stream_params: dict):
    yield from stream_tutor(
        system_prompt=stream_params["system_prompt"],
        user_message=stream_params["user_message"],
        conversation_history=stream_params.get("conversation_history"),
    )


def finalize_tutor(tutor_session_id: str, full_reply: str) -> list[str]:
    with _tutor_sessions_lock:
        session = _tutor_sessions.get(tutor_session_id)
    if not session:
        return []
    session["messages"].append({"role": "assistant", "content": full_reply})
    _, suggestions = parse_suggestions(full_reply)
    return suggestions
