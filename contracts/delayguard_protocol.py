# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# DelayGuard Protocol — Flight Insurance on GenLayer
# Deployed on Bradbury testnet

import json
from datetime import datetime, timezone
from genlayer import *


DELAY_THRESHOLD_MINUTES = 30


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass
    class Write:
        pass


class DelayGuardProtocol(gl.Contract):
    # JSON storage for Bradbury compatibility
    next_policy_id: u256
    policies: TreeMap[u256, str]
    emitted_transfers: TreeMap[str, str]
    transfer_count: u256 = u256(0)

    def __init__(self):
        pass

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    @gl.public.write.payable
    def purchasePolicy(self, flight_number: str, flight_date: str, claimant: str) -> u256:
        if gl.message.value <= u256(0):
            raise gl.vm.UserError("Policy must be funded with GEN")
        if not flight_number or not flight_date or not claimant:
            raise gl.vm.UserError("flight_number, flight_date, and claimant required")

        policy_id = self.next_policy_id
        self.next_policy_id += u256(1)

        policy = {
            "flight_number": flight_number,
            "flight_date": flight_date,
            "depositor": gl.message.sender_address.as_hex,
            "claimant": claimant,
            "amount": int(gl.message.value),
            "status": "RESEARCHING",
            "verdict": "",
            "delay_minutes": 0,
            "created_at": self._now()
        }
        self.policies[policy_id] = json.dumps(policy)

        return policy_id

    @gl.public.write
    def evaluatePolicy(self, policy_id: u256, flight_status: str, delay_minutes: int) -> str:
        policy_raw = self.policies.get(policy_id, None)
        if policy_raw is None:
            raise gl.vm.UserError(f"Policy {policy_id} not found")

        policy = json.loads(policy_raw)
        if policy["status"] == "RESOLVED":
            raise gl.vm.UserError(f"Policy {policy_id} already resolved")

        flight_status = flight_status.strip().upper()
        if flight_status not in ("DELAYED", "ON_TIME"):
            raise gl.vm.UserError("flight_status must be DELAYED or ON_TIME")
        if delay_minutes < 0:
            raise gl.vm.UserError("delay_minutes must be >= 0")

        policy["verdict"] = flight_status
        policy["delay_minutes"] = delay_minutes
        policy["status"] = "RESOLVED"

        if flight_status == "DELAYED" and delay_minutes >= DELAY_THRESHOLD_MINUTES:
            _Recipient(Address(policy["claimant"])).emit_transfer(value=u256(policy["amount"]))
            self.emitted_transfers[str(self.transfer_count)] = json.dumps({
                "type": "payout",
                "amount": policy["amount"],
                "recipient": policy["claimant"],
                "policy_id": int(policy_id),
                "flight_number": policy["flight_number"],
                "delay_minutes": delay_minutes,
            })
        else:
            _Recipient(Address(policy["depositor"])).emit_transfer(value=u256(policy["amount"]))
            self.emitted_transfers[str(self.transfer_count)] = json.dumps({
                "type": "refund",
                "amount": policy["amount"],
                "recipient": policy["depositor"],
                "policy_id": int(policy_id),
                "flight_number": policy["flight_number"],
                "delay_minutes": delay_minutes,
            })

        self.transfer_count += u256(1)
        self.policies[policy_id] = json.dumps(policy)
        return flight_status

    @gl.public.view
    def getPolicy(self, policy_id: u256) -> str:
        policy_raw = self.policies.get(policy_id, None)
        if policy_raw is None:
            return json.dumps({"policy_id": int(policy_id), "exists": False})
        return policy_raw

    @gl.public.view
    def getTransferCount(self) -> str:
        return json.dumps({"count": int(self.transfer_count)})

    @gl.public.view
    def getTransfer(self, index: str) -> str:
        val = self.emitted_transfers.get(index, None)
        if val is None:
            return json.dumps({"exists": False})
        return val

    @gl.public.view
    def getEmittedTransfers(self) -> str:
        result = {}
        try:
            for k in self.emitted_transfers.keys():
                result[k] = self.emitted_transfers[k]
        except Exception as e:
            result["error"] = str(e)
        return json.dumps(result)
