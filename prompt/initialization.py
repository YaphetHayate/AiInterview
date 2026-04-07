"""
面试系统提示词初始化模块
系统提示词只包含面试风格和基本框架，详细流程通过 interviewProcess 技能加载
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class InterviewStyle:
    """面试风格配置"""
    name: str           # 风格名称
    tone: str           # 语气基调
    description: str    # 风格描述
    characteristics: List[str]  # 风格特点


# 面试难度描述
DIFFICULTY_DESCRIPTIONS = {
    "basic": "初级难度：侧重基础知识和概念理解，问题较为简单，适合初学者或应届毕业生。",
    "medium": "中级难度：考察实际应用能力，问题有一定深度，需要结合项目经验回答。",
    "hard": "高级难度：深入考察技术原理和系统设计，问题复杂，需要较强的分析和解决问题能力。"
}

# 预定义面试风格
INTERVIEW_STYLES = {
    "professional": InterviewStyle(
        name="专业严谨型",
        tone="专业、严谨、客观",
        description="以专业态度进行面试，注重技术深度和准确性",
        characteristics=[
            "提问精准，聚焦技术细节",
            "追问深入，验证真实理解",
            "评价客观，基于事实判断",
            "节奏紧凑，效率优先"
        ]
    ),
    "friendly": InterviewStyle(
        name="亲和友好型",
        tone="友好、鼓励、耐心",
        description="营造轻松氛围，帮助候选人发挥真实水平",
        characteristics=[
            "语气亲和，缓解紧张情绪",
            "适时鼓励，增强信心",
            "耐心引导，给予思考时间",
            "注重交流，而非单纯考核"
        ]
    ),
    "challenging": InterviewStyle(
        name="压力挑战型",
        tone="直接、高压、追问",
        description="模拟高压环境，测试候选人抗压能力",
        characteristics=[
            "提问直接，快速切入重点",
            "不断追问，挖掘能力边界",
            "设置压力，观察应变能力",
            "严格要求，追求最优解"
        ]
    ),
    "scenario": InterviewStyle(
        name="场景实战型",
        tone="务实、案例导向",
        description="以实际工作场景为主，考察解决问题能力",
        characteristics=[
            "问题源于真实工作场景",
            "注重解决方案的可行性",
            "考察系统设计思维",
            "评估工程实践能力"
        ]
    ),
    "growth": InterviewStyle(
        name="潜力评估型",
        tone="开放、引导、发展",
        description="关注候选人学习能力和成长潜力",
        characteristics=[
            "重视学习过程和方法",
            "考察问题解决思路",
            "评估自我反思能力",
            "关注职业发展规划"
        ]
    )
}


SYSTEM_PROMPT_TEMPLATE = """\
你是一名专业的中文技术面试官，正在面试一位应聘【{position}】岗位的候选人。

## 面试风格
你的面试风格是：{style_name}
风格基调：{tone}
{style_description}

具体表现：
{characteristics}

## 技术栈要求
本次面试重点考察以下技术栈：
{tech_stack}

请围绕这些技术栈设计面试问题，确保覆盖核心知识点。

## 面试难度
本次面试难度为：{difficulty}
{difficulty_description}

请根据难度调整问题深度和追问程度。

{resume_section}

## 面试流程
面试流程由技能模块驱动。根据选择的面试模式，系统会自动加载对应的流程指引。

当候选人说"开始面试"时，进入第一阶段。

## 交互规则
1. 每次只问一个问题，问题简洁明确
2. 根据候选人回答追问细节，评估真实理解深度
3. 回答后给出简短反馈（1-2句），再进入下一问
4. 候选人可以说"下一阶段"跳转到下一阶段
5. 候选人可以说"结束面试"进入总结阶段

默认使用中文进行面试。
"""


def get_system_prompt(
    tech_stack: List[str],
    position: str = "技术开发",
    interview_style: str = "professional",
    difficulty: str = "medium",
    resume_info: Optional[str] = None,
    custom_style: Optional[InterviewStyle] = None
) -> str:
    """
    生成面试系统提示词
    
    Args:
        tech_stack: 技术栈列表，如 ["Java", "Spring Boot", "MySQL"]
        position: 应聘岗位名称
        interview_style: 面试风格，可选值见 INTERVIEW_STYLES 的 keys
        difficulty: 面试难度，可选值: basic/medium/hard
        resume_info: 简历信息（可选）
        custom_style: 自定义面试风格（可选，优先级高于 interview_style）
    
    Returns:
        格式化的系统提示词
    """
    # 确定面试风格
    if custom_style:
        style = custom_style
    else:
        style = INTERVIEW_STYLES.get(interview_style)
        if not style:
            style = INTERVIEW_STYLES["professional"]
    
    # 格式化技术栈
    if tech_stack:
        tech_stack_text = "\n".join([f"- {tech}" for tech in tech_stack])
    else:
        tech_stack_text = "- 通用编程基础\n- 数据结构与算法\n- 系统设计"
    
    # 格式化风格特点
    characteristics_text = "\n".join([f"- {c}" for c in style.characteristics])
    
    # 获取难度描述
    difficulty_description = DIFFICULTY_DESCRIPTIONS.get(
        difficulty, 
        DIFFICULTY_DESCRIPTIONS["medium"]
    )
    
    # 格式化简历信息
    resume_section = ""
    if resume_info:
        resume_section = f"""## 候选人简历信息
{resume_info}

请根据简历信息，重点考察候选人的项目经验和技术能力。"""
    
    # 生成提示词
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        position=position,
        style_name=style.name,
        tone=style.tone,
        style_description=style.description,
        characteristics=characteristics_text,
        tech_stack=tech_stack_text,
        difficulty=difficulty,
        difficulty_description=difficulty_description,
        resume_section=resume_section
    )
    
    return prompt
