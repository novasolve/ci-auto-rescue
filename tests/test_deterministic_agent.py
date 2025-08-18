"""Tests for the deterministic Deep Agent implementation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from nova.agent.deep_agent import NovaDeepAgent
from nova.agent.state import AgentState
from nova.telemetry import TelemetryBase
from nova.git_utils import GitManager


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, settings=None):
        self.settings = settings
        self.call_count = 0
        self.responses = []
    
    def complete(self, system: str, user: str, max_tokens: int = 1000) -> str:
        """Return predefined responses."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return "No more responses configured"


@pytest.fixture
def mock_state(tmp_path):
    """Create a mock agent state."""
    state = AgentState(repo_path=tmp_path)
    state.failing_tests = [
        {"name": "test_divide", "error": "ZeroDivisionError"},
        {"name": "test_add", "error": "AssertionError"}
    ]
    state.total_failures = 2
    state.max_iterations = 2
    return state


@pytest.fixture
def mock_telemetry():
    """Create a mock telemetry instance."""
    telemetry = Mock(spec=TelemetryBase)
    telemetry.log_event = Mock()
    return telemetry


def test_deterministic_plan_phase(mock_state, mock_telemetry, tmp_path):
    """Test the planning phase generates a plan."""
    # Set up mock LLM responses
    plan_response = """
    Step 1: Fix divide function to handle zero division
    Step 2: Fix add function to return correct result
    Files to examine: src/math_ops.py
    """
    
    with patch('nova.agent.deep_agent.LLMClient') as MockLLMClientClass:
        mock_client = MockLLMClient()
        mock_client.responses = [plan_response]
        MockLLMClientClass.return_value = mock_client
        
        # Create agent
        agent = NovaDeepAgent(
            state=mock_state,
            telemetry=mock_telemetry,
            verbose=True
        )
        
        # Run should fail because no files exist yet
        with patch('nova.agent.unified_tools.open_file', return_value="ERROR: File not found"):
            with patch('nova.runner.TestRunner') as MockRunner:
                mock_runner = MockRunner.return_value
                mock_runner.run_tests.return_value = ([], "")
                
                result = agent.run(
                    failures_summary="test_divide | test_add",
                    error_details="ZeroDivisionError in test_divide"
                )
        
        # Verify plan was generated and stored
        assert mock_state.plan == plan_response
        assert mock_client.call_count >= 1
        mock_telemetry.log_event.assert_any_call("deep_agent_start", {
            "failing_tests": 2,
            "iteration": 0
        })


def test_deterministic_full_cycle(mock_state, mock_telemetry, tmp_path):
    """Test a full Plan-Edit-Apply-Test cycle."""
    # Create test files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    math_file = src_dir / "math_ops.py"
    math_file.write_text("""
def divide(a, b):
    return a / b

def add(a, b):
    return a + b - 1  # Bug: subtracting 1
""")
    
    # Mock responses
    plan_response = """
    Fix the divide function to handle zero division.
    Fix the add function to return correct sum without subtracting 1.
    Files: src/math_ops.py
    """
    
    fixed_code = """
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def add(a, b):
    return a + b
"""
    
    with patch('nova.agent.deep_agent.LLMClient') as MockLLMClientClass:
        mock_client = MockLLMClient()
        mock_client.responses = [plan_response, fixed_code]
        MockLLMClientClass.return_value = mock_client
        
        # Mock tools
        with patch('nova.agent.unified_tools.ApplyPatchTool') as MockPatchTool:
            mock_patch_tool = MockPatchTool.return_value
            mock_patch_tool._run.return_value = "SUCCESS: Patch applied"
            
            with patch('nova.runner.TestRunner') as MockRunner:
                mock_runner = MockRunner.return_value
                # First run: still has failures, second run: all pass
                mock_runner.run_tests.side_effect = [
                    ([{"name": "test_add"}], "1 test failed"),  # After first fix
                    ([], "All tests pass")  # After second iteration
                ]
                
                agent = NovaDeepAgent(
                    state=mock_state,
                    telemetry=mock_telemetry,
                    verbose=True
                )
                
                result = agent.run(
                    failures_summary="test_divide | test_add",
                    error_details="File 'src/math_ops.py', line 2"
                )
                
                # Should succeed after fixing
                assert result is True
                assert mock_state.final_status == "success"
                assert len(mock_state.patches_applied) > 0
                

def test_deterministic_regression_rollback(mock_state, mock_telemetry, tmp_path):
    """Test that regressions cause rollback."""
    # Set up file
    src_file = tmp_path / "src.py"
    src_file.write_text("def foo(): return 1")
    
    with patch('nova.agent.deep_agent.LLMClient') as MockLLMClientClass:
        mock_client = MockLLMClient()
        mock_client.responses = [
            "Fix foo to return 2",
            "def foo(): return 2\ndef bar(): raise Exception()"  # Introduces new failure
        ]
        MockLLMClientClass.return_value = mock_client
        
        with patch('nova.agent.unified_tools.ApplyPatchTool') as MockPatchTool:
            mock_patch_tool = MockPatchTool.return_value
            mock_patch_tool._run.return_value = "SUCCESS: Patch applied"
            
            with patch('nova.runner.TestRunner') as MockRunner:
                mock_runner = MockRunner.return_value
                # After patch: new test fails (regression)
                mock_runner.run_tests.return_value = (
                    [{"name": "test_bar"}],  # New failing test!
                    "1 test failed"
                )
                
                with patch.object(GitManager, 'cleanup') as mock_cleanup:
                    agent = NovaDeepAgent(
                        state=mock_state,
                        telemetry=mock_telemetry,
                        git_manager=Mock()
                    )
                    
                    result = agent.run(
                        failures_summary="test_foo",
                        error_details="foo returns wrong value"
                    )
                    
                    # Should fail and rollback
                    assert result is False
                    assert mock_state.final_status == "patch_error"
                    agent.git_manager.cleanup.assert_called_with(success=False)


def test_deterministic_critic_rejection(mock_state, mock_telemetry):
    """Test handling of critic rejection."""
    with patch('nova.agent.deep_agent.LLMClient') as MockLLMClientClass:
        mock_client = MockLLMClient()
        mock_client.responses = ["Fix plan", "Fixed code"]
        MockLLMClientClass.return_value = mock_client
        
        with patch('nova.agent.unified_tools.open_file', return_value="original code"):
            with patch('nova.agent.unified_tools.ApplyPatchTool') as MockPatchTool:
                mock_patch_tool = MockPatchTool.return_value
                mock_patch_tool._run.return_value = "FAILED: Patch rejected by critic - Too many changes"
                
                agent = NovaDeepAgent(
                    state=mock_state,
                    telemetry=mock_telemetry
                )
                
                result = agent.run()
                
                # Should fail with patch_rejected status
                assert result is False
                assert mock_state.final_status == "patch_rejected"
                assert mock_state.critic_feedback == "Too many changes"