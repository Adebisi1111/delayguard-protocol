"""Direct mode tests for DelayGuard Protocol using gltest."""
import pytest
import json


def _addr_hex(addr_bytes):
    """Convert bytes address to hex string."""
    if isinstance(addr_bytes, bytes):
        return "0x" + addr_bytes.hex()
    return str(addr_bytes)


def test_purchase_policy_funded(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))
    result = json.loads(contract.getPolicy(policy_id))
    assert result["status"] == "RESEARCHING"
    assert result["amount"] == 1000000000000000000


def test_purchase_policy_no_funds_rejected(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 0
    with direct_vm.expect_revert("Policy must be funded with GEN"):
        contract.purchasePolicy("BA173", "2026-09-15", "0x0000000000000000000000000000000000000042")


def test_evaluate_delayed_payout(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    result = contract.evaluatePolicy(policy_id, "DELAYED", 75)
    assert result == "DELAYED"

    transfers = json.loads(contract.getEmittedTransfers())
    payout_found = False
    for key, val in transfers.items():
        t = json.loads(val) if isinstance(val, str) else val
        if t.get("type") == "payout" and int(t.get("amount", 0)) == 1000000000000000000:
            payout_found = True
            break
    assert payout_found, f"No payout recorded: {transfers}"


def test_evaluate_on_time_refund(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    result = contract.evaluatePolicy(policy_id, "ON_TIME", 0)
    assert result == "ON_TIME"

    transfers = json.loads(contract.getEmittedTransfers())
    refund_found = False
    for key, val in transfers.items():
        t = json.loads(val) if isinstance(val, str) else val
        if t.get("type") == "refund" and int(t.get("amount", 0)) == 1000000000000000000:
            refund_found = True
            break
    assert refund_found, f"No refund recorded: {transfers}"


def test_get_policy_not_found(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    result = json.loads(contract.getPolicy(999))
    assert result["exists"] is False


def test_transfer_count_increments(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice

    count = json.loads(contract.getTransferCount())
    assert count["count"] == 0

    # Policy 1: DELAYED
    direct_vm.value = 1000000000000000000
    contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))
    contract.evaluatePolicy(0, "DELAYED", 75)

    count = json.loads(contract.getTransferCount())
    assert count["count"] == 1

    # Policy 2: ON_TIME
    direct_vm.value = 500000000000000000
    contract.purchasePolicy("UA999", "2026-09-16", _addr_hex(direct_bob))
    contract.evaluatePolicy(1, "ON_TIME", 0)

    count = json.loads(contract.getTransferCount())
    assert count["count"] == 2
