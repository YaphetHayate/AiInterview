import time
from threading import Lock
from typing import Optional

from agents.modelFactory import interviewer_chat
from prompt.initialization import get_system_prompt
from service.config import InterviewConfig
from db.repository import ConversationRepository


DEFAULT_CONFIG = InterviewConfig(
    tech_stack=["Python", "Django", "MySQL", "Redis"],
    position="后端开发工程师",
    interview_style="professional"
)

_interviewer_agents = {}
_interviewer_agents_lock = Lock()


def _build_clean_system_prompt(config: InterviewConfig) -> str:
    return get_system_prompt(
        tech_stack=config.tech_stack,
        position=config.position,
        interview_style=config.interview_style,
        difficulty=config.difficulty,
        resume_info=config.resume_info,
    )


def get_or_create_interviewer(config: InterviewConfig):
    config_key = (
        tuple(config.tech_stack),
        config.position,
        config.interview_style,
        config.difficulty,
        config.resume_info,
        config.candidate_id,
        config.job_id,
        config.mode,
    )

    with _interviewer_agents_lock:
        if config_key not in _interviewer_agents:
            from langchain.agents import create_agent

            system_prompt = _build_clean_system_prompt(config)

            print("=" * 60)
            print("[DEBUG] 面试官LLM系统提示词（纯净）:")
            print("-" * 60)
            print(system_prompt)
            print("=" * 60)

            _interviewer_agents[config_key] = create_agent(
                model=interviewer_chat(),
                tools=[],
                system_prompt=system_prompt,
            )

        return _interviewer_agents[config_key]


def extract_text(result) -> str:
    messages = result.get("messages", [])
    if not messages:
        return "No response."
    last = messages[-1]
    content = getattr(last, "content", "")
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def invoke_interviewer(messages, agent=None, max_retries: int = 2):
    if agent is None:
        agent = get_or_create_interviewer(DEFAULT_CONFIG)

    print("=" * 60)
    print("[DEBUG] 面试官LLM收到的消息:")
    print("-" * 60)
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        print(f"[{i+1}] Role: {role}")
        print(f"    Content: {content[:500]}{'...' if len(content) > 500 else ''}")
        print()
    print("=" * 60)

    for attempt in range(max_retries + 1):
        try:
            result = agent.invoke({"messages": messages})
            return result if result is not None else {"messages": messages}
        except Exception as exc:
            is_ollama_502 = "status code: 502" in str(exc)
            if is_ollama_502 and attempt < max_retries:
                time.sleep(1)
                continue
            raise

    return {"messages": messages}


_sessions = {}
_sessions_config = {}
_sessions_lock = Lock()


def _get_session_messages(session_id: str):
    with _sessions_lock:
        if session_id in _sessions:
            return list(_sessions[session_id])
    db_msgs = ConversationRepository.get_messages(session_id)
    if db_msgs:
        with _sessions_lock:
            _sessions[session_id] = list(db_msgs)
        return db_msgs
    with _sessions_lock:
        return list(_sessions.get(session_id, []))


def _set_session_messages(session_id: str, messages):
    with _sessions_lock:
        _sessions[session_id] = list(messages)


def _get_session_config(session_id: str) -> InterviewConfig:
    with _sessions_lock:
        return _sessions_config.get(session_id, DEFAULT_CONFIG)


def _set_session_config(session_id: str, config: InterviewConfig):
    with _sessions_lock:
        _sessions_config[session_id] = config


def reset_session(session_id: str) -> None:
    with _sessions_lock:
        _sessions.pop(session_id, None)
        _sessions_config.pop(session_id, None)
    ConversationRepository.delete_by_session(session_id)


def chat_once(
    user_input: str,
    session_id: str = "default",
    config: Optional[InterviewConfig] = None
) -> str:
    if not user_input or not user_input.strip():
        raise ValueError("user_input cannot be empty")

    if config is not None:
        reset_session(session_id)
        _set_session_config(session_id, config)

    current_config = _get_session_config(session_id)
    agent = get_or_create_interviewer(current_config)

    conversation_messages = _get_session_messages(session_id)
    request_messages = conversation_messages + [
        {"role": "user", "content": user_input.strip()}
    ]

    result = invoke_interviewer(request_messages, agent=agent)
    if result is None:
        result = {"messages": request_messages}
    _set_session_messages(session_id, result.get("messages", request_messages))

    try:
        ConversationRepository.append(session_id, "user", user_input.strip())
        reply = extract_text(result)
        ConversationRepository.append(session_id, "assistant", reply)
    except Exception:
        reply = extract_text(result)

    return reply



