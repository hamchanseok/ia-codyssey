from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Question


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class QuestionCreate(BaseModel):
    subject: str
    content: str


class QuestionRead(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime

    class Config:
        orm_mode = True


@app.post('/questions', response_model=QuestionRead)
def create_question(question_in: QuestionCreate, db: Session = Depends(get_db)):
    question = Question(
        subject=question_in.subject,
        content=question_in.content,
        create_date=datetime.utcnow(),
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@app.get('/questions', response_model=List[QuestionRead])
def read_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.id.desc()).all()
    return questions


@app.get('/questions/{question_id}', response_model=QuestionRead)
def read_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail='Question not found')
    return question