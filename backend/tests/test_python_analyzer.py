from backend.app.analyzers.python_analyzer import analyze_python_code


def test_python_analysis():
    code = """
class User:
    def login(self):
        pass

def calculate():
    return 42
"""

    result = analyze_python_code(code)

    assert any(
        item["name"] == "User"
        for item in result["classes"]
    )

    assert any(
        item["name"] == "calculate"
        for item in result["functions"]
    )

    # Also verify that the method 'login' inside 'User' was caught
    assert any(
        item["name"] == "login"
        for item in result["functions"]
    )
