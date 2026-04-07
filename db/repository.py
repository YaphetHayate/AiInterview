from typing import Optional
from uuid import uuid4
from threading import Lock
import json
import re

from db.connection import db_cursor


class TechStackRepository:
    @staticmethod
    def get_all():
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("SELECT id, name, created_at FROM tech_stacks ORDER BY name")
            return cur.fetchall()

    @staticmethod
    def get_by_name(name: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("SELECT id, name, created_at FROM tech_stacks WHERE name = %s", (name,))
            return cur.fetchone()

    @staticmethod
    def create(name: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "INSERT INTO tech_stacks (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id, name, created_at",
                (name,)
            )
            return cur.fetchone()


class QuestionBankRepository:
    @staticmethod
    def get_by_tech(tech_stack: str, difficulty: str = "medium", limit: int = 10):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "SELECT id, tech_stack, difficulty, content, created_at FROM question_bank WHERE tech_stack = %s AND difficulty = %s ORDER BY RANDOM() LIMIT %s",
                (tech_stack, difficulty, limit)
            )
            return cur.fetchall()

    @staticmethod
    def get_random_questions(tech_stacks: list, difficulty: str = "medium", limit: int = 10):
        with db_cursor(dict_cursor=True) as (cur, conn):
            placeholders = ','.join(['%s'] * len(tech_stacks))
            cur.execute(
                f"SELECT id, tech_stack, difficulty, content, created_at FROM question_bank WHERE tech_stack IN ({placeholders}) AND difficulty = %s ORDER BY RANDOM() LIMIT %s",
                (*tech_stacks, difficulty, limit)
            )
            return cur.fetchall()


class SessionRepository:
    @staticmethod
    def create(session_id: str, tech_stack: str = "", position: str = "", difficulty: str = "medium", style: str = "professional", mode: str = "simulation", system_prompt: str = "", current_stage: str = "", resume_filename: str = "", resume_info: str = "", candidate_id: str = "", job_id: str = ""):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                """INSERT INTO interview_sessions 
                (session_id, tech_stack, position, difficulty, style, mode, system_prompt, current_stage, resume_filename, resume_info, candidate_id, job_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                ON CONFLICT (session_id) DO UPDATE SET 
                tech_stack = EXCLUDED.tech_stack,
                position = EXCLUDED.position,
                difficulty = EXCLUDED.difficulty,
                style = EXCLUDED.style,
                mode = EXCLUDED.mode,
                system_prompt = EXCLUDED.system_prompt,
                current_stage = EXCLUDED.current_stage,
                resume_filename = EXCLUDED.resume_filename,
                resume_info = EXCLUDED.resume_info,
                candidate_id = EXCLUDED.candidate_id,
                job_id = EXCLUDED.job_id,
                updated_at = NOW()
                RETURNING *""",
                (session_id, tech_stack, position, difficulty, style, mode, system_prompt, current_stage, resume_filename, resume_info, candidate_id, job_id)
            )
            return cur.fetchone()

    @staticmethod
    def get(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("SELECT * FROM interview_sessions WHERE session_id = %s", (session_id,))
            return cur.fetchone()

    @staticmethod
    def update(session_id: str, **kwargs):
        if not kwargs:
            return None
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(session_id)
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                f"UPDATE interview_sessions SET {set_clause}, updated_at = NOW() WHERE session_id = %s RETURNING *",
                values
            )
            return cur.fetchone()

    @staticmethod
    def delete(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("DELETE FROM interview_sessions WHERE session_id = %s", (session_id,))
            return cur.rowcount > 0


class QuestionRepository:
    @staticmethod
    def save_questions(session_id: str, questions: list):
        with db_cursor(dict_cursor=True) as (cur, conn):
            results = []
            for i, content in enumerate(questions):
                cur.execute(
                    """INSERT INTO interview_questions 
                    (session_id, question_id, content, status, follow_up_count, max_follow_ups) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (session_id, question_id) DO UPDATE SET 
                    content = EXCLUDED.content,
                    updated_at = NOW()
                    RETURNING *""",
                    (session_id, i + 1, content, "pending", 0, 3)
                )
                results.append(cur.fetchone())
            return results

    @staticmethod
    def get_by_session(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                """SELECT iq.*, ist.tech_stack, ist.position, ist.difficulty 
                FROM interview_questions iq 
                LEFT JOIN interview_sessions ist ON iq.session_id = ist.session_id 
                WHERE iq.session_id = %s 
                ORDER BY iq.question_id""",
                (session_id,)
            )
            return cur.fetchall()

    @staticmethod
    def update_status(db_id: int, status: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "UPDATE interview_questions SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, db_id)
            )
            return cur.rowcount > 0

    @staticmethod
    def increment_follow_up(db_id: int):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "UPDATE interview_questions SET follow_up_count = follow_up_count + 1, updated_at = NOW() WHERE id = %s",
                (db_id,)
            )
            return cur.rowcount > 0

    @staticmethod
    def get_progress(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                """SELECT 
                    COUNT(*) as total_questions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
                FROM interview_questions 
                WHERE session_id = %s""",
                (session_id,)
            )
            result = cur.fetchone()
            if result:
                result['is_finished'] = result['pending'] == 0 and result['in_progress'] == 0
            return result

    @staticmethod
    def delete_by_session(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("DELETE FROM interview_questions WHERE session_id = %s", (session_id,))
            return cur.rowcount > 0


class AnswerRepository:
    @staticmethod
    def create(session_id: str, question_db_id: int, question_id: int, answer: str = "", feedback: str = "", follow_up_question: str = "", is_follow_up: bool = False):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                """INSERT INTO interview_answers 
                (session_id, question_db_id, question_id, answer, feedback, follow_up_question, is_follow_up) 
                VALUES (%s, %s, %s, %s, %s, %s, %s) 
                RETURNING *""",
                (session_id, question_db_id, question_id, answer, feedback, follow_up_question, is_follow_up)
            )
            return cur.fetchone()

    @staticmethod
    def get_by_question(question_db_id: int):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "SELECT * FROM interview_answers WHERE question_db_id = %s ORDER BY created_at",
                (question_db_id,)
            )
            return cur.fetchall()

    @staticmethod
    def get_by_session(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "SELECT * FROM interview_answers WHERE session_id = %s ORDER BY created_at",
                (session_id,)
            )
            return cur.fetchall()


class ConversationRepository:
    @staticmethod
    def append(session_id: str, role: str, content: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "INSERT INTO interview_conversations (session_id, role, content) VALUES (%s, %s, %s) RETURNING *",
                (session_id, role, content)
            )
            return cur.fetchone()

    @staticmethod
    def get_messages(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "SELECT role, content FROM interview_conversations WHERE session_id = %s ORDER BY created_at",
                (session_id,)
            )
            rows = cur.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]

    @staticmethod
    def delete_by_session(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("DELETE FROM interview_conversations WHERE session_id = %s", (session_id,))
            return cur.rowcount > 0


class LearningRecordRepository:
    @staticmethod
    def create(session_id: str, question_bank_id: Optional[int], knowledge_point: str, status: str = "asking", explanation: str = ""):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                """INSERT INTO learning_records 
                (session_id, question_bank_id, knowledge_point, status, explanation) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING *""",
                (session_id, question_bank_id, knowledge_point, status, explanation)
            )
            return cur.fetchone()

    @staticmethod
    def get_by_session(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "SELECT * FROM learning_records WHERE session_id = %s ORDER BY created_at",
                (session_id,)
            )
            return cur.fetchall()

    @staticmethod
    def update_status(record_id: int, status: str, explanation: str = ""):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "UPDATE learning_records SET status = %s, explanation = %s, updated_at = NOW() WHERE id = %s RETURNING *",
                (status, explanation, record_id)
            )
            return cur.fetchone()

    @staticmethod
    def get_latest(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute(
                "SELECT * FROM learning_records WHERE session_id = %s ORDER BY created_at DESC LIMIT 1",
                (session_id,)
            )
            return cur.fetchone()

    @staticmethod
    def delete_by_session(session_id: str):
        with db_cursor(dict_cursor=True) as (cur, conn):
            cur.execute("DELETE FROM learning_records WHERE session_id = %s", (session_id,))
            return cur.rowcount > 0