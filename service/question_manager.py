"""
面试问题管理模块
用于管理面试问题列表、追问记录和状态追踪
"""

from threading import Lock
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from db.repository import QuestionRepository, AnswerRepository


class QuestionStatus(str, Enum):
    """问题状态枚举"""
    PENDING = "pending"           # 未提问
    IN_PROGRESS = "in_progress"   # 进行中（已提问，追问中）
    COMPLETED = "completed"       # 已完成


@dataclass
class AnswerRecord:
    """回答记录"""
    answer: str                           # 候选人回答内容
    feedback: str = ""                    # 面试官反馈
    follow_up_question: str = ""          # 追问内容
    is_follow_up: bool = False            # 是否为追问


@dataclass
class QuestionRecord:
    """问题记录"""
    question_id: int                      # 问题序号（从1开始）
    content: str                          # 问题内容
    status: QuestionStatus = QuestionStatus.PENDING
    follow_up_count: int = 0              # 已追问次数
    max_follow_ups: int = 3               # 最大追问次数
    answers: list[AnswerRecord] = field(default_factory=list)
    
    def add_answer(self, answer: str, feedback: str = "", 
                   follow_up_question: str = "", is_follow_up: bool = False):
        """添加回答记录"""
        self.answers.append(AnswerRecord(
            answer=answer,
            feedback=feedback,
            follow_up_question=follow_up_question,
            is_follow_up=is_follow_up
        ))
        if is_follow_up:
            self.follow_up_count += 1
    
    def can_follow_up(self) -> bool:
        """是否还可以追问"""
        return self.follow_up_count < self.max_follow_ups
    
    def mark_completed(self):
        """标记为已完成"""
        self.status = QuestionStatus.COMPLETED


@dataclass
class InterviewSession:
    """面试会话"""
    session_id: str
    tech_stack: str
    position: str
    difficulty: str
    questions: list[QuestionRecord] = field(default_factory=list)
    current_question_index: int = -1      # 当前问题索引，-1表示还未开始


class QuestionManager:
    
    def __init__(self):
        self._sessions: dict[str, InterviewSession] = {}
        self._lock = Lock()
        self._question_db_map: dict[str, dict[int, int]] = {}

    def _load_from_db(self, session_id: str) -> Optional[InterviewSession]:
        rows = QuestionRepository.get_by_session(session_id)
        if not rows:
            return None
        question_records = []
        db_map = {}
        for r in rows:
            qr = QuestionRecord(
                question_id=r["question_id"],
                content=r["content"],
                status=QuestionStatus(r["status"]),
                follow_up_count=r["follow_up_count"],
                max_follow_ups=r["max_follow_ups"],
            )
            answer_rows = AnswerRepository.get_by_question(r["id"])
            for ar in answer_rows:
                qr.answers.append(AnswerRecord(
                    answer=ar["answer"],
                    feedback=ar["feedback"],
                    follow_up_question=ar["follow_up_question"],
                    is_follow_up=ar["is_follow_up"],
                ))
            question_records.append(qr)
            db_map[r["question_id"]] = r["id"]

        self._question_db_map[session_id] = db_map
        first = rows[0]
        session = InterviewSession(
            session_id=session_id,
            tech_stack=first.get("tech_stack", ""),
            position="",
            difficulty="",
            questions=question_records,
        )
        return session
    
    def save_questions(self, session_id: str, questions: list[str], 
                       tech_stack: str = "", position: str = "", 
                       difficulty: str = "") -> InterviewSession:
        with self._lock:
            question_records = [
                QuestionRecord(question_id=i + 1, content=q)
                for i, q in enumerate(questions)
            ]
            
            session = InterviewSession(
                session_id=session_id,
                tech_stack=tech_stack,
                position=position,
                difficulty=difficulty,
                questions=question_records
            )
            
            self._sessions[session_id] = session

        try:
            db_rows = QuestionRepository.save_questions(session_id, questions)
            db_map = {r["question_id"]: r["id"] for r in db_rows}
            self._question_db_map[session_id] = db_map
        except Exception as e:
            print(f"[WARN] 保存问题到数据库失败: {e}")

        return session
    
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]
        session = self._load_from_db(session_id)
        if session:
            with self._lock:
                self._sessions[session_id] = session
            return session
        return None
    
    def get_latest_question(self, session_id: str) -> Optional[QuestionRecord]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                session = self._load_from_db(session_id)
                if session:
                    self._sessions[session_id] = session
                    self._lock.release()
                    self._lock.acquire()
            if not session or not session.questions:
                return None
            
            for q in session.questions:
                if q.status == QuestionStatus.IN_PROGRESS:
                    return q
            
            for q in session.questions:
                if q.status == QuestionStatus.PENDING:
                    q.status = QuestionStatus.IN_PROGRESS
                    session.current_question_index = q.question_id - 1
                    try:
                        db_map = self._question_db_map.get(session_id, {})
                        db_id = db_map.get(q.question_id)
                        if db_id:
                            QuestionRepository.update_status(db_id, "in_progress")
                    except Exception:
                        pass
                    return q
            
            return None
    
    def update_question(self, session_id: str, question_id: int, 
                        answer: str, feedback: str = "",
                        follow_up_question: str = "", 
                        is_follow_up: bool = False) -> Optional[QuestionRecord]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                session = self._load_from_db(session_id)
                if session:
                    self._sessions[session_id] = session
            
            if not session:
                return None
            
            question = None
            for q in session.questions:
                if q.question_id == question_id:
                    question = q
                    break
            
            if not question:
                return None
            
            question.add_answer(
                answer=answer,
                feedback=feedback,
                follow_up_question=follow_up_question,
                is_follow_up=is_follow_up
            )

        try:
            db_map = self._question_db_map.get(session_id, {})
            db_id = db_map.get(question_id)
            if db_id:
                AnswerRepository.create(
                    session_id=session_id,
                    question_db_id=db_id,
                    question_id=question_id,
                    answer=answer,
                    feedback=feedback,
                    follow_up_question=follow_up_question,
                    is_follow_up=is_follow_up,
                )
                if is_follow_up:
                    QuestionRepository.increment_follow_up(db_id)
        except Exception as e:
            print(f"[WARN] 保存回答到数据库失败: {e}")

        return question
    
    def complete_question(self, session_id: str, question_id: int) -> Optional[QuestionRecord]:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            
            for q in session.questions:
                if q.question_id == question_id:
                    q.mark_completed()
                    try:
                        db_map = self._question_db_map.get(session_id, {})
                        db_id = db_map.get(question_id)
                        if db_id:
                            QuestionRepository.update_status(db_id, "completed")
                    except Exception:
                        pass
                    return q
            
            return None
    
    def get_progress(self, session_id: str) -> dict:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                session = self._load_from_db(session_id)
                if session:
                    self._sessions[session_id] = session
        if not session:
            try:
                return QuestionRepository.get_progress(session_id)
            except Exception:
                return {"error": "Session not found"}
        
        total = len(session.questions)
        completed = sum(1 for q in session.questions 
                      if q.status == QuestionStatus.COMPLETED)
        in_progress = sum(1 for q in session.questions 
                        if q.status == QuestionStatus.IN_PROGRESS)
        pending = total - completed - in_progress
        
        return {
            "session_id": session_id,
            "total_questions": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "is_finished": pending == 0 and in_progress == 0
        }
    
    def remove_session(self, session_id: str) -> bool:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._question_db_map.pop(session_id, None)
        try:
            QuestionRepository.delete_by_session(session_id)
        except Exception:
            pass
        return True
    
    def get_all_questions(self, session_id: str) -> list[QuestionRecord]:
        """获取所有问题记录"""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            return list(session.questions)


# 全局实例
question_manager = QuestionManager()
