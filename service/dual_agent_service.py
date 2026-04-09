import logging
from pathlib import Path
from threading import Lock
from typing import Optional
from uuid import uuid4

from agents.interviewer_agent import invoke_interviewer, stream_interviewer
from agents.manager_agent import MANAGER_SYSTEM_PROMPT, create_manager_agent, invoke_manager_with
from db.repository import QuestionBankRepository
from prompt.initialization import get_system_prompt
from service.config import InterviewConfig

_sessions: dict[str, dict] = {}
_sessions_lock = Lock()

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

CONFIRMATION_KEYWORDS = {"完毕", "回复完毕", "回答完毕", "结束回答", "发完了"}
STAGE_ADVANCE_KEYWORDS = {"下一阶段", "下一题", "继续下一阶段", "进   入下一阶段"}
END_INTERVIEW_KEYWORDS = {"结束面试", "结束", "结束面谈", "end"}

STAGE_NAMES = {
    1: "基础知识考察",
    2: "项目经历考察",
    3: "岗位需求考察",
    4: "面试总结",
}

MODE_CONFIG = {
    "simulation": {
        "max_follow_ups": 3,
        "context_mode": "question_isolated",
        "mode_hint": "",
    },
    "learning": {
        "max_follow_ups": 5,
        "context_mode": "full_history",
        "mode_hint": "可以适当引导候选人，提供参考答案和解析。",
    },
}

INJECT_CONFIG_IN_MESSAGE = False


def _get_prompt_logger(session_id: str) -> logging.Logger:
    logger_name = f"prompt_debug.{session_id}"
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _LOG_DIR / f"prompt_{session_id}.log"
    handler = logging.FileHandler(str(log_path), encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _log_section(
    logger: logging.Logger, tag: str, meta: str = "", content: str = ""
) -> None:
    header = tag if not meta else f"{tag} ({meta})"
    sep = "\u2550" * 64
    logger.info(
        "\n\u2554%s\n\u2551 %s\n\u255a%s\n%s",
        sep,
        header,
        sep,
        content,
    )


def _build_session_config(config: InterviewConfig) -> dict:
    return {
        "tech_stack": ", ".join(config.tech_stack),
        "difficulty": config.difficulty,
        "interview_style": config.interview_style,
        "position": config.position,
        "mode": config.mode,
        "resume_info": config.resume_info,
    }


def _create_session(config: InterviewConfig, session_id: str) -> dict:
    session_config = _build_session_config(config)
    manager_agent = create_manager_agent(session_config)
    return {
        "session_id": session_id,
        "mode": config.mode,
        "stage": 1,
        "stage_name": STAGE_NAMES[1],
        "position": config.position,
        "tech_stack": ", ".join(config.tech_stack),
        "interview_style": config.interview_style,
        "difficulty": config.difficulty,
        "resume_info": config.resume_info,
        "config": session_config,
        "manager_agent": manager_agent,
        "questions": [],
        "current_question_idx": -1,
        "pending_buffer": [],
        "stage_summaries": [],
        "manager_history": [],
        "interviewer_history": [],
        "exchange_count": 0,
    }


def _fetch_questions(session: dict, limit: int = 5) -> list[dict]:
    tech_list = [t.strip() for t in session["tech_stack"].split(",")]
    difficulty = session["difficulty"]
    try:
        rows = QuestionBankRepository.get_random_questions(tech_list, difficulty, limit)
        return [{"id": r["id"], "content": r["content"]} for r in rows]
    except Exception:
        return []


def _build_manager_start_message(session: dict) -> str:
    parts = [
        "面试即将开始。",
        "请先调用 read_session_config 获取当前面试配置。",
        "然后调用 read_skill_md 读取面试流程技能文件，理解完整流程。",
        "接着调用 read_stage_file(1) 读取阶段1的指引。",
        "最后组装提示词给面试官，开始阶段1的面试。",
        "\n候选人说：开始面试",
    ]
    if INJECT_CONFIG_IN_MESSAGE:
        parts.insert(
            1,
            f"\n面试配置信息：\n"
            f"- 岗位：{session['position']}\n"
            f"- 技术栈：{session['tech_stack']}\n"
            f"- 面试风格：{session['interview_style']}\n"
            f"- 难度：{session['difficulty']}\n"
            f"- 面试模式：{session['mode']}\n",
        )
    return "\n".join(parts)


def _build_manager_chat_message(
    session: dict,
    full_answer: str,
    question_info: Optional[dict] = None,
) -> str:
    mode_cfg = MODE_CONFIG.get(session["mode"], MODE_CONFIG["simulation"])
    current_q = None
    if session["current_question_idx"] >= 0:
        idx = session["current_question_idx"]
        if idx < len(session["questions"]):
            current_q = session["questions"][idx]

    parts = [
        "当前面试状态：",
        f"- 当前阶段：{session['stage']}（{session['stage_name']}）",
        f"- 当前阶段已交互次数：{session['exchange_count']}",
        f"- 最大追问次数：{mode_cfg['max_follow_ups']}",
        f"- mode_hint：{mode_cfg['mode_hint'] or '（无）'}",
    ]

    if INJECT_CONFIG_IN_MESSAGE:
        parts.extend([
            f"- 面试模式：{session['mode']}",
            f"- 面试风格：{session['interview_style']}",
            f"- 难度：{session['difficulty']}",
        ])
    else:
        parts.append("（如需面试配置信息，请调用 read_session_config）")

    if current_q:
        parts.append(f"\n当前问题：{current_q['content']}")
        parts.append(f"当前问题追问次数：{current_q.get('follow_up_count', 0)}")
        parts.append(f"问题状态：{current_q.get('status', 'active')}")

    parts.append(f"\n候选人回答：{full_answer}")
    parts.append("\n请判断候选人回答是否完整，并生成对应输出。")

    return "\n".join(parts)


def _build_manager_stage_advance_message(session: dict, next_stage: int) -> str:
    stage_name = STAGE_NAMES.get(next_stage, "未知阶段")
    parts = [
        f"阶段 {session['stage']}（{session['stage_name']}）已完成。",
        f"请调用 read_stage_file({next_stage}) 读取阶段 {next_stage}（{stage_name}）的指引文件。",
        f"然后组装提示词给面试官，开始阶段 {next_stage} 的面试。",
    ]

    if INJECT_CONFIG_IN_MESSAGE:
        parts.append(
            f"\n面试配置：岗位 {session['position']}，技术栈 {session['tech_stack']}"
            f"，模式：{session['mode']}，风格：{session['interview_style']}"
        )
    else:
        parts.append("（如需面试配置信息，请调用 read_session_config）")

    if session["stage_summaries"]:
        parts.append("\n之前阶段摘要：")
        for i, s in enumerate(session["stage_summaries"]):
            parts.append(f"阶段{i + 1}: {s}")

    return "\n".join(parts)


def _build_manager_summary_message(session: dict) -> str:
    parts = [
        "面试已进入总结阶段（阶段4）。",
        "请调用 read_stage_file(4) 读取总结阶段的指引文件。",
        "然后基于以下信息生成综合评价报告。",
    ]

    if INJECT_CONFIG_IN_MESSAGE:
        parts.append(
            f"\n面试配置：岗位 {session['position']}，技术栈 {session['tech_stack']}"
            f"，模式：{session['mode']}"
        )
    else:
        parts.append("（如需面试配置信息，请调用 read_session_config）")

    parts.append("\n各阶段摘要：")
    for i, s in enumerate(session["stage_summaries"]):
        parts.append(f"阶段{i + 1}（{STAGE_NAMES.get(i + 1, '')}）: {s}")

    parts.append("\n问题回答记录：")
    for q in session["questions"]:
        parts.append(f"- 问题: {q['content']}")
        parts.append(f"  状态: {q.get('status', 'unknown')}")
        if q.get("summary"):
            parts.append(f"  摘要: {q['summary']}")

    return "\n".join(parts)


def _build_manager_question_summary_message(
    session: dict, question: dict
) -> str:
    parts = [
        f"当前问题已完成：{question['content']}",
        f"追问次数：{question.get('follow_up_count', 0)}",
        "对话记录：",
    ]
    for msg in question.get("thread", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        parts.append(f"  [{role}] {content[:200]}")

    parts.append("\n请用一句话概括候选人在这道题上的表现，作为问题摘要。")
    parts.append("只输出摘要文本，不要输出 JSON。")

    return "\n".join(parts)


_AWAIT_PREFIX = "[AWAIT]"


def _is_await_continuation(response: str) -> bool:
    return response.strip().startswith(_AWAIT_PREFIX)


def _extract_await_message(response: str) -> str:
    message = response.strip()[len(_AWAIT_PREFIX):].strip()
    return message or "请继续补充您的回答。"


def _get_context_thread(session: dict) -> list[dict]:
    mode_cfg = MODE_CONFIG.get(session["mode"], MODE_CONFIG["simulation"])
    if mode_cfg["context_mode"] == "full_history":
        return list(session["interviewer_history"])

    if session["current_question_idx"] >= 0:
        idx = session["current_question_idx"]
        if idx < len(session["questions"]):
            return list(session["questions"][idx].get("thread", []))

    return []


def _detect_user_intent(user_input: str) -> Optional[str]:
    text = user_input.strip().lower()
    if text in END_INTERVIEW_KEYWORDS:
        return "end_interview"
    if text in STAGE_ADVANCE_KEYWORDS:
        return "advance_stage"
    if text in CONFIRMATION_KEYWORDS:
        return "force_complete"
    return None


def _get_or_advance_question(session: dict) -> Optional[dict]:
    idx = session["current_question_idx"]
    if idx >= 0 and idx < len(session["questions"]):
        q = session["questions"][idx]
        if q.get("status") == "active":
            return q

    if session["questions"]:
        fetched = _fetch_questions(session, limit=1)
    else:
        fetched = _fetch_questions(session, limit=5)
        if fetched:
            for fq in fetched:
                session["questions"].append(
                    {
                        "id": fq["id"],
                        "content": fq["content"],
                        "status": "active",
                        "thread": [],
                        "summary": None,
                        "follow_up_count": 0,
                    }
                )
            session["current_question_idx"] = 0
            return session["questions"][0]
        return None

    if fetched:
        session["questions"].append(
            {
                "id": fetched[0]["id"],
                "content": fetched[0]["content"],
                "status": "active",
                "thread": [],
                "summary": None,
                "follow_up_count": 0,
            }
        )
        session["current_question_idx"] = len(session["questions"]) - 1
        return session["questions"][-1]

    return None


def _complete_current_question(session: dict) -> None:
    idx = session["current_question_idx"]
    if idx < 0 or idx >= len(session["questions"]):
        return
    session["questions"][idx]["status"] = "completed"


def _advance_to_next_question(session: dict) -> bool:
    _complete_current_question(session)
    idx = session["current_question_idx"]
    for i in range(idx + 1, len(session["questions"])):
        if session["questions"][i].get("status") != "completed":
            session["current_question_idx"] = i
            session["exchange_count"] = 0
            return True
    return False


def _invoke_session_manager(session: dict, messages: list[dict]) -> str:
    return invoke_manager_with(session["manager_agent"], messages)


def _advance_stage(session: dict, logger: logging.Logger) -> bool:
    current = session["stage"]
    if current >= 4:
        return False

    _complete_current_question(session)

    if session["questions"]:
        last_q = session["questions"][session["current_question_idx"]]
        msg = _build_manager_question_summary_message(session, last_q)
        session["manager_history"].append({"role": "user", "content": msg})
        summary = _invoke_session_manager(session, session["manager_history"])
        session["manager_history"].append(
            {"role": "assistant", "content": summary}
        )
        last_q["summary"] = summary

    for q in session["questions"]:
        if q.get("summary") is None:
            q["summary"] = f"问题: {q['content'][:50]}..."

    stage_summary_parts = []
    for q in session["questions"]:
        stage_summary_parts.append(f"- {q.get('summary', '无摘要')}")
    session["stage_summaries"].append("\n".join(stage_summary_parts))

    next_stage = current + 1
    session["stage"] = next_stage
    session["stage_name"] = STAGE_NAMES.get(next_stage, "面试总结")
    session["questions"] = []
    session["current_question_idx"] = -1
    session["exchange_count"] = 0

    _log_section(
        logger, "[FLOW] Stage Advance",
        content=f"from_stage={current}, to_stage={next_stage}",
    )
    return True


def _get_fallback_system_prompt(session: dict) -> str:
    return get_system_prompt(
        tech_stack=[t.strip() for t in session["tech_stack"].split(",")],
        position=session["position"],
        interview_style=session["interview_style"],
        difficulty=session["difficulty"],
        resume_info=session.get("resume_info"),
    )


def start_dual_interview(config: InterviewConfig) -> dict:
    session_id = str(uuid4())
    logger = _get_prompt_logger(session_id)

    session = _create_session(config, session_id)

    _log_section(logger, "[MANAGER] System Prompt", content=MANAGER_SYSTEM_PROMPT)

    manager_message = _build_manager_start_message(session)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=start", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    first_questions = _fetch_questions(session, limit=5)
    if first_questions:
        for q in first_questions:
            session["questions"].append(
                {
                    "id": q["id"],
                    "content": q["content"],
                    "status": "active",
                    "thread": [],
                    "summary": None,
                    "follow_up_count": 0,
                }
            )
        session["current_question_idx"] = 0

    system_prompt = _get_fallback_system_prompt(session)

    current_q = (
        session["questions"][0]
        if session["questions"]
        else None
    )
    if current_q:
        user_message = f"请向候选人提出第一个问题：{current_q['content']}"
    else:
        user_message = "请开始面试，向候选人提出第一个问题。"

    session["interviewer_history"].append({"role": "user", "content": user_message})

    _log_section(logger, "[INTERVIEWER] System Prompt", content=system_prompt)
    _log_section(logger, "[INTERVIEWER] User Message", content=user_message)
    interview_reply = invoke_interviewer(
        system_prompt=system_prompt,
        user_message=user_message,
    )
    _log_section(logger, "[INTERVIEWER] Response", content=interview_reply)

    if session["questions"]:
        session["questions"][0]["thread"].append(
            {"role": "assistant", "content": interview_reply}
        )

    session["interviewer_history"].append({"role": "assistant", "content": interview_reply})
    session["exchange_count"] = 1

    with _sessions_lock:
        _sessions[session_id] = session

    return {
        "session_id": session_id,
        "reply": interview_reply,
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
    }


def dual_interview_chat(session_id: str, user_input: str) -> dict:
    with _sessions_lock:
        session = _sessions.get(session_id)

    if not session:
        raise ValueError(f"会话不存在: {session_id}")

    logger = _get_prompt_logger(session_id)
    user_input_stripped = user_input.strip()

    user_intent = _detect_user_intent(user_input_stripped)

    if user_intent == "end_interview":
        return _handle_final_summary(session, logger)

    if user_intent == "advance_stage":
        return _handle_stage_advance(session, logger)

    if user_intent == "force_complete":
        session["pending_buffer"].append(user_input_stripped)
        full_answer = "\n".join(session["pending_buffer"])
        session["pending_buffer"] = []
        _log_section(logger, "[FLOW] Force Complete", content=full_answer)
        return _process_complete_answer(session, full_answer, logger)

    session["pending_buffer"].append(user_input_stripped)

    pending_text = "\n".join(session["pending_buffer"])
    _log_section(
        logger, "[FLOW] Pending Buffer",
        content=f"count={len(session['pending_buffer'])}\n{pending_text}",
    )

    manager_msg = (
        f"候选人发送了消息（可能是完整回答或部分回答）：\n{pending_text}\n\n"
        f"请判断这是否是完整回答。"
    )
    session["manager_history"].append({"role": "user", "content": manager_msg})
    _log_section(logger, "[MANAGER] Input", meta="source=completeness_check", content=manager_msg)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    if _is_await_continuation(manager_response):
        await_message = _extract_await_message(manager_response)
        _log_section(
            logger, "[FLOW] Await Continuation",
            content=await_message,
        )
        return {
            "session_id": session_id,
            "action": "await_continuation",
            "message_to_user": await_message,
            "reply": await_message,
            "current_stage": str(session["stage"]),
            "stage_name": session["stage_name"],
        }

    full_answer = "\n".join(session["pending_buffer"])
    session["pending_buffer"] = []
    return _process_complete_answer(session, full_answer, logger)


def _process_complete_answer(
    session: dict, full_answer: str, logger: logging.Logger
) -> dict:
    current_q = _get_or_advance_question(session)
    mode_cfg = MODE_CONFIG.get(session["mode"], MODE_CONFIG["simulation"])

    if current_q:
        current_q["thread"].append({"role": "user", "content": full_answer})
        current_q["follow_up_count"] = current_q.get("follow_up_count", 0) + 1

    manager_message = _build_manager_chat_message(session, full_answer, current_q)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=chat", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    system_prompt = _get_fallback_system_prompt(session)

    mode_hint = mode_cfg.get("mode_hint", "")
    user_message = f"候选人回答：{full_answer}\n\n请给出反馈并继续提问。"
    if manager_response.strip():
        user_message = f"{user_message}\n\n面试指导：{manager_response.strip()}"
    if mode_hint:
        user_message = f"{user_message}\n\n模式提示：{mode_hint}"

    context_thread = _get_context_thread(session)

    _log_section(logger, "[INTERVIEWER] System Prompt", content=system_prompt)
    _log_section(logger, "[INTERVIEWER] User Message", content=user_message)
    interview_reply = invoke_interviewer(
        system_prompt=system_prompt,
        user_message=user_message,
        conversation_history=context_thread if context_thread else None,
    )
    _log_section(logger, "[INTERVIEWER] Response", content=interview_reply)

    if current_q:
        current_q["thread"].append({"role": "assistant", "content": interview_reply})

    session["interviewer_history"].append({"role": "user", "content": user_message})
    session["interviewer_history"].append({"role": "assistant", "content": interview_reply})
    session["exchange_count"] = session.get("exchange_count", 0) + 1

    if current_q:
        max_fu = mode_cfg["max_follow_ups"]
        if current_q.get("follow_up_count", 0) >= max_fu:
            current_q["status"] = "max_reached"

    return {
        "session_id": session["session_id"],
        "action": "interview",
        "reply": interview_reply,
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
    }


def _handle_stage_advance(session: dict, logger: logging.Logger) -> dict:
    current = session["stage"]
    if current >= 4:
        return _handle_final_summary(session, logger)

    if not _advance_stage(session, logger):
        return _handle_final_summary(session, logger)

    next_stage = session["stage"]
    manager_message = _build_manager_stage_advance_message(session, next_stage)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=stage_advance", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    if next_stage <= 3:
        new_questions = _fetch_questions(session, limit=5)
        if new_questions:
            for q in new_questions:
                session["questions"].append(
                    {
                        "id": q["id"],
                        "content": q["content"],
                        "status": "active",
                        "thread": [],
                        "summary": None,
                        "follow_up_count": 0,
                    }
                )
            session["current_question_idx"] = 0

    system_prompt = _get_fallback_system_prompt(session)

    if session["questions"]:
        first_q = session["questions"][0]
        user_message = f"进入新阶段。请向候选人提出第一个问题：{first_q['content']}"
    else:
        user_message = f"进入阶段 {next_stage}，请开始提问。"

    session["interviewer_history"] = [{"role": "user", "content": user_message}]

    _log_section(logger, "[INTERVIEWER] System Prompt", content=system_prompt)
    _log_section(logger, "[INTERVIEWER] User Message", content=user_message)
    interview_reply = invoke_interviewer(
        system_prompt=system_prompt,
        user_message=user_message,
    )
    _log_section(logger, "[INTERVIEWER] Response", content=interview_reply)

    if session["questions"]:
        session["questions"][0]["thread"].append({"role": "assistant", "content": interview_reply})

    session["interviewer_history"].append({"role": "assistant", "content": interview_reply})
    session["exchange_count"] = 1

    return {
        "session_id": session["session_id"],
        "action": "interview",
        "reply": interview_reply,
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
    }


def _handle_final_summary(session: dict, logger: logging.Logger) -> dict:
    if session["stage"] != 4:
        if session["questions"]:
            _complete_current_question(session)
            last_q = session["questions"][session["current_question_idx"]]
            if last_q.get("summary") is None:
                msg = _build_manager_question_summary_message(session, last_q)
                session["manager_history"].append({"role": "user", "content": msg})
                summary = _invoke_session_manager(session, session["manager_history"])
                session["manager_history"].append({"role": "assistant", "content": summary})
                last_q["summary"] = summary

        stage_summary_parts = []
        for q in session["questions"]:
            if q.get("summary") is None:
                q["summary"] = f"问题: {q['content'][:50]}..."
            stage_summary_parts.append(f"- {q.get('summary', '无摘要')}")
        session["stage_summaries"].append("\n".join(stage_summary_parts))

        session["stage"] = 4
        session["stage_name"] = "面试总结"

    manager_message = _build_manager_summary_message(session)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=final_summary", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)

    return {
        "session_id": session["session_id"],
        "action": "interview",
        "reply": manager_response,
        "current_stage": "4",
        "stage_name": "面试总结",
    }


def get_session_info(session_id: str) -> Optional[dict]:
    with _sessions_lock:
        session = _sessions.get(session_id)
    if not session:
        return None
    return {
        "session_id": session["session_id"],
        "tech_stack": session["tech_stack"],
        "position": session["position"],
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
        "exchange_count": session.get("exchange_count", 0),
        "mode": session.get("mode", "simulation"),
    }


def get_current_question(session_id: str) -> Optional[str]:
    with _sessions_lock:
        session = _sessions.get(session_id)
    if not session:
        return None
    idx = session.get("current_question_idx", -1)
    questions = session.get("questions", [])
    if 0 <= idx < len(questions):
        return questions[idx].get("content", "")
    return None


def reset_dual_session(session_id: str) -> None:
    with _sessions_lock:
        _sessions.pop(session_id, None)
    logger_name = f"prompt_debug.{session_id}"
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


# ── Streaming prepare / stream / finalize ──────────────────────────


def prepare_dual_interview_start(config: InterviewConfig) -> tuple[dict, dict]:
    session_id = str(uuid4())
    logger = _get_prompt_logger(session_id)

    session = _create_session(config, session_id)

    _log_section(logger, "[MANAGER] System Prompt", content=MANAGER_SYSTEM_PROMPT)

    manager_message = _build_manager_start_message(session)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=start", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    first_questions = _fetch_questions(session, limit=5)
    if first_questions:
        for q in first_questions:
            session["questions"].append(
                {
                    "id": q["id"],
                    "content": q["content"],
                    "status": "active",
                    "thread": [],
                    "summary": None,
                    "follow_up_count": 0,
                }
            )
        session["current_question_idx"] = 0

    system_prompt = _get_fallback_system_prompt(session)

    current_q = (
        session["questions"][0]
        if session["questions"]
        else None
    )
    if current_q:
        user_message = f"请向候选人提出第一个问题：{current_q['content']}"
    else:
        user_message = "请开始面试，向候选人提出第一个问题。"

    session["interviewer_history"].append({"role": "user", "content": user_message})

    _log_section(logger, "[INTERVIEWER] System Prompt", content=system_prompt)
    _log_section(logger, "[INTERVIEWER] User Message", content=user_message)

    with _sessions_lock:
        _sessions[session_id] = session

    meta = {
        "session_id": session_id,
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
    }
    stream_params = {
        "system_prompt": system_prompt,
        "user_message": user_message,
        "conversation_history": None,
        "context": "start",
    }
    return meta, stream_params


def prepare_dual_interview_chat(session_id: str, user_input: str) -> dict:
    with _sessions_lock:
        session = _sessions.get(session_id)

    if not session:
        raise ValueError(f"会话不存在: {session_id}")

    logger = _get_prompt_logger(session_id)
    user_input_stripped = user_input.strip()

    user_intent = _detect_user_intent(user_input_stripped)

    if user_intent == "end_interview":
        return {"action": "complete", "result": _handle_final_summary(session, logger)}

    if user_intent == "advance_stage":
        return _prepare_stage_advance_stream(session, logger)

    if user_intent == "force_complete":
        session["pending_buffer"].append(user_input_stripped)
        full_answer = "\n".join(session["pending_buffer"])
        session["pending_buffer"] = []
        _log_section(logger, "[FLOW] Force Complete", content=full_answer)
        return _prepare_complete_answer_stream(session, full_answer, logger)

    session["pending_buffer"].append(user_input_stripped)

    pending_text = "\n".join(session["pending_buffer"])
    _log_section(
        logger, "[FLOW] Pending Buffer",
        content=f"count={len(session['pending_buffer'])}\n{pending_text}",
    )

    manager_msg = (
        f"候选人发送了消息（可能是完整回答或部分回答）：\n{pending_text}\n\n"
        f"请判断这是否是完整回答。"
    )
    session["manager_history"].append({"role": "user", "content": manager_msg})
    _log_section(logger, "[MANAGER] Input", meta="source=completeness_check", content=manager_msg)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    if _is_await_continuation(manager_response):
        await_message = _extract_await_message(manager_response)
        _log_section(
            logger, "[FLOW] Await Continuation",
            content=await_message,
        )
        return {
            "action": "await",
            "message": await_message,
            "session_id": session_id,
            "current_stage": str(session["stage"]),
            "stage_name": session["stage_name"],
        }

    full_answer = "\n".join(session["pending_buffer"])
    session["pending_buffer"] = []
    return _prepare_complete_answer_stream(session, full_answer, logger)


def _prepare_complete_answer_stream(
    session: dict, full_answer: str, logger: logging.Logger
) -> dict:
    current_q = _get_or_advance_question(session)
    mode_cfg = MODE_CONFIG.get(session["mode"], MODE_CONFIG["simulation"])

    if current_q:
        current_q["thread"].append({"role": "user", "content": full_answer})
        current_q["follow_up_count"] = current_q.get("follow_up_count", 0) + 1

    manager_message = _build_manager_chat_message(session, full_answer, current_q)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=chat", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    system_prompt = _get_fallback_system_prompt(session)

    mode_hint = mode_cfg.get("mode_hint", "")
    user_message = f"候选人回答：{full_answer}\n\n请给出反馈并继续提问。"
    if manager_response.strip():
        user_message = f"{user_message}\n\n面试指导：{manager_response.strip()}"
    if mode_hint:
        user_message = f"{user_message}\n\n模式提示：{mode_hint}"

    context_thread = _get_context_thread(session)

    _log_section(logger, "[INTERVIEWER] System Prompt", content=system_prompt)
    _log_section(logger, "[INTERVIEWER] User Message", content=user_message)

    stream_params = {
        "system_prompt": system_prompt,
        "user_message": user_message,
        "conversation_history": context_thread if context_thread else None,
        "context": "chat",
        "current_q_index": session["current_question_idx"],
    }
    return {
        "action": "interview",
        "stream_params": stream_params,
        "session_id": session["session_id"],
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
    }


def _prepare_stage_advance_stream(session: dict, logger: logging.Logger) -> dict:
    current = session["stage"]
    if current >= 4:
        return {"action": "complete", "result": _handle_final_summary(session, logger)}

    if not _advance_stage(session, logger):
        return {"action": "complete", "result": _handle_final_summary(session, logger)}

    next_stage = session["stage"]
    manager_message = _build_manager_stage_advance_message(session, next_stage)
    session["manager_history"].append({"role": "user", "content": manager_message})

    _log_section(logger, "[MANAGER] Input", meta="source=stage_advance", content=manager_message)
    manager_response = _invoke_session_manager(session, session["manager_history"])
    _log_section(logger, "[MANAGER] Output", content=manager_response)
    session["manager_history"].append({"role": "assistant", "content": manager_response})

    if next_stage <= 3:
        new_questions = _fetch_questions(session, limit=5)
        if new_questions:
            for q in new_questions:
                session["questions"].append(
                    {
                        "id": q["id"],
                        "content": q["content"],
                        "status": "active",
                        "thread": [],
                        "summary": None,
                        "follow_up_count": 0,
                    }
                )
            session["current_question_idx"] = 0

    system_prompt = _get_fallback_system_prompt(session)

    if session["questions"]:
        first_q = session["questions"][0]
        user_message = f"进入新阶段。请向候选人提出第一个问题：{first_q['content']}"
    else:
        user_message = f"进入阶段 {next_stage}，请开始提问。"

    session["interviewer_history"] = [{"role": "user", "content": user_message}]

    _log_section(logger, "[INTERVIEWER] System Prompt", content=system_prompt)
    _log_section(logger, "[INTERVIEWER] User Message", content=user_message)

    stream_params = {
        "system_prompt": system_prompt,
        "user_message": user_message,
        "conversation_history": None,
        "context": "stage_advance",
    }
    return {
        "action": "interview",
        "stream_params": stream_params,
        "session_id": session["session_id"],
        "current_stage": str(session["stage"]),
        "stage_name": session["stage_name"],
    }


def stream_interview_reply(stream_params: dict):
    yield from stream_interviewer(
        system_prompt=stream_params["system_prompt"],
        user_message=stream_params["user_message"],
        conversation_history=stream_params.get("conversation_history"),
    )


def finalize_interview(session_id: str, full_reply: str, stream_params: dict) -> None:
    with _sessions_lock:
        session = _sessions.get(session_id)
    if not session:
        return

    logger = _get_prompt_logger(session_id)
    _log_section(logger, "[INTERVIEWER] Response", content=full_reply)

    context = stream_params.get("context", "chat")

    if context == "start":
        if session["questions"]:
            session["questions"][0]["thread"].append(
                {"role": "assistant", "content": full_reply}
            )
        session["interviewer_history"].append({"role": "assistant", "content": full_reply})
        session["exchange_count"] = 1

    elif context == "chat":
        current_q_index = stream_params.get("current_q_index", -1)
        if 0 <= current_q_index < len(session["questions"]):
            current_q = session["questions"][current_q_index]
            current_q["thread"].append({"role": "assistant", "content": full_reply})
            mode_cfg = MODE_CONFIG.get(session["mode"], MODE_CONFIG["simulation"])
            max_fu = mode_cfg["max_follow_ups"]
            if current_q.get("follow_up_count", 0) >= max_fu:
                current_q["status"] = "max_reached"

        session["interviewer_history"].append({"role": "user", "content": stream_params["user_message"]})
        session["interviewer_history"].append({"role": "assistant", "content": full_reply})
        session["exchange_count"] = session.get("exchange_count", 0) + 1

    elif context == "stage_advance":
        if session["questions"]:
            session["questions"][0]["thread"].append({"role": "assistant", "content": full_reply})
        session["interviewer_history"].append({"role": "assistant", "content": full_reply})
        session["exchange_count"] = 1
