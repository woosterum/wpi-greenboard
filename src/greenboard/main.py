import streamlit as st
import sqlalchemy

import os
DATABASE_URL = os.getenv("DATABASE_URL")

engine = sqlalchemy.create_engine(DATABASE_URL)

st.title("WPI Greenboard")

with engine.connect() as conn:
    result = conn.execute(sqlalchemy.text("SELECT now()")).fetchone()
    st.write("Database time:", result[0])

    # Get all the tables in the database
    tables = conn.execute(sqlalchemy.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)).fetchall()

    st.write("Tables in the database:")
    for table in tables:
        st.write("-", table[0])