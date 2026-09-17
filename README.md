# DelayGuard Protocol

**Decentralized Flight Insurance on GenLayer Bradbury Testnet**

Live: https://adebisi1111.github.io/delayguard-protocol/
Contract: [`0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883`](https://explorer-bradbury.genlayer.com/address/0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883)

---

## What Is This?

DelayGuard is a decentralized flight insurance protocol built on GenLayer's AI-native blockchain.

1. **Purchase** — Buy a policy for any flight with GEN
2. **Wait** — After the flight date, check the status
3. **Evaluate** — If delayed ≥ 30 min → payout to claimant. If on time → refund to depositor
4. **Recorded** — Every payout and refund is stored permanently on-chain

---

## Quick Start

### Try It Now
1. Open https://adebisi1111.github.io/delayguard-protocol/
2. Connect MetaMask (add Bradbury testnet if needed)
3. Purchase a policy
4. Evaluate it after the flight date

### Test Locally

```bash
# Clone
git clone https://github.com/Adebisi1111/delayguard-protocol.git
cd delayguard-protocol

# Run all tests (requires GenLayer dev environment with .venv)
cd genlayer-project
.venv/bin/python -m pytest ../delayguard-protocol/tests/test_delayguard.py -v
```

**21 tests** covering basic flow, edge cases, security, and boundary conditions.

### Deploy Your Own

```bash
cd delayguard-protocol
npm install genlayer-js viem
node scripts/deploy.mjs
```

---

## Architecture

```
Frontend (index.html)                    Bradbury Testnet
┌────────────────────┐                  ┌──────────────────────────┐
│ MetaMask wallet    │ ── eth_call ───► │ Contract:                │
│ connection         │                  │ DelayGuardProtocol       │
│                    │ ── eth_sendTx ─► │ 0x318CBF3A...cb883        │
│ Purchase policy    │                  │                          │
│ Evaluate policy    │ ◄── events ──── │ Methods:                 │
│ View transfers     │                  │   purchasePolicy(...)    │
└────────────────────┘                  │   evaluatePolicy(...)    │
                                        │   getPolicy(...)         │
                                        │   getEmittedTransfers()  │
                                        └──────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Contract | Python (GenVM) |
| Network | GenLayer Bradbury Testnet (chain 72013) |
| Frontend | Vanilla HTML/JS (no build step) |
| Wallet | MetaMask / injected Web3 |
| Tests | pytest + gltest direct fixtures |
| Deployment | genlayer-js |

---

## Contract Methods

| Method | Type | Description |
|--------|------|-------------|
| `purchasePolicy(flight_number, flight_date, claimant)` | payable write | Purchase a policy |
| `evaluatePolicy(policy_id, flight_status, delay_minutes)` | write | Evaluate and trigger payout/refund |
| `getPolicy(policy_id)` | view | Get policy JSON |
| `getTransferCount()` | view | Get total transfer count |
| `getEmittedTransfers()` | view | Get all transfers |
| `getTransfer(index)` | view | Get specific transfer |

### Parameters

- `flight_number`: string, e.g. "BA173"
- `flight_date`: string, e.g. "2026-09-15"
- `claimant`: hex address, e.g. "0x1234..."
- `flight_status`: "DELAYED" or "ON_TIME"
- `delay_minutes`: integer, ≥ 30 triggers payout

---

## Test Coverage (21 tests)

**Basic Flow (6)**
- Purchase policy with funds
- Reject purchase without funds
- DELAYED evaluation → payout
- ON_TIME evaluation → refund
- Non-existent policy handling
- Transfer count incrementing

**Security & Validation (5)**
- Double-evaluate rejection
- Invalid flight status rejection
- Negative delay rejection
- Empty inputs rejection
- Non-existent policy evaluation

**Edge Cases (10)**
- Boundary: 29 min → refund
- Boundary: 30 min → payout
- Transfer data integrity
- Multiple users independent policies
- Specific transfer index retrieval
- Non-existent transfer retrieval
- Case-insensitive status
- Sequential policy IDs
- Transfer accumulation

---

## Networks

| Network | Chain ID | RPC | Status |
|---------|----------|-----|--------|
| **Bradbury Testnet** | 72013 (0x1194D) | https://studio.genlayer.com/api | ✅ Active |

### Contract Addresses

| Network | Address | Deployer |
|---------|---------|----------|
| Bradbury Testnet | `0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883` | `0x782abaE1...0991Fa01A` |

---

## FAQ

**What happens if my flight is delayed by exactly 30 minutes?**
Payout. The threshold is ≥ 30 minutes.

**Can I evaluate a policy twice?**
No. Once a policy is resolved (DELAYED or ON_TIME), it's final.

**Who can call evaluatePolicy?**
Anyone. The flight status is provided by the caller (oracle pattern).

**Why not automatic LLM verification?**
The current design uses caller-provided status for predictability. LLM oracle integration is planned.

**What currency is used?**
GEN (GenLayer's native token) on the Bradbury testnet.

---

## License

MIT

---

*Built with GenLayer — AI-native blockchain for intelligent contracts.*
