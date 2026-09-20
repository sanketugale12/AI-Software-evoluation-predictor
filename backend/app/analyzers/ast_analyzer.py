import os
from typing import List, Dict, Any, Optional
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
from ..schemas.symbols import SymbolRecord, SymbolType, SymbolRange

class MultiLanguageParser:
    def __init__(self):
        self.parsers = {
            ".py": (Parser(), Language(tspython.language())),
            ".js": (Parser(), Language(tsjavascript.language())),
            ".ts": (Parser(), Language(tstypescript.language_typescript())),
            ".tsx": (Parser(), Language(tstypescript.language_tsx())),
        }
        # Initialize parsers with their respective languages
        for ext, (parser, lang) in self.parsers.items():
            parser.set_language(lang)

    def parse_file(self, file_path: str) -> List[SymbolRecord]:
        ext = os.path.splitext(file_path)[1]
        if ext not in self.parsers:
            return []

        parser, _ = self.parsers[ext]

        with open(file_path, "rb") as f:
            tree = parser.parse(f.read())

        symbols = []
        root_node = tree.root_node

        # The file itself is a symbol
        file_id = f"{file_path}:FILE"
        file_symbol = SymbolRecord(
            id=file_id,
            name=os.path.basename(file_path),
            type=SymbolType.FILE,
            range=SymbolRange(
                start_line=0, start_column=0,
                end_line=root_node.end_point[0], end_column=root_node.end_point[1]
            )
        )
        symbols.append(file_symbol)

        self._extract_symbols(root_node, file_id, symbols, file_path)
        return symbols

    def _extract_symbols(self, node, parent_id: str, symbols: List[SymbolRecord], file_path: str):
        # This is a simplified visitor. In a full implementation,
        # we would have specific queries for each language.

        # Example for Python/JS basic function and class detection
        # Note: Real Tree-sitter implementation usually uses 'queries' for efficiency

        # Check if node is a function or class (generalized approach for demo)
        node_type = node.type
        if node_type in ("function_definition", "function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf8")
                sym_id = f"{file_path}:{name}"
                symbols.append(SymbolRecord(
                    id=sym_id,
                    name=name,
                    type=SymbolType.FUNCTION,
                    range=SymbolRange(
                        start_line=node.start_point[0], start_column=node.start_point[1],
                        end_line=node.end_point[0], end_column=node.end_point[1]
                    ),
                    parent_id=parent_id
                ))
                # Recurse into the function body
                for child in node.children:
                    self._extract_symbols(child, sym_id, symbols, file_path)
                return # Avoid double processing in the loop below

        elif node_type in ("class_definition", "class_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf8")
                sym_id = f"{file_path}:{name}"
                symbols.append(SymbolRecord(
                    id=sym_id,
                    name=name,
                    type=SymbolType.CLASS,
                    range=SymbolRange(
                        start_line=node.start_point[0], start_column=node.start_point[1],
                        end_line=node.end_point[0], end_column=node.end_point[1]
                    ),
                    parent_id=parent_id
                ))
                for child in node.children:
                    self._extract_symbols(child, sym_id, symbols, file_path)
                return

        for child in node.children:
            self._extract_symbols(child, parent_id, symbols, file_path)

def analyze_ast(file_path: str) -> List[SymbolRecord]:
    parser = MultiLanguageParser()
    return parser.parse_file(file_path)
