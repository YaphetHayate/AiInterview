import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from db.repository import QuestionBankRepository


def fetch_and_format(tech_stacks: list[str], difficulty: str, limit: int) -> str:
    rows = QuestionBankRepository.get_random_questions(tech_stacks, difficulty, limit)
    if not rows:
        stacks_str = ", ".join(tech_stacks)
        return f"未找到匹配的题目（技术栈：{stacks_str} | 难度：{difficulty}）。请尝试其他技术栈或难度。"

    stacks_str = ", ".join(tech_stacks)
    lines = [f"已从题库获取 {len(rows)} 道题目（技术栈：{stacks_str} | 难度：{difficulty}）："]
    for i, row in enumerate(rows, 1):
        lines.append(f"问题{i}：{row['content']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="从 question_bank 表获取面试题目")
    parser.add_argument("--tech-stacks", required=True, help="逗号分隔的技术栈名称，如 Java,Redis")
    parser.add_argument("--difficulty", default="medium", choices=["basic", "medium", "hard"], help="难度级别（默认 medium）")
    parser.add_argument("--limit", type=int, default=5, help="获取题目数量（默认 5）")
    args = parser.parse_args()

    tech_stacks = [s.strip() for s in args.tech_stacks.split(",")]
    result = fetch_and_format(tech_stacks, args.difficulty, args.limit)
    print(result)


if __name__ == "__main__":
    main()
