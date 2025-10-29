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

@router.get("/tables/{table_name}")
async def get_table_data(table_name: str, db: Session = Depends(get_db)):
    """Get all data from a specific table."""
    # Prevent SQL injection by checking if the table name is valid
    tables = db.execute(sqlalchemy.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)).fetchall()
    if (table_name,) not in tables:
        raise HTTPException(status_code=404, detail="Table not found")

    query = sqlalchemy.text(f"SELECT * FROM {table_name}")
    result = db.execute(query)
    columns = result.keys()
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]