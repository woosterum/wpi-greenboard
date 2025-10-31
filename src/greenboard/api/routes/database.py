from fastapi import APIRouter, Depends
from sqlmodel import Session, select, text

from ..database import get_session
from fastapi import HTTPException

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

@router.get("/tables/{table_name}")
async def get_table_data(table_name: str, db: Session = Depends(get_session)):
    """Get all data from a specific table."""
    # Prevent SQL injection by checking if the table name is valid
    tables_query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = db.exec(tables_query).all()
    if (table_name,) not in tables:
        raise HTTPException(status_code=404, detail="Table not found")

    query = text(f"SELECT * FROM {table_name}")
    result = db.exec(query)
    columns = result.keys()
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]