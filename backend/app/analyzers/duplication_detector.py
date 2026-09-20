"""Code duplication detection analyzer."""
import os
import hashlib
from typing import Any
from collections import defaultdict


ANALYZER_VERSION = "1.0.0"

# Minimum lines for a block to be considered for duplication
MIN_DUPLICATE_LINES = 5
# Minimum token count after normalization
MIN_TOKEN_COUNT = 10


def detect_duplicates(files: dict[str, str]) -> dict[str, Any]:
    """
    Detect code duplication across files using normalized hashing.
    Groups similar code blocks and reports them as duplicates.
    """
    # Extract code blocks from each file
    blocks_by_file = {}
    for file_path, source_code in files.items():
        blocks = _extract_code_blocks(source_code, file_path)
        blocks_by_file[file_path] = blocks

    # Normalize and hash each block
    block_hashes = defaultdict(list)
    for file_path, blocks in blocks_by_file.items():
        for block in blocks:
            normalized = _normalize_block(block["content"])
            if len(normalized.split()) < MIN_TOKEN_COUNT:
                continue
            block_hash = hashlib.md5(normalized.encode()).hexdigest()
            block_hashes[block_hash].append({
                "file": file_path,
                "start_line": block["start_line"],
                "end_line": block["end_line"],
                "content_hash": block_hash,
                "normalized": normalized,
            })

    # Find duplicates (hashes with more than one occurrence)
    duplicates = []
    seen_pairs = set()

    for block_hash, occurrences in block_hashes.items():
        if len(occurrences) < 2:
            continue

        # Group occurrences into duplicate clusters
        for i in range(len(occurrences)):
            for j in range(i + 1, len(occurrences)):
                pair_key = tuple(sorted([
                    (occurrences[i]["file"], occurrences[i]["start_line"]),
                    (occurrences[j]["file"], occurrences[j]["start_line"]),
                ]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                duplicates.append({
                    "id": f"dup-{block_hash[:8]}-{i}-{j}",
                    "rule_id": "code-duplication",
                    "category": "duplication",
                    "subcategory": "duplicate_code",
                    "severity": "medium",
                    "confidence": 0.8,
                    "title": f"Duplicate code block: {occurrences[i]['file']} and {occurrences[j]['file']}",
                    "description": (
                        f"Lines {occurrences[i]['start_line']}-{occurrences[i]['end_line']} in "
                        f"{occurrences[i]['file']} are duplicated in "
                        f"{occurrences[j]['file']} lines {occurrences[j]['start_line']}-{occurrences[j]['end_line']}. "
                        f"Consider extracting common code into a shared function or module."
                    ),
                    "file": occurrences[i]["file"],
                    "line": occurrences[i]["start_line"],
                    "recommendation": (
                        "Extract the duplicated code into a shared function, class, or module. "
                        "Use the DRY (Don't Repeat Yourself) principle."
                    ),
                    "analyzer_version": ANALYZER_VERSION,
                    "cwe": "CWE-1066",
                    "owasp": None,
                    "metadata": {
                        "duplicate_file": occurrences[j]["file"],
                        "duplicate_line": occurrences[j]["start_line"],
                        "block_size_lines": occurrences[i]["end_line"] - occurrences[i]["start_line"] + 1,
                        "source": "duplication-detector",
                    },
                })

    # Calculate duplication ratio
    total_lines = sum(
        len(source.split("\n"))
        for source in files.values()
    )
    duplicated_lines = sum(
        (d["metadata"]["block_size_lines"] * 2)  # Each duplicate appears at least twice
        for d in duplicates
    )
    duplication_ratio = duplicated_lines / total_lines if total_lines > 0 else 0

    return {
        "duplicates": duplicates,
        "total_duplicates": len(duplicates),
        "duplicated_lines": duplicated_lines,
        "total_lines": total_lines,
        "duplication_ratio": round(duplication_ratio, 4),
    }


def _extract_code_blocks(source_code: str, file_path: str) -> list[dict[str, Any]]:
    """Extract meaningful code blocks (functions, classes, or line groups)."""
    blocks = []
    lines = source_code.split("\n")

    ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""

    if ext == "py":
        # Extract Python functions and classes
        try:
            import ast
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    block_lines = lines[start_line - 1:end_line]
                    content = "\n".join(block_lines)
                    blocks.append({
                        "start_line": start_line,
                        "end_line": end_line,
                        "content": content,
                        "type": type(node).__name__,
                    })
        except SyntaxError:
            pass

    # Also extract generic blocks of consecutive non-empty lines
    current_block = []
    current_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "//", "/*", "*", "*/")):
            if not current_block:
                current_start = i + 1
            current_block.append(line)
        else:
            if len(current_block) >= MIN_DUPLICATE_LINES:
                blocks.append({
                    "start_line": current_start,
                    "end_line": current_start + len(current_block) - 1,
                    "content": "\n".join(current_block),
                    "type": "block",
                })
            current_block = []

    if len(current_block) >= MIN_DUPLICATE_LINES:
        blocks.append({
            "start_line": current_start,
            "end_line": current_start + len(current_block) - 1,
            "content": "\n".join(current_block),
            "type": "block",
        })

    return blocks


def _normalize_block(content: str) -> str:
    """Normalize a code block for comparison by removing whitespace and comments."""
    import re
    # Remove comments
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    # Remove string literals (keep them but normalize)
    content = re.sub(r'["\']([^"\']*)["\']', '"STRING"', content)
    return content.strip()