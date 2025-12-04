from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Question


router = APIRouter(
    prefix='/api/question',
    tags=['question'],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class QuestionRead(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime

    class Config:
        orm_mode = True


@router.get('', response_model=List[QuestionRead])
def question_list(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.id.desc()).all()
    return questions