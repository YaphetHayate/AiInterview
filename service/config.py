from typing import List, Optional


class InterviewConfig:
    def __init__(
        self,
        tech_stack: List[str],
        position: str = "技术开发",
        interview_style: str = "professional",
        difficulty: str = "medium",
        resume_info: Optional[str] = None,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        mode: str = "simulation",
    ):
        self.tech_stack = tech_stack
        self.position = position
        self.interview_style = interview_style
        self.difficulty = difficulty
        self.resume_info = resume_info
        self.candidate_id = candidate_id
        self.job_id = job_id
        self.mode = mode
