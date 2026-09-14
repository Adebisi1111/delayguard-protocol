import pytest
import json
from unittest.mock import MagicMock, patch

# Mock genlayer
import sys
sys.modules['genlayer'] = MagicMock()

from contracts.delayguard_protocol import DelayGuardProtocol


class TestDelayGuardProtocol:
    """Test suite for DelayGuard Protocol."""

    def setup_method(self):
        self.contract = DelayGuardProtocol()
        self.contract.next_policy_id = 0
        self.contract.policies = {}

    def test_purchase_policy_locks_funds(self):
        """Test purchasing a policy with funds."""
        with patch('contracts.delayguard_protocol.gl') as mock_gl:
            mock_gl.message.value = 1000000000000000000  # 1 GEN
            mock_gl.message.sender_address = MagicMock()
            mock_gl.message.sender_address.__str__ = lambda self: "0xDepositor"
            
            policy_id = self.contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")
        
        assert policy_id == 0
        assert self.contract.policies[0].amount == 1000000000000000000
        assert self.contract.policies[0].status == "RESEARCHING"

    def test_purchase_policy_without_funds_rejected(self):
        """Test that purchasing without funds is rejected."""
        with patch('contracts.delayguard_protocol.gl') as mock_gl:
            mock_gl.message.value = 0
            
            with pytest.raises(Exception, match="Policy must be funded with GEN"):
                self.contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")

    def test_evaluate_delayed_flight_payout(self):
        """Test that delayed flight triggers payout to claimant."""
        with patch('contracts.delayguard_protocol.gl') as mock_gl:
            # Setup policy
            mock_gl.message.value = 1000000000000000000
            mock_gl.message.sender_address = MagicMock()
            mock_gl.message.sender_address.__str__ = lambda self: "0xDepositor"
            mock_gl.vm.run_nondet_unsafe.return_value = json.dumps({
                "flight_status": "DELAYED",
                "delay_minutes": 75
            })
            
            policy_id = self.contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")
            
            # Evaluate policy
            result = self.contract.evaluatePolicy(policy_id)
        
        assert result == "DELAYED"
        assert self.contract.policies[policy_id].verdict == "DELAYED"
        assert self.contract.policies[policy_id].delay_minutes == 75
        assert self.contract.policies[policy_id].status == "RESOLVED"

    def test_evaluate_on_time_flight_returns_funds(self):
        """Test that on-time flight returns funds to depositor."""
        with patch('contracts.delayguard_protocol.gl') as mock_gl:
            mock_gl.message.value = 1000000000000000000
            mock_gl.message.sender_address = MagicMock()
            mock_gl.message.sender_address.__str__ = lambda self: "0xDepositor"
            mock_gl.vm.run_nondet_unsafe.return_value = json.dumps({
                "flight_status": "ON_TIME",
                "delay_minutes": 0
            })
            
            policy_id = self.contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")
            result = self.contract.evaluatePolicy(policy_id)
        
        assert result == "ON_TIME"
        assert self.contract.policies[policy_id].verdict == "ON_TIME"
        assert self.contract.policies[policy_id].status == "RESOLVED"

    def test_get_policy(self):
        """Test retrieving policy details."""
        self.contract.policies[0] = MagicMock()
        self.contract.policies[0].flight_number = "BA173"
        self.contract.policies[0].flight_date = "2026-09-15"
        self.contract.policies[0].depositor = "0xDepositor"
        self.contract.policies[0].claimant = "0xClaimant"
        self.contract.policies[0].amount = 1000000000000000000
        self.contract.policies[0].status = "RESOLVED"
        self.contract.policies[0].verdict = "DELAYED"
        self.contract.policies[0].delay_minutes = 75
        self.contract.policies[0].created_at = 1710000000
        
        result = self.contract.getPolicy(0)
        data = json.loads(result)
        
        assert data["exists"] is True
        assert data["flight_number"] == "BA173"
        assert data["verdict"] == "DELAYED"

    def test_get_policy_not_found(self):
        """Test retrieving non-existent policy."""
        result = self.contract.getPolicy(999)
        data = json.loads(result)
        assert data["exists"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
