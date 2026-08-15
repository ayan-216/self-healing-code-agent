from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.db.database import get_db
from src.evaluation.evaluator import evaluator

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
def get_metrics(db: Session = Depends(get_db)):
    return evaluator.compute_platform_metrics(db)
