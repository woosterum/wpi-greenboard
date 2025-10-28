from fastapi import FastAPI
from .routes import database
from .routes import packages

app = FastAPI(
    title="WPI Greenboard API",
    description="Carbon Emissions Tracker for WPI Students",
    version="0.1.0"
)

# Include all route modules
app.include_router(database.router)
app.include_router(packages.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to WPI Greenboard API",
        "docs": "/docs"
    }
