# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# DelayGuard Protocol — Flight Insurance on GenLayer

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from genlayer import *


DELAY_THRESHOLD_MINUTES = 30


@allow_storage
@dataclass
class Policy:
    flight_number: str
    flight_date: str
    depositor: str
    claimant: str
    amount: u256
    status: str
    verdict: str
    delay_minutes: u256
    created_at: u256


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class DelayGuardProtocol(gl.Contract):
    next_policy_id: u256
    policies: TreeMap[u256, Policy]
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

        self.policies[policy_id] = Policy(
            flight_number=flight_number,
            flight_date=flight_date,
            depositor=str(gl.message.sender_address),
            claimant=claimant,
            amount=gl.message.value,
            status="RESEARCHING",
            verdict="",
            delay_minutes=u256(0),
            created_at=u256(self._now())
        )

        return policy_id

    @gl.public.write
    def evaluatePolicy(self, policy_id: u256) -> str:
        policy = self.policies.get(policy_id, None)
        if policy is None:
            raise gl.vm.UserError(f"Policy {policy_id} not found")
        if policy.status == "RESOLVED":
            raise gl.vm.UserError(f"Policy {policy_id} already resolved")

        prompt = (
            f"Check flight {policy.flight_number} on {policy.flight_date}.\n"
            f"Respond with JSON: {{\"flight_status\": \"DELAYED\" or \"ON_TIME\", \"delay_minutes\": <int>}}"
        )

        try:
            raw = gl.nondet.exec_prompt(prompt)
            # Handle Lazy evaluation
            if hasattr(raw, 'get') and callable(raw.get):
                raw = raw.get()
            if isinstance(raw, dict):
                parsed = raw
            elif isinstance(raw, gl.vm.Return):
                parsed = json.loads(raw.calldata)
            elif isinstance(raw, str):
                parsed = json.loads(raw)
            else:
                parsed = {"flight_status": "ON_TIME", "delay_minutes": 0}
        except Exception as e:
            raise gl.vm.UserError(f"LLM parse error: {e}")

        flight_status = parsed.get("flight_status", "ON_TIME")
        delay_minutes = int(parsed.get("delay_minutes", 0))

        policy.verdict = flight_status
        policy.delay_minutes = u256(delay_minutes)
        policy.status = "RESOLVED"

        if flight_status == "DELAYED" and delay_minutes >= DELAY_THRESHOLD_MINUTES:
            _Recipient(Address(policy.claimant)).emit_transfer(value=policy.amount)
            self.emitted_transfers[str(self.transfer_count)] = json.dumps({
                "type": "payout",
                "amount": int(policy.amount),
                "recipient": policy.claimant,
                "policy_id": int(policy_id),
                "flight_number": policy.flight_number,
                "delay_minutes": delay_minutes,
            })
        else:
            _Recipient(Address(policy.depositor)).emit_transfer(value=policy.amount)
            self.emitted_transfers[str(self.transfer_count)] = json.dumps({
                "type": "refund",
                "amount": int(policy.amount),
                "recipient": policy.depositor,
                "policy_id": int(policy_id),
                "flight_number": policy.flight_number,
                "delay_minutes": delay_minutes,
            })

        self.transfer_count += u256(1)
        self.policies[policy_id] = policy
        return flight_status

    @gl.public.view
    def getPolicy(self, policy_id: u256) -> str:
        policy = self.policies.get(policy_id, None)
        if policy is None:
            return json.dumps({"policy_id": int(policy_id), "exists": False})
        return json.dumps({
            "policy_id": int(policy_id),
            "exists": True,
            "flight_number": policy.flight_number,
            "flight_date": policy.flight_date,
            "depositor": policy.depositor,
            "claimant": policy.claimant,
            "amount": int(policy.amount),
            "status": policy.status,
            "verdict": policy.verdict,
            "delay_minutes": int(policy.delay_minutes),
            "created_at": int(policy.created_at)
        })

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
