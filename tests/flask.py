"""
HTTP testing utilities.

For HTTP endpoint testing, consider using pytest-httpx:
https://pypi.org/project/pytest-httpx/

Example:
    def test_endpoint(httpx_mock):
        httpx_mock.add_response(method="GET", url="https://api.example.com/data", json={"key": "value"})
        # Your test code here
"""
