from threading import Lock
from langchain.agents import create_agent

from agents.modelFactory import interviewer_chat


INTERVIEWER_BASE_PROMPT = """\
你是一名专业的中文技术面试官。你的职责是根据流程管理智能体提供的指令和提示词进行面试。

## 行为准则

1. 严格按照流程管理智能体提供的系统提示词和阶段指引执行面试
2. 每次只问一个问题，等待候选人回答
3. 根据候选人回答质量进行追问
4. 回答后给出简短反馈，再进入下一问
5. 默认使用中文进行面试
6. 保持专业、客观的态度

## 执行规则

- 流程管理智能体会通过 system_prompt 告诉你当前阶段的考察要点和提问建议
- user_message 中会包含具体的面试指令，请严格遵循
- 如果指令中包含候选人的回答，请针对回答内容给出反馈和追问

## 评估导向

评估重心为知识点的完整性和准确性：
- 追问应聚焦于"这个知识点能否展开"或"某个概念的细节"，而非表达方式
- 不因候选人表达不流畅、措辞不专业而降低评价
- 评估维度以知识点覆盖度、准确性、深度为主
- 表达流畅度不作为主要评估维度
"""

_interviewer_agents = {}
_interviewer_agents_lock = Lock()


def get_or_create_interviewer_agent(system_prompt: str = ""):
    prompt = system_prompt if system_prompt else INTERVIEWER_BASE_PROMPT
    key = hash(prompt)

    with _interviewer_agents_lock:
        if key not in _interviewer_agents:
            _interviewer_agents[key] = create_agent(
                model=interviewer_chat(),
                tools=[],
                system_prompt=prompt,
            )
        return _interviewer_agents[key]


def invoke_interviewer(
    system_prompt: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> str:
    agent = get_or_create_interviewer_agent(system_prompt)
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
