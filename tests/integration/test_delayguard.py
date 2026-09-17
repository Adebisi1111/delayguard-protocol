"""Integration tests for DelayGuard Protocol on Bradbury testnet."""
import pytest
import json


@pytest.mark.integration
def test_purchase_and_payout(deployed_contract, integration_alice, integration_bob):
    """Purchase policy and verify payout on Bradbury."""
    contract = deployed_contract
    reward_wei = int(0.01 * 10**18)

    # Check initial count
    count_raw = contract.getTransferCount(args=[]).call()
    count = json.loads(count_raw)
    assert count["count"] == 0

    # Purchase policy
    contract.purchasePolicy(
        args=["BA173", "2026-09-15", str(integration_alice.address)]
    ).transact_method(
        value=reward_wei,
        wait_interval=10000,
        wait_retries=20,
    )

    # Verify policy created
    policy_raw = contract.getPolicy(args=[0]).call()
    policy = json.loads(policy_raw)
    assert policy["status"] == "RESEARCHING"
    assert policy["amount"] == reward_wei

    # Evaluate as DELAYED (triggers payout)
    contract.evaluatePolicy(args=[0, "DELAYED", 75]).transact_method(
        wait_interval=10000,
        wait_retries=20,
    )

    # Verify resolved
    policy_raw = contract.getPolicy(args=[0]).call()
    policy = json.loads(policy_raw)
    assert policy["status"] == "RESOLVED"
    assert policy["verdict"] == "DELAYED"

    # Verify transfer count incremented
    count_raw = contract.getTransferCount(args=[]).call()
    count = json.loads(count_raw)
    assert count["count"] == 1

    # Verify transfer record
    transfers_raw = contract.getEmittedTransfers(args=[]).call()
    transfers = json.loads(transfers_raw)
    assert "0" in transfers
    transfer = json.loads(transfers["0"])
    assert transfer["type"] == "payout"
    assert transfer["amount"] == reward_wei
