from pathlib import Path
from langchain_core.tools import tool

from db.repository import QuestionBankRepository

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills" / "interviewManager"


@tool
def read_skill_md() -> str:
    """读取面试流程管理技能文件 skills/interviewManager/SKILL.md，获取完整的面试流程定义。"""
    path = SKILLS_DIR / "SKILL.md"
    if not path.exists():
        return f"文件不存在: {path}"
    return path.read_text(encoding="utf-8")


@tool
def read_stage_file(stage_number: int) -> str:
    """根据阶段编号(1-4)读取对应的阶段指引文件。

    阶段对应:
    1 - 基础知识考察 (stage1_basic_knowledge.md)
    2 - 项目经历考察 (stage2_project_experience.md)
    3 - 岗位需求考察 (stage3_job_matching.md)
    4 - 面试总结 (stage4_summary.md)

    Args:
        stage_number: 阶段编号，1到4的整数
    """
    stage_files = {
        1: "stage1_basic_knowledge.md",
        2: "stage2_project_experience.md",
        3: "stage3_job_matching.md",
        4: "stage4_summary.md",
    }
    filename = stage_files.get(stage_number)
    if not filename:
        return f"无效的阶段编号: {stage_number}，有效值为 1-4"
    path = SKILLS_DIR / "references" / "stages" / filename
    if not path.exists():
        return f"文件不存在: {path}"
    return path.read_text(encoding="utf-8")


@tool
def fetch_questions_from_bank(tech_stacks: str, difficulty: str, limit: int = 5) -> str:
    """从面试题库获取面试题目。在 stage1（基础知识考察）阶段开始时调用此工具获取真实题目。

    Args:
        tech_stacks: 逗号分隔的技术栈名称，如 "Java,Redis"
        difficulty: 难度级别，可选值: "basic", "medium", "hard"
        limit: 获取题目数量，默认5
    """
    stacks = [s.strip() for s in tech_stacks.split(",")]
    try:
        rows = QuestionBankRepository.get_random_questions(stacks, difficulty, limit)
    except Exception as e:
        return f"获取题目失败：{e}"

    if not rows:
        stacks_display = ", ".join(stacks)
        return f"未找到匹配的题目（技术栈：{stacks_display} | 难度：{difficulty}）。请尝试其他技术栈或难度。"

    stacks_display = ", ".join(stacks)
    lines = [f"已从题库获取 {len(rows)} 道题目（技术栈：{stacks_display} | 难度：{difficulty}）："]
    for i, row in enumerate(rows, 1):
        content = row["content"] if isinstance(row, dict) else row[3]
        lines.append(f"问题{i}：{content}")

    return "\n".join(lines)


ALL_TOOLS = [read_skill_md, read_stage_file, fetch_questions_from_bank]
