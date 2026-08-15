from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.db.database import get_db
from src.core.db.models import Repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("/")
def list_repositories(db: Session = Depends(get_db)):
    repos = db.query(Repository).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "owner": r.owner,
            "clone_url": r.clone_url,
            "created_at": r.created_at
        } for r in repos
    ]
