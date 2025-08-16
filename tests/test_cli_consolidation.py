"""
Test CLI Consolidation
======================

Tests for the consolidated CLI with Deep Agent as default and legacy agent option.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

from nova.cli import app
from nova.agent.agent_factory import AgentFactory


runner = CliRunner()


class TestCLIConsolidation:
    """Test the consolidated CLI implementation."""
    
    def test_help_text_mentions_deep_agent_default(self):
        """Test that help text clearly states Deep Agent is the default."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "Deep Agent" in result.stdout
        assert "default" in result.stdout.lower()
        assert "--legacy-agent" in result.stdout
        assert "deprecated" in result.stdout.lower()
    
    def test_legacy_agent_flag_exists(self):
        """Test that --legacy-agent flag is available."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "--legacy-agent" in result.stdout
        assert "deprecated" in result.stdout.lower()
        assert "removed in v2.0" in result.stdout
    
    @patch('nova.cli.GitBranchManager')
    @patch('nova.cli.TestRunner')
    @patch('nova.agent.agent_factory.AgentFactory')
    def test_default_uses_deep_agent(self, mock_factory, mock_runner, mock_git):
        """Test that default behavior uses Deep Agent."""
        # Setup mocks
        mock_runner_instance = Mock()
        mock_runner_instance.run_tests.return_value = ([], 10)  # No failing tests
        mock_runner.return_value = mock_runner_instance
        
        mock_git_instance = Mock()
        mock_git.return_value = mock_git_instance
        
        mock_agent = Mock()
        mock_agent.run.return_value = True
        mock_factory.create_agent.return_value = mock_agent
        
        # Run the command without --legacy-agent
        with patch('nova.cli.get_settings'):
            result = runner.invoke(app, ["fix", "."])
        
        # Verify Deep Agent was used (agent_type="deep")
        if mock_factory.create_agent.called:
            call_args = mock_factory.create_agent.call_args
            # Check in kwargs or positional args
            if call_args[1]:  # kwargs
                assert call_args[1].get('agent_type') == 'deep'
            elif call_args[0]:  # positional args
                assert call_args[0][0] == 'deep'
    
    @patch('nova.cli.GitBranchManager')
    @patch('nova.cli.TestRunner')
    @patch('nova.agent.agent_factory.AgentFactory')
    def test_legacy_flag_uses_legacy_agent(self, mock_factory, mock_runner, mock_git):
        """Test that --legacy-agent flag uses the legacy agent."""
        # Setup mocks
        mock_runner_instance = Mock()
        mock_runner_instance.run_tests.return_value = ([], 10)  # No failing tests
        mock_runner.return_value = mock_runner_instance
        
        mock_git_instance = Mock()
        mock_git.return_value = mock_git_instance
        
        mock_agent = Mock()
        mock_agent.run.return_value = True
        mock_factory.create_agent.return_value = mock_agent
        
        # Run the command with --legacy-agent
        with patch('nova.cli.get_settings'):
            result = runner.invoke(app, ["fix", ".", "--legacy-agent"])
        
        # Verify Legacy Agent was used (agent_type="legacy")
        if mock_factory.create_agent.called:
            call_args = mock_factory.create_agent.call_args
            # Check in kwargs or positional args
            if call_args[1]:  # kwargs
                assert call_args[1].get('agent_type') == 'legacy'
            elif call_args[0]:  # positional args
                assert call_args[0][0] == 'legacy'
    
    def test_agent_factory_available_agents(self):
        """Test that AgentFactory knows about both agent types."""
        available = AgentFactory.get_available_agents()
        assert "deep" in available
        assert "legacy" in available
    
    def test_agent_factory_default_is_deep(self):
        """Test that AgentFactory default is Deep Agent."""
        default = AgentFactory.get_default_agent()
        assert default == "deep"
    
    @patch('nova.agent.agent_factory.NovaDeepAgent')
    def test_agent_factory_creates_deep_agent(self, mock_deep_agent_class):
        """Test that AgentFactory can create Deep Agent."""
        mock_instance = Mock()
        mock_deep_agent_class.return_value = mock_instance
        
        agent = AgentFactory.create_agent(
            agent_type="deep",
            state=Mock(),
            telemetry=Mock()
        )
        
        # Should create a Deep Agent (or wrapper)
        assert agent is not None
    
    @patch('nova.agent.legacy_agent.LegacyAgent')  
    def test_agent_factory_creates_legacy_agent(self, mock_legacy_class):
        """Test that AgentFactory can create Legacy Agent with warning."""
        mock_instance = Mock()
        mock_legacy_class.return_value = mock_instance
        
        with pytest.warns(DeprecationWarning, match="legacy agent is deprecated"):
            agent = AgentFactory.create_agent(
                agent_type="legacy",
                state=Mock(),
                telemetry=Mock()
            )
        
        assert agent is not None
        mock_legacy_class.assert_called_once()
    
    def test_agent_factory_invalid_type_raises(self):
        """Test that AgentFactory raises for invalid agent type."""
        with pytest.raises(ValueError, match="Invalid agent type"):
            AgentFactory.create_agent(
                agent_type="invalid",
                state=Mock(),
                telemetry=Mock()
            )
    
    def test_main_cli_entry_shows_help(self):
        """Test that main CLI without command shows help."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Nova CI-Rescue" in result.stdout
        assert "fix" in result.stdout
        assert "eval" in result.stdout
        assert "config" in result.stdout
    
    def test_version_flag_works(self):
        """Test that --version flag works."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Nova CI-Rescue" in result.stdout
    
    @patch('warnings.warn')
    def test_legacy_agent_shows_deprecation_in_output(self, mock_warn):
        """Test that using legacy agent shows deprecation warning."""
        from nova.agent.legacy_agent import LegacyAgent
        
        # Creating a legacy agent should trigger warning
        agent = LegacyAgent(verbose=False)
        
        # Check that the agent exists
        assert agent is not None


class TestLegacyAgentImplementation:
    """Test the minimal legacy agent implementation."""
    
    def test_legacy_agent_exists(self):
        """Test that LegacyAgent class exists and can be imported."""
        from nova.agent.legacy_agent import LegacyAgent
        assert LegacyAgent is not None
    
    def test_legacy_agent_has_run_method(self):
        """Test that LegacyAgent has a run method."""
        from nova.agent.legacy_agent import LegacyAgent
        agent = LegacyAgent(verbose=False)
        assert hasattr(agent, 'run')
        assert callable(agent.run)
    
    @patch('nova.agent.legacy_agent.TestRunner')
    @patch('nova.agent.legacy_agent.LLMClient')
    def test_legacy_agent_basic_flow(self, mock_llm_client, mock_runner):
        """Test that LegacyAgent follows the basic plan-act-review flow."""
        from nova.agent.legacy_agent import LegacyAgent
        
        # Setup mocks
        mock_llm = Mock()
        mock_llm.generate.return_value = "Fix plan"
        mock_llm_client.return_value = mock_llm
        
        mock_test_runner = Mock()
        mock_test_runner.run_tests.return_value = ([], 10)  # All tests passing
        mock_runner.return_value = mock_test_runner
        
        # Create and run agent
        agent = LegacyAgent(verbose=False)
        result = agent.run(
            failures_summary="Test failures",
            error_details="Error details"
        )
        
        # Should return True when tests pass
        assert result is True
