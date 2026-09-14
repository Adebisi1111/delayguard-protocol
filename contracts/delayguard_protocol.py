# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# DelayGuard Protocol — Flight Insurance on GenLayer
#
# A decentralized flight insurance protocol where passengers are automatically
# paid out when AI consensus verifies flight delays.
#
# LIFECYCLE:
# purchasePolicy (funds locked) → RESEARCHING → evaluatePolicy → DELAYED → payout to passenger
#                                                              → ON_TIME → funds returned to underwriter

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from genlayer import *


# Configuration
DELAY_THRESHOLD_MINUTES = 30  # Minimum delay to trigger payout


@allow_storage
@dataclass
class Policy:
    flight_number: str
    flight_date: str
    depositor: str
    claimant: str
    amount: u256
    status: str  # RESEARCHING / RESOLVED
    verdict: str  # DELAYED / ON_TIME / INCONCLUSIVE
    delay_minutes: u256
    created_at: u256


class DelayGuardProtocol(gl.Contract):
    next_policy_id: u256
    policies: TreeMap[u256, Policy]

    def __init__(self):
        self.next_policy_id = u256(0)
        self.policies = TreeMap[u256, Policy]()

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    @gl.public.write.payable
    def purchasePolicy(self, flight_number: str, flight_date: str, claimant: str) -> u256:
        """Purchase flight insurance — locks funds into escrow."""
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
        """Evaluate policy via AI consensus on flight status."""
        policy = self.policies.get(policy_id, None)
        if policy is None:
            raise gl.vm.UserError(f"Policy {policy_id} not found")
        if policy.status == "RESOLVED":
            raise gl.vm.UserError(f"Policy {policy_id} already resolved")

        def leader_work() -> dict:
            prompt = (
                f"Check the current status of flight {policy.flight_number} on {policy.flight_date}.\n"
                f"Determine if the flight is DELAYED or ON TIME.\n"
                f"If delayed, provide the delay duration in minutes.\n\n"
                f"Respond as JSON: {{\"flight_status\": \"DELAYED\"|\"ON_TIME\", \"delay_minutes\": <int>}}"
            )
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            return res

        def validator(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                leader_msg = getattr(leaders_res, "message", "")
                try:
                    leader_work()
                    return False
                except gl.vm.UserError as e:
                    return str(e.message) == str(leader_msg)
                except Exception:
                    return False
            try:
                mine = leader_work()
            except Exception:
                return False
            return (
                mine.get("flight_status") == leaders_res.calldata.get("flight_status") and
                abs(int(mine.get("delay_minutes", 0)) - int(leaders_res.calldata.get("delay_minutes", 0))) <= 5
            )

        try:
            result = gl.vm.run_nondet_unsafe(leader_work, validator)
        except gl.vm.UserError:
            result = {"flight_status": "ON_TIME", "delay_minutes": 0}

        flight_status = result.get("flight_status", "ON_TIME")
        delay_minutes = int(result.get("delay_minutes", 0))

        policy.verdict = flight_status
        policy.delay_minutes = u256(delay_minutes)
        policy.status = "RESOLVED"

        if flight_status == "DELAYED" and delay_minutes >= DELAY_THRESHOLD_MINUTES:
            # Flight delayed — payout to passenger (claimant)
            _Recipient(Address(policy.claimant)).emit_transfer(value=policy.amount)
        else:
            # Flight on time — return funds to depositor (underwriter)
            _Recipient(Address(policy.depositor)).emit_transfer(value=policy.amount)

        self.policies[policy_id] = policy
        return flight_status

    @gl.public.view
    def getPolicy(self, policy_id: u256) -> str:
        """Get full policy details."""
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
