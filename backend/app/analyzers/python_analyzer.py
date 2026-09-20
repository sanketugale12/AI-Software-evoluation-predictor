from tree_sitter import Language, Parser
import tree_sitter_python as tspython

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


def analyze_python_code(source_code: str):
    """
    Analyzes Python source code using tree-sitter to extract
    function and class definitions.
    """
    tree = parser.parse(source_code.encode("utf-8"))

    functions = []
    classes = []

    def walk(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                functions.append({
                    "name": source_code[
                        name_node.start_byte:name_node.end_byte
                    ],
                    "line": node.start_point[0] + 1,
                })

        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                classes.append({
                    "name": source_code[
                        name_node.start_byte:name_node.end_byte
                    ],
                    "line": node.start_point[0] + 1,
                })

        for child in node.children:
            walk(child)

    walk(tree.root_node)

    return {
        "functions": functions,
        "classes": classes,
    }
