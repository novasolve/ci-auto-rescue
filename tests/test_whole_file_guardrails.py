# tests/test_whole_file_guardrails.py
from src.nova.agent.llm_agent_enhanced import EnhancedLLMAgent
from pathlib import Path

def test_extract_and_validate_blocks(tmp_path: Path):
    agent = EnhancedLLMAgent(tmp_path)
    src = {"src/calculator.py": '"""Doc"""\n\ndef factorial(n):\n    return 1\n'}
    failing = [{"name":"test_factorial","short_traceback":"factorial"}]
    text = "FILE: src/calculator.py\n```python\n\"\"\"Doc\"\"\"\n\ndef factorial(n):\n    return 1\n```\n"
    files = agent._extract_full_files(text)
    assert "src/calculator.py" in files
    assert agent._validate_full_file("src/calculator.py", files["src/calculator.py"], src, failing)
