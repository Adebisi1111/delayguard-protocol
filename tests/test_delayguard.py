"""Direct mode tests for DelayGuard Protocol using gltest."""
import pytest
import json


def _addr_hex(addr_bytes):
    """Convert bytes address to hex string."""
    if isinstance(addr_bytes, bytes):
        return "0x" + addr_bytes.hex()
    return str(addr_bytes)


# === Basic Flow Tests ===

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


# === Edge Case Tests ===

def test_double_evaluate_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Cannot evaluate a policy that's already resolved."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    # First evaluation succeeds
    contract.evaluatePolicy(policy_id, "DELAYED", 75)

    # Second evaluation should fail
    with direct_vm.expect_revert("already resolved"):
        contract.evaluatePolicy(policy_id, "ON_TIME", 0)


def test_invalid_flight_status_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Invalid flight status should be rejected."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    with direct_vm.expect_revert("flight_status must be DELAYED or ON_TIME"):
        contract.evaluatePolicy(policy_id, "CANCELLED", 0)


def test_negative_delay_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Negative delay minutes should be rejected."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    with direct_vm.expect_revert("delay_minutes must be >= 0"):
        contract.evaluatePolicy(policy_id, "DELAYED", -10)


def test_empty_flight_number_rejected(direct_vm, direct_deploy, direct_alice):
    """Empty flight number should be rejected."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000

    with direct_vm.expect_revert("flight_number, flight_date, and claimant required"):
        contract.purchasePolicy("", "2026-09-15", "0x0000000000000000000000000000000000000042")


def test_empty_claimant_rejected(direct_vm, direct_deploy, direct_alice):
    """Empty claimant should be rejected."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000

    with direct_vm.expect_revert("flight_number, flight_date, and claimant required"):
        contract.purchasePolicy("BA173", "2026-09-15", "")


def test_evaluate_nonexistent_policy_rejected(direct_vm, direct_deploy, direct_alice):
    """Evaluating a non-existent policy should fail."""
    contract = direct_deploy("contracts/delayguard_protocol.py")

    with direct_vm.expect_revert("not found"):
        contract.evaluatePolicy(999, "DELAYED", 75)


def test_delay_boundary_29min_refund(direct_vm, direct_deploy, direct_alice, direct_bob):
    """29 min delay should trigger refund (below 30 min threshold)."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    result = contract.evaluatePolicy(policy_id, "DELAYED", 29)
    assert result == "DELAYED"

    # Should still record as refund (below threshold)
    transfers = json.loads(contract.getEmittedTransfers())
    assert "0" in transfers
    t = json.loads(transfers["0"])
    assert t["type"] == "refund"


def test_delay_boundary_30min_payout(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Exactly 30 min delay should trigger payout (at threshold)."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    result = contract.evaluatePolicy(policy_id, "DELAYED", 30)
    assert result == "DELAYED"

    transfers = json.loads(contract.getEmittedTransfers())
    t = json.loads(transfers["0"])
    assert t["type"] == "payout"


def test_transfer_data_integrity(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Transfer record should contain all required fields with correct values."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    contract.evaluatePolicy(policy_id, "DELAYED", 75)

    transfers = json.loads(contract.getEmittedTransfers())
    t = json.loads(transfers["0"])

    # Check all required fields
    assert "type" in t
    assert "amount" in t
    assert "recipient" in t
    assert "policy_id" in t
    assert "flight_number" in t
    assert "delay_minutes" in t

    # Check values
    assert t["type"] == "payout"
    assert t["amount"] == 1000000000000000000
    assert t["recipient"] == _addr_hex(direct_bob)
    assert t["policy_id"] == 0
    assert t["flight_number"] == "BA173"
    assert t["delay_minutes"] == 75


def test_multiple_users_independent_policies(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Different users can purchase independent policies."""
    contract = direct_deploy("contracts/delayguard_protocol.py")

    # Alice purchases policy 0
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    contract.purchasePolicy("AA100", "2026-10-01", _addr_hex(direct_alice))

    # Bob purchases policy 1
    direct_vm.sender = direct_bob
    direct_vm.value = 2000000000000000000
    contract.purchasePolicy("BB200", "2026-10-02", _addr_hex(direct_bob))

    # Verify both exist
    policy0 = json.loads(contract.getPolicy(0))
    policy1 = json.loads(contract.getPolicy(1))

    assert policy0["flight_number"] == "AA100"
    assert policy0["amount"] == 1000000000000000000
    assert policy1["flight_number"] == "BB200"
    assert policy1["amount"] == 2000000000000000000


def test_get_transfer_specific_index(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Can retrieve a specific transfer by index."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))
    contract.evaluatePolicy(0, "DELAYED", 75)

    transfer = contract.getTransfer("0")
    t = json.loads(transfer)
    assert t["type"] == "payout"


def test_get_transfer_not_found(direct_vm, direct_deploy, direct_alice):
    """Retrieving non-existent transfer returns exists=False."""
    contract = direct_deploy("contracts/delayguard_protocol.py")

    result = contract.getTransfer("999")
    parsed = json.loads(result)
    assert parsed["exists"] is False


def test_case_insensitive_status(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Flight status should be case-insensitive (normalized to upper)."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 1000000000000000000
    policy_id = contract.purchasePolicy("BA173", "2026-09-15", _addr_hex(direct_bob))

    # Lowercase should work
    result = contract.evaluatePolicy(policy_id, "delayed", 75)
    assert result == "DELAYED"


def test_multiple_policies_sequential_ids(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Policy IDs should increment sequentially."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice

    direct_vm.value = 100000000000000000
    id0 = contract.purchasePolicy("F1", "2026-01-01", _addr_hex(direct_bob))
    id1 = contract.purchasePolicy("F2", "2026-01-02", _addr_hex(direct_bob))
    id2 = contract.purchasePolicy("F3", "2026-01-03", _addr_hex(direct_bob))

    assert id0 == 0
    assert id1 == 1
    assert id2 == 2


def test_emitted_transfers_accumulate(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Transfer records persist and accumulate across evaluations."""
    contract = direct_deploy("contracts/delayguard_protocol.py")
    direct_vm.sender = direct_alice

    # Policy 0: DELAYED
    direct_vm.value = 100000000000000000
    contract.purchasePolicy("F1", "2026-01-01", _addr_hex(direct_bob))
    contract.evaluatePolicy(0, "DELAYED", 75)

    # Policy 1: ON_TIME
    direct_vm.value = 100000000000000000
    contract.purchasePolicy("F2", "2026-01-02", _addr_hex(direct_bob))
    contract.evaluatePolicy(1, "ON_TIME", 0)

    transfers = json.loads(contract.getEmittedTransfers())
    assert len(transfers) == 2
    assert "0" in transfers
    assert "1" in transfers
