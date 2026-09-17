"""Direct mode tests for DelayGuard Protocol using gltest."""
import pytest
import json


def _purchase_and_evaluate(direct_vm, contract, flight_status, delay_minutes):
    """Helper to purchase policy and evaluate with mocked LLM."""
    direct_vm.value = 1000000000000000000  # 1 GEN
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")
    direct_vm.mock_llm(r".*", f'{{"flight_status": "{flight_status}", "delay_minutes": {delay_minutes}}}')
    contract.evaluatePolicy(policy_id)
    return policy_id


def test_purchase_policy_funded(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")
    assert policy_id == 0
    result = json.loads(contract.getPolicy(policy_id))
    assert result["status"] == "RESEARCHING"
    assert result["amount"] == 1000000000000000000


def test_purchase_policy_no_funds_rejected(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 0
    with direct_vm.expect_revert("Policy must be funded with GEN"):
        contract.purchasePolicy("BA173", "2026-09-15", "0xClaimant")


def test_evaluate_delayed_payout(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    _purchase_and_evaluate(direct_vm, contract, "DELAYED", 75)
    transfers = json.loads(contract.getEmittedTransfers())
    assert any(json.loads(v).get("type") == "payout" for v in transfers.values())


def test_evaluate_on_time_refund(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    _purchase_and_evaluate(direct_vm, contract, "ON_TIME", 0)
    transfers = json.loads(contract.getEmittedTransfers())
    assert any(json.loads(v).get("type") == "refund" for v in transfers.values())


def test_get_policy_not_found(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    result = json.loads(contract.getPolicy(999))
    assert result["exists"] is False


def test_transfer_count_increments(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    
    count = json.loads(contract.getTransferCount())
    assert count["count"] == 0
    
    _purchase_and_evaluate(direct_vm, contract, "DELAYED", 75)
    count = json.loads(contract.getTransferCount())
    assert count["count"] == 1
    
    _purchase_and_evaluate(direct_vm, contract, "ON_TIME", 0)
    count = json.loads(contract.getTransferCount())
    assert count["count"] == 2
