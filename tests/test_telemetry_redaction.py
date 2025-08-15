"""
Test telemetry secret redaction functionality
"""
import json
from pathlib import Path
import pytest
import tempfile
import os


def test_telemetry_redacts_secrets(tmp_path):
    """Test that sensitive API keys are redacted in telemetry logs"""
    from nova.telemetry.logger import JSONLLogger, redact_secrets, NovaSettings
    
    # Prepare dummy settings with fake secrets
    fake_openai_key = "sk-SECRET123OPENAI456"
    fake_anthropic_key = "ant-SECRET789ANTHROPIC"
    fake_openswe_key = "openswe-SECRETKEY123"
    
    settings = NovaSettings(
        openai_api_key=fake_openai_key, 
        anthropic_api_key=fake_anthropic_key, 
        openswe_api_key=fake_openswe_key, 
        telemetry_dir=str(tmp_path)
    )
    
    logger = JSONLLogger(settings=settings, enabled=True)
    logger.start_run(".")  # Initialize telemetry logging
    
    # Log an event containing the secrets
    payload = {
        "msg": f"API key = {fake_openai_key}",
        "config": {
            "openai": fake_openai_key,
            "anthropic": fake_anthropic_key,
            "openswe": fake_openswe_key
        },
        "environment": {
            "OPENAI_API_KEY": fake_openai_key,
            "ANTHROPIC_API_KEY": fake_anthropic_key
        }
    }
    logger.log_event("test_event", payload)
    logger.end_run(success=True)
    
    # Read the trace log and confirm the secrets were redacted
    trace_file = tmp_path / logger.run_id / "trace.jsonl"
    assert trace_file.exists(), f"Trace file not found at {trace_file}"
    
    content = trace_file.read_text()
    
    # Assert that none of the secrets appear in the content
    assert fake_openai_key not in content, "OpenAI key not redacted"
    assert fake_anthropic_key not in content, "Anthropic key not redacted"
    assert fake_openswe_key not in content, "OpenSWE key not redacted"
    
    # Assert that redaction markers are present
    assert "[REDACTED]" in content, "No redaction markers found"
    
    # Parse and verify JSON structure is valid
    lines = content.strip().split('\n')
    for line in lines:
        event = json.loads(line)  # Should not raise if JSON is valid
        
        # Check that the event structure is preserved
        assert "timestamp" in event
        assert "event_type" in event


def test_redact_secrets_function():
    """Test the redact_secrets function directly"""
    from nova.telemetry.logger import redact_secrets
    
    # Define secrets to redact
    secrets = [
        "sk-proj-abcd1234efgh5678",
        "ant-01234567890",
        "openswe-test123",
        "ghp_1234567890abcdef",
        "sk-test123",
        "ghp_secret456",
        "sk-nested-secret789"
    ]
    
    # Test various secret patterns
    test_data = {
        "openai_key": "sk-proj-abcd1234efgh5678",
        "anthropic_key": "ant-01234567890",
        "openswe_key": "openswe-test123",
        "github_token": "ghp_1234567890abcdef",
        "mixed_text": "My key is sk-test123 and token is ghp_secret456",
        "nested": {
            "api_key": "sk-nested-secret789",
            "normal": "This is normal text"
        }
    }
    
    redacted = redact_secrets(test_data, secrets)
    
    # Verify secrets are redacted
    assert redacted["openai_key"] == "[REDACTED]"
    assert redacted["anthropic_key"] == "[REDACTED]"
    assert redacted["openswe_key"] == "[REDACTED]"
    assert redacted["github_token"] == "[REDACTED]"
    assert "[REDACTED]" in redacted["mixed_text"]
    assert "sk-test123" not in redacted["mixed_text"]
    assert "ghp_secret456" not in redacted["mixed_text"]
    
    # Verify nested structures are handled
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["normal"] == "This is normal text"


def test_telemetry_no_leaks_in_error_logs(tmp_path):
    """Test that secrets don't leak even in error scenarios"""
    from nova.telemetry.logger import JSONLLogger, NovaSettings
    
    fake_key = "sk-SUPERSECRET999"
    settings = NovaSettings(
        openai_api_key=fake_key,
        telemetry_dir=str(tmp_path)
    )
    
    logger = JSONLLogger(settings=settings, enabled=True)
    logger.start_run(".")
    
    # Simulate an error with the secret in the error message
    try:
        raise ValueError(f"Failed to authenticate with key: {fake_key}")
    except Exception as e:
        logger.log_event("error", {
            "error": str(e),
            "traceback": f"Traceback includes {fake_key}"
        })
    
    logger.end_run(success=False)
    
    # Check the logs
    trace_file = tmp_path / logger.run_id / "trace.jsonl"
    content = trace_file.read_text()
    
    # The secret should not appear anywhere
    assert fake_key not in content, "Secret leaked in error logs"
    assert "[REDACTED]" in content, "Redaction not applied to errors"


def test_environment_variable_redaction(tmp_path, monkeypatch):
    """Test that environment variables with secrets are redacted"""
    from nova.telemetry.logger import JSONLLogger, NovaSettings
    
    # Set environment variables with secrets
    secret_key = "sk-ENV-SECRET-KEY"
    monkeypatch.setenv("OPENAI_API_KEY", secret_key)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-ENV-KEY")
    
    settings = NovaSettings(telemetry_dir=str(tmp_path))
    logger = JSONLLogger(settings=settings, enabled=True)
    logger.start_run(".")
    
    # Log environment information
    logger.log_event("env_check", {
        "env": dict(os.environ),
        "path": os.environ.get("PATH", "")
    })
    
    logger.end_run(success=True)
    
    # Verify secrets are not in logs
    trace_file = tmp_path / logger.run_id / "trace.jsonl"
    content = trace_file.read_text()
    
    assert secret_key not in content, "Environment secret not redacted"
    assert "ant-ENV-KEY" not in content, "Anthropic env key not redacted"
