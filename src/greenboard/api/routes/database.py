from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
import sqlalchemy

router = APIRouter(prefix="/db", tags=["database"])

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check database connection health."""
    result = db.execute(sqlalchemy.text("SELECT now()")).fetchone()
    return {"status": "healthy", "database_time": result[0]}

@router.get("/tables")
async def get_tables(db: Session = Depends(get_db)):
    """Get all tables in the public schema."""
    tables = db.execute(sqlalchemy.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)).fetchall()
    return {"tables": [table[0] for table in tables]}