SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tech_stacks (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(64) UNIQUE NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS question_bank (
    id          SERIAL PRIMARY KEY,
    tech_stack  VARCHAR(64)  NOT NULL,
    difficulty  VARCHAR(32)  NOT NULL DEFAULT 'medium',
    content     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id              SERIAL PRIMARY KEY,
    session_id      VARCHAR(64) UNIQUE NOT NULL,
    tech_stack      VARCHAR(255) NOT NULL DEFAULT '',
    position        VARCHAR(255) NOT NULL DEFAULT '',
    difficulty      VARCHAR(32)  NOT NULL DEFAULT 'medium',
    style           VARCHAR(64)  NOT NULL DEFAULT 'professional',
    mode            VARCHAR(32)  NOT NULL DEFAULT 'simulation',
    system_prompt   TEXT DEFAULT '',
    current_stage   VARCHAR(64) DEFAULT '',
    resume_filename VARCHAR(255) DEFAULT '',
    resume_info     TEXT DEFAULT '',
    candidate_id    VARCHAR(64) DEFAULT '',
    job_id          VARCHAR(64) DEFAULT '',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_questions (
    id              SERIAL PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    question_id     INT NOT NULL,
    content         TEXT NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    follow_up_count INT NOT NULL DEFAULT 0,
    max_follow_ups  INT NOT NULL DEFAULT 3,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, question_id)
);

CREATE TABLE IF NOT EXISTS interview_answers (
    id                  SERIAL PRIMARY KEY,
    session_id          VARCHAR(64) NOT NULL,
    question_db_id      INT NOT NULL REFERENCES interview_questions(id) ON DELETE CASCADE,
    question_id         INT NOT NULL,
    answer              TEXT DEFAULT '',
    feedback            TEXT DEFAULT '',
    follow_up_question  TEXT DEFAULT '',
    is_follow_up        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_conversations (
    id          SERIAL PRIMARY KEY,
    session_id  VARCHAR(64) NOT NULL REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    role        VARCHAR(16) NOT NULL,
    content     TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS learning_records (
    id                SERIAL PRIMARY KEY,
    session_id        VARCHAR(64) NOT NULL REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    question_bank_id  INT,
    knowledge_point   TEXT NOT NULL,
    status            VARCHAR(32) NOT NULL DEFAULT 'asking',
    explanation       TEXT DEFAULT '',
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_bank_tech ON question_bank(tech_stack, difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_session ON interview_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_answers_session ON interview_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON interview_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_learning_session ON learning_records(session_id);
"""

SEED_SQL = """
INSERT INTO tech_stacks (name) VALUES
    ('Java'), ('Redis'), ('MySQL')
ON CONFLICT (name) DO NOTHING;

INSERT INTO question_bank (tech_stack, difficulty, content) VALUES
    ('Java', 'basic',  '请简要介绍Java的四大基本特性（封装、继承、多态、抽象）。'),
    ('Java', 'basic',  'Java中==和equals()有什么区别？hashCode()和equals()的关系是什么？'),
    ('Java', 'basic',  '请解释Java中的自动装箱和拆箱，以及可能引发的问题。'),
    ('Java', 'medium', 'JVM的内存模型是怎样的？堆内存是如何划分的？'),
    ('Java', 'medium', '请详细讲解Java的垃圾回收机制，常见的GC算法有哪些？'),
    ('Java', 'medium', 'HashMap的底层实现原理是什么？JDK1.8做了哪些优化？'),
    ('Java', 'medium', 'synchronized和ReentrantLock有什么区别？各自的适用场景？'),
    ('Java', 'hard',   '请分析ConcurrentHashMap在JDK1.7和1.8中的实现差异。'),
    ('Java', 'hard',   'JVM类加载机制是怎样的？什么是双亲委派模型？如何打破它？'),
    ('Java', 'hard',   '请讲解Java线程池的核心参数和工作原理，以及合理的线程数配置策略。'),

    ('Redis', 'basic',  'Redis支持哪些数据类型？各自适合什么场景？'),
    ('Redis', 'basic',  '请解释Redis中String类型的常用命令及其应用场景。'),
    ('Redis', 'basic',  'Redis的持久化机制有哪些？RDB和AOF的区别是什么？'),
    ('Redis', 'medium', '请详细解释Redis的过期键删除策略和内存淘汰机制。'),
    ('Redis', 'medium', '什么是缓存穿透、缓存击穿和缓存雪崩？分别如何解决？'),
    ('Redis', 'medium', 'Redis的哨兵模式和集群模式有什么区别？各自的工作原理是什么？'),
    ('Redis', 'hard',   'Redis的底层数据结构有哪些？skiplist、ziplist、quicklist分别用在什么地方？'),
    ('Redis', 'hard',   '请解释Redis事务的实现机制，MULTI/EXEC与Lua脚本有什么区别？'),
    ('Redis', 'hard',   'Redis集群的槽位分配和数据迁移是如何工作的？'),

    ('MySQL', 'basic',  'MySQL支持的存储引擎有哪些？InnoDB和MyISAM的核心区别是什么？'),
    ('MySQL', 'basic',  '请解释MySQL中事务的ACID特性，InnoDB是如何保证这四个特性的？'),
    ('MySQL', 'basic',  'MySQL中char和varchar有什么区别？DATETIME和TIMESTAMP有什么不同？'),
    ('MySQL', 'medium', '请详细讲解MySQL的索引结构，B+树相比B树有什么优势？'),
    ('MySQL', 'medium', '什么是聚簇索引和非聚簇索引？覆盖索引和回表查询分别是什么？'),
    ('MySQL', 'medium', 'MySQL的事务隔离级别有哪些？InnoDB默认使用哪种？它是如何解决幻读问题的？'),
    ('MySQL', 'medium', '请解释MySQL的MVCC机制，它的实现原理是什么？'),
    ('MySQL', 'hard',   '如何分析和优化慢查询？EXPLAIN执行计划中的关键字段分别代表什么含义？'),
    ('MySQL', 'hard',   '请讲解MySQL的锁机制，行锁、表锁、间隙锁、临键锁分别在什么场景下使用？'),
    ('MySQL', 'hard',   'MySQL主从复制的原理是什么？有哪些复制方式？如何解决主从延迟问题？')
ON CONFLICT DO NOTHING;
"""
