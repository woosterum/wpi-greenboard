from fastapi import APIRouter, Depends
from sqlmodel import Session, select, text

from ..database import get_session

router = APIRouter(prefix="/db", tags=["database"])

@router.get("/health")
async def health_check(db: Session = Depends(get_session)):
    """Check database connection health."""
    query = text("""select now()""")
    result = db.exec(query).one()
    return {"status": "healthy", "database_time": result[0]}

@router.get("/tables")
async def get_tables(db: Session = Depends(get_session)):
    """Get all tables in the public schema."""
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    results = db.exec(query).all()
    return {"tables": [row[0] for row in results]}