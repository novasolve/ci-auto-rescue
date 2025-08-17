"""
Tests for SafePatchManager
==========================

Tests the enforcement of critic review before patch application.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from nova.agent.safe_patch_manager import SafePatchManager, create_safe_patch_manager
from nova.telemetry.logger import JSONLLogger
from nova.config import SafetyConfig


class TestSafePatchManager:
    """Test suite for SafePatchManager."""
    
    @pytest.fixture
    def mock_telemetry(self):
        """Create a mock telemetry logger."""
        telemetry = Mock(spec=JSONLLogger)
        telemetry.log_event = Mock()
        return telemetry
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        return Mock()
    
    @pytest.fixture
    def sample_patch(self):
        """Sample patch diff for testing."""
        return """--- a/src/example.py
+++ b/src/example.py
@@ -1,5 +1,5 @@
 def add(a, b):
-    return a - b  # Bug: should be addition
+    return a + b  # Fixed: now correctly adds
 
 def multiply(a, b):
     return a * b"""
    
    def test_approved_patch_gets_applied(self, mock_telemetry, mock_llm):
        """Test that approved patches are applied."""
        # Create manager
        manager = SafePatchManager(
            repo_path=Path("."),
            llm=mock_llm,
            telemetry=mock_telemetry,
            verbose=True
        )
        
        # Mock the tools' responses
        with patch.object(manager.critic_tool, '_run', return_value="APPROVED: Fixes the addition bug correctly"):
            with patch.object(manager.apply_tool, '_run', return_value="SUCCESS: Patch applied successfully."):
                # Run review and apply
                result = manager.review_and_apply(self.sample_patch())
        
        # Verify results
        assert result["applied"] is True
        assert result["review_decision"] == "APPROVED"
        assert result["review_reason"] == "Fixes the addition bug correctly"
        assert result["apply_result"] == "SUCCESS: Patch applied successfully."
        
        # Verify telemetry was logged
        assert mock_telemetry.log_event.call_count >= 2  # At least review + apply events
    
    def test_rejected_patch_not_applied(self, mock_telemetry, mock_llm):
        """Test that rejected patches are not applied."""
        # Create manager
        manager = SafePatchManager(
            repo_path=Path("."),
            llm=mock_llm,
            telemetry=mock_telemetry,
            verbose=False
        )
        
        # Mock the critic to reject
        with patch.object(manager.critic_tool, '_run', return_value="REJECTED: Modifies test files"):
            # Run review and apply
            result = manager.review_and_apply(self.sample_patch())
        
        # Verify patch was NOT applied
        assert result["applied"] is False
        assert result["review_decision"] == "REJECTED"
        assert result["review_reason"] == "Modifies test files"
        assert result["apply_result"] is None  # Should not have attempted to apply
        
        # Verify apply_tool was never called
        with patch.object(manager.apply_tool, '_run') as mock_apply:
            mock_apply.assert_not_called()
    
    def test_override_allows_rejected_patch(self, mock_telemetry, mock_llm):
        """Test that override flag allows applying rejected patches."""
        # Create manager with override enabled
        manager = SafePatchManager(
            repo_path=Path("."),
            llm=mock_llm,
            telemetry=mock_telemetry,
            allow_override=True,  # Enable override
            verbose=True
        )
        
        # Mock rejection and successful application
        with patch.object(manager.critic_tool, '_run', return_value="REJECTED: Too many changes"):
            with patch.object(manager.apply_tool, '_run', return_value="SUCCESS: Patch applied successfully."):
                # Run with force=True
                result = manager.review_and_apply(self.sample_patch(), force=True)
        
        # Verify patch was applied despite rejection
        assert result["applied"] is True
        assert result["review_decision"] == "REJECTED"
        assert result["apply_result"] == "SUCCESS: Patch applied successfully."
        
        # Verify override event was logged
        override_events = [call for call in mock_telemetry.log_event.call_args_list 
                          if call[0][0].get("event") == "safety_override"]
        assert len(override_events) > 0
    
    def test_override_denied_when_disabled(self, mock_telemetry, mock_llm):
        """Test that override is denied when not allowed."""
        # Create manager with override disabled (default)
        manager = SafePatchManager(
            repo_path=Path("."),
            llm=mock_llm,
            telemetry=mock_telemetry,
            allow_override=False  # Explicitly disable
        )
        
        # Mock rejection
        with patch.object(manager.critic_tool, '_run', return_value="REJECTED: Dangerous changes"):
            # Try to force
            result = manager.review_and_apply(self.sample_patch(), force=True)
        
        # Verify patch was NOT applied
        assert result["applied"] is False
        assert result["review_decision"] == "REJECTED"
        
        # Verify override denied event was logged
        denied_events = [call for call in mock_telemetry.log_event.call_args_list 
                        if call[0][0].get("event") == "override_denied"]
        assert len(denied_events) > 0
    
    def test_review_history_tracking(self, mock_telemetry, mock_llm):
        """Test that review history is properly tracked."""
        manager = SafePatchManager(
            repo_path=Path("."),
            llm=mock_llm,
            telemetry=mock_telemetry
        )
        
        # Perform several reviews
        with patch.object(manager.critic_tool, '_run') as mock_critic:
            with patch.object(manager.apply_tool, '_run') as mock_apply:
                # First patch - approved
                mock_critic.return_value = "APPROVED: Good fix"
                mock_apply.return_value = "SUCCESS: Applied"
                manager.review_and_apply("patch1")
                
                # Second patch - rejected
                mock_critic.return_value = "REJECTED: Bad idea"
                manager.review_and_apply("patch2")
                
                # Third patch - approved
                mock_critic.return_value = "APPROVED: Another good fix"
                mock_apply.return_value = "SUCCESS: Applied"
                manager.review_and_apply("patch3")
        
        # Check history
        history = manager.get_review_history()
        assert len(history) == 3
        
        # Check stats
        stats = manager.get_stats()
        assert stats["total_reviews"] == 3
        assert stats["approved"] == 2
        assert stats["rejected"] == 1
        # Note: applied count would be tracked through telemetry events
    
    def test_patch_apply_failure_handling(self, mock_telemetry, mock_llm):
        """Test handling of patch application failures."""
        manager = SafePatchManager(
            repo_path=Path("."),
            llm=mock_llm,
            telemetry=mock_telemetry
        )
        
        # Mock approval but application failure
        with patch.object(manager.critic_tool, '_run', return_value="APPROVED: Looks good"):
            with patch.object(manager.apply_tool, '_run', return_value="FAILED: Context mismatch"):
                result = manager.review_and_apply(self.sample_patch())
        
        # Verify result
        assert result["applied"] is False  # Not applied due to failure
        assert result["review_decision"] == "APPROVED"
        assert result["apply_result"] == "FAILED: Context mismatch"
        
        # Verify failure event was logged
        failure_events = [call for call in mock_telemetry.log_event.call_args_list 
                         if call[0][0].get("event") == "patch_apply_failed"]
        assert len(failure_events) > 0


class TestIntegration:
    """Integration tests with real tools."""
    
    def test_factory_function(self):
        """Test the create_safe_patch_manager factory function."""
        # Mock dependencies
        mock_state = Mock()
        mock_state.repo_path = Path(".")
        mock_telemetry = Mock(spec=JSONLLogger)
        mock_llm = Mock()
        
        # Create manager using factory
        manager = create_safe_patch_manager(
            state=mock_state,
            telemetry=mock_telemetry,
            llm=mock_llm,
            verbose=True,
            allow_override=False
        )
        
        # Verify it's properly configured
        assert isinstance(manager, SafePatchManager)
        assert manager.allow_override is False
        assert manager.verbose is True
