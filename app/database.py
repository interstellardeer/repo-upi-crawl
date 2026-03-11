import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine, text

from app.config import settings

os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.DB_PATH}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables and set up FTS5 virtual table."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.exec(text("PRAGMA journal_mode=WAL"))
        # FTS5 table for full-text search on papers
        session.exec(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS paper_fts USING fts5(
                title,
                abstract_id,
                abstract_en,
                content='paper',
                content_rowid='id'
            )
        """))
        # Keep FTS in sync via triggers
        session.exec(text("""
            CREATE TRIGGER IF NOT EXISTS paper_ai AFTER INSERT ON paper BEGIN
                INSERT INTO paper_fts(rowid, title, abstract_id, abstract_en)
                VALUES (new.id, new.title, new.abstract_id, new.abstract_en);
            END
        """))
        session.exec(text("""
            CREATE TRIGGER IF NOT EXISTS paper_ad AFTER DELETE ON paper BEGIN
                INSERT INTO paper_fts(paper_fts, rowid, title, abstract_id, abstract_en)
                VALUES ('delete', old.id, old.title, old.abstract_id, old.abstract_en);
            END
        """))
        session.exec(text("""
            CREATE TRIGGER IF NOT EXISTS paper_au AFTER UPDATE ON paper BEGIN
                INSERT INTO paper_fts(paper_fts, rowid, title, abstract_id, abstract_en)
                VALUES ('delete', old.id, old.title, old.abstract_id, old.abstract_en);
                INSERT INTO paper_fts(rowid, title, abstract_id, abstract_en)
                VALUES (new.id, new.title, new.abstract_id, new.abstract_en);
            END
        """))
        session.commit()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
