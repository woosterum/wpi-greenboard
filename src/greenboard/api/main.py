from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import get_db
import sqlalchemy

app = FastAPI(title="WPI Greenboard API")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    result = db.execute(sqlalchemy.text("SELECT now()")).fetchone()
    return {"status": "healthy", "database_time": result[0]}

@app.get("/tables")
async def get_tables(db: Session = Depends(get_db)):
    tables = db.execute(sqlalchemy.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)).fetchall()
    return {"tables": [table[0] for table in tables]}