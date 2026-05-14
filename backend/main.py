from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import nodes, score

app = FastAPI(title="Tunnel Smart Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nodes.router)
app.include_router(score.router)

@app.get("/")
def root():
    return {
        "name": "Tunnel Smart Advisor API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    return {"status": "ok"}
