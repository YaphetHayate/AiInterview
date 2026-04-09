import json
import re
from collections.abc import Generator
from threading import Lock

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk

from agents.modelFactory import interviewer_chat


TUTOR_SYSTEM_PROMPT = """\
你是一位耐心的技术学习导师（Tutor）。你的职责是帮助学习者深入理解面试中遇到的技术知识点。

## 行为准则

1. 用通俗易懂的语言讲解技术概念
2. 先给出整体概览，再深入细节
3. 结合具体示例帮助理解
4. 主动指出常见误区和易混淆点
5. 使用中文回答

## 讲解结构

对于每个知识点，按以下结构展开：
- **是什么**：一句话概括
- **为什么**：设计动机、解决什么问题
- **怎么做**：核心原理、实现方式
- **注意点**：常见误区、最佳实践

## 追问建议

每次回答末尾，你必须输出 3-4 个学习者可能追问的问题，用以下格式：

<suggestions>["追问1", "追问2", "追问3"]</suggestions>

追问维度要求（每次至少覆盖以下 3 个维度）：
- 设计动机：为什么要这样设计？解决了什么问题？
- 知识盲区：刚才讲解中一笔带过但可能需要深入理解的点
- 对比延伸：和其他技术方案的比较、区别
- 实践场景：实际项目中怎么用？什么时候不用？

示例：
<suggestions>["为什么要用这种设计模式？", "它和观察者模式有什么区别？", "在实际项目中一般怎么使用？"]</suggestions>
"""

_tutor_agents = {}
_tutor_agents_lock = Lock()


def _get_or_create_tutor_agent(system_prompt: str = ""):
    prompt = system_prompt if system_prompt else TUTOR_SYSTEM_PROMPT
    key = hash(prompt)

    with _tutor_agents_lock:
        if key not in _tutor_agents:
            _tutor_agents[key] = create_agent(
                model=interviewer_chat(),
                tools=[],
                system_prompt=prompt,
            )
        return _tutor_agents[key]


def invoke_tutor(
    system_prompt: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> str:
    agent = _get_or_create_tutor_agent(system_prompt)
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    result = agent.invoke({"messages": messages})
    ai_messages = result.get("messages", [])
    if not ai_messages:
        return ""
    last = ai_messages[-1]
    content = getattr(last, "content", "")
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def stream_tutor(
    system_prompt: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> Generator[str]:
    agent = _get_or_create_tutor_agent(system_prompt)
    messages: list[dict] = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    for event in agent.stream({"messages": messages}, stream_mode="messages"):
        if not isinstance(event, tuple) or len(event) != 2:
            continue
        chunk, _metadata = event
        if not isinstance(chunk, AIMessageChunk):
            continue
        content = chunk.content
        if isinstance(content, str) and content:
            yield content
        elif isinstance(content, list):
            text = "".join(
                str(item) if isinstance(item, str) else ""
                for item in content
            )
            if text:
                yield text


def parse_suggestions(response: str) -> tuple[str, list[str]]:
    match = re.search(r"<suggestions>\s*(\[.*?\])\s*</suggestions>", response, re.DOTALL)
    if not match:
        return response, []

    raw_json = match.group(1)
    cleaned_response = response[: match.start()] + response[match.end() :]
    cleaned_response = cleaned_response.strip()

    try:
        suggestions = json.loads(raw_json)
        if isinstance(suggestions, list):
            return cleaned_response, [str(s) for s in suggestions if isinstance(s, str)]
    except (json.JSONDecodeError, ValueError):
        pass

    return cleaned_response, []
