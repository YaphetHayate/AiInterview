from typing import Optional

from db.repository import TechStackRepository
from prompt.initialization import INTERVIEW_STYLES
from service.config import InterviewConfig
from service.interview import reset_session as _reset_session
from service.dual_agent_service import (
    start_dual_interview,
    dual_interview_chat as _dual_chat,
    reset_dual_session,
    get_session_info,
)
from service.question_manager import question_manager


def get_options() -> dict:
    try:
        stacks = TechStackRepository.get_all()
        tech_stack_names = [s["name"] for s in stacks]
    except Exception:
        tech_stack_names = []

    return {
        "tech_stacks": tech_stack_names,
        "positions": [
            "后端开发", "前端开发", "全栈开发",
            "算法工程师", "大数据开发", "测试开发",
        ],
        "modes": [
            {"name": "simulation", "display_name": "拟真模式"},
            {"name": "learning", "display_name": "学习模式"},
            {"name": "dual_agent", "display_name": "双Agent模式"},
        ],
    }


def list_styles() -> dict:
    return {
        "styles": {
            key: {
                "name": style.name,
                "tone": style.tone,
                "description": style.description,
            }
            for key, style in INTERVIEW_STYLES.items()
        }
    }


def interview_session(
    message: str,
    session_id: Optional[str] = None,
    tech_stack: Optional[list[str]] = None,
    position: Optional[str] = None,
    style: Optional[str] = None,
    difficulty: Optional[str] = None,
    mode: Optional[str] = None,
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
    resume_info: Optional[str] = None,
) -> dict:
    if session_id:
        return _continue_session(session_id, message)

    return _create_session(
        message=message,
        tech_stack=tech_stack or ["Python", "Django", "MySQL", "Redis"],
        position=position or "后端开发工程师",
        style=style or "professional",
        difficulty=difficulty or "medium",
        mode=mode or "dual_agent",
        candidate_id=candidate_id,
        job_id=job_id,
        resume_info=resume_info,
    )


def _create_session(
    message: str,
    tech_stack: list[str],
    position: str,
    style: str,
    difficulty: str,
    mode: str,
    candidate_id: Optional[str],
    job_id: Optional[str],
    resume_info: Optional[str],
) -> dict:
    config = InterviewConfig(
        tech_stack=tech_stack,
        position=position,
        interview_style=style,
        difficulty=difficulty,
        mode=mode,
        candidate_id=candidate_id,
        job_id=job_id,
        resume_info=resume_info,
    )

    result = start_dual_interview(config)
    return {
        "session_id": result["session_id"],
        "action": "interview",
        "reply": result["reply"],
        "current_stage": result.get("current_stage"),
        "stage_name": result.get("stage_name"),
    }


def _continue_session(session_id: str, message: str) -> dict:
    result = _dual_chat(session_id, message)
    return {
        "session_id": result["session_id"],
        "action": result.get("action", "interview"),
        "message_to_user": result.get("message_to_user"),
        "reply": result["reply"],
        "current_stage": result.get("current_stage"),
        "stage_name": result.get("stage_name"),
    }


def reset_session(session_id: str) -> dict:
    reset_dual_session(session_id)
    _reset_session(session_id)
    return {"message": "Session reset", "session_id": session_id}


def question_bank_tree() -> dict:
    from db.connection import db_cursor

    with db_cursor(dict_cursor=True) as (cur, conn):
        cur.execute(
            "SELECT id, tech_stack, difficulty, content FROM question_bank ORDER BY tech_stack, difficulty, id"
        )
        rows = cur.fetchall()

    tree: dict = {}
    for row in rows:
        tech = row["tech_stack"]
        diff = row["difficulty"]
        if tech not in tree:
            tree[tech] = {"name": tech, "children": {}}
        if diff not in tree[tech]["children"]:
            tree[tech]["children"][diff] = {
                "name": diff,
                "label": {"basic": "初级", "medium": "中级", "hard": "高级"}.get(diff, diff),
                "children": [],
            }
        tree[tech]["children"][diff]["children"].append(
            {"id": row["id"], "name": row["content"][:60], "fullContent": row["content"]}
        )

    result = []
    for tech_data in tree.values():
        tech_node = {"name": tech_data["name"], "children": []}
        for diff_data in tech_data["children"].values():
            tech_node["children"].append(diff_data)
        result.append(tech_node)

    return {"tree": result}


def get_progress(session_id: str) -> dict:
    dual_info = get_session_info(session_id)
    if dual_info:
        return {
            "session_id": session_id,
            "current_stage": dual_info["current_stage"],
            "stage_name": dual_info["stage_name"],
            "exchange_count": dual_info["exchange_count"],
            "mode": dual_info.get("mode", "simulation"),
        }
    return question_manager.get_progress(session_id)
