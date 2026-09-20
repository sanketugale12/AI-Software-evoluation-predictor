from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from ..schemas.symbols import SymbolRecord
from ..analyzers.ast_analyzer import analyze_ast
from ..analyzers.arch_intelligence import analyze_architecture
from ..services.repository_service import get_repository_files # Assuming this exists based on project structure

router = APIRouter(prefix="/architecture", tags=["architecture"])

@router.post("/metrics")
async def get_architecture_metrics(repo_id: str):
    """
    Calculates high-level architecture metrics for a repository.
    """
    try:
        # Fetch all files in the repository
        files = get_repository_files(repo_id) # Dict[str, str]

        all_symbols = []
        for file_path in files:
            symbols = analyze_ast(file_path)
            all_symbols.extend(symbols)

        metrics = analyze_architecture(all_symbols)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Architecture analysis failed: {str(e)}")

@router.post("/symbols")
async def get_symbol_records(repo_id: str, file_path: Optional[str] = None):
    """
    Returns normalized symbol records for a specific file or the entire project.
    """
    try:
        files = get_repository_files(repo_id)

        if file_path:
            if file_path not in files:
                raise HTTPException(status_code=404, detail="File not found")
            return analyze_ast(file_path)

        all_symbols = []
        for path in files:
            all_symbols.extend(analyze_ast(path))
        return all_symbols

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Symbol extraction failed: {str(e)}")
