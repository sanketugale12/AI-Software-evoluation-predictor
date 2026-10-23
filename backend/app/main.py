from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import repository, graph, analysis, auth, architecture, analysis_comparison, intelligence
from .database import engine, Base
from .models import User, GitHubToken, Repository, AnalysisJob, RepositorySnapshot



app = FastAPI(title="ASEP Backend")

# Create database tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(repository.router)
app.include_router(graph.router)
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(architecture.router, prefix="/api/architecture", tags=["Architecture"])
app.include_router(analysis_comparison.router, prefix="/api/analysis", tags=["Comparison"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Intelligence"])

@app.get("/")
def home():
    return {"message": "ASEP backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}