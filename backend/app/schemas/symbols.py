from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SymbolType(str, Enum):
    FILE = "FILE"
    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    VARIABLE = "VARIABLE"
    IMPORT = "IMPORT"

class SymbolRange(BaseModel):
    start_line: int
    start_column: int
    end_line: int
    end_column: int

class SymbolRecord(BaseModel):
    id: str = Field(..., description="Unique identifier, e.g., 'path/to/file.py:ClassName'")
    name: str = Field(..., description="The name of the symbol")
    type: SymbolType
    range: SymbolRange
    parent_id: Optional[str] = Field(None, description="ID of the containing symbol")
    dependencies: List[str] = Field(default_factory=list, description="IDs of symbols this symbol depends on")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Language-specific additional data")
