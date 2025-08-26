# tests/test_runner_discovery.py
from src.nova.runner.test_runner import TestRunner, FailingTest
from pathlib import Path
import json

def test_parse_json_report_handles_call_setup_teardown(tmp_path: Path):
    jr = tmp_path/"report.json"
    jr.write_text(json.dumps({"tests":[
        {"nodeid":"tests/test_x.py::test_a","outcome":"failed",
         "setup":{"longrepr":""},"call":{"longrepr":"tests/test_x.py:10: E assert 2==3","outcome":"failed"}}
    ]}))
    tr = TestRunner(tmp_path)
    out = tr._parse_json_report(str(jr))
    assert len(out)==1 and isinstance(out[0], FailingTest)
    assert out[0].file == "tests/test_x.py"
    assert out[0].line == 10
