# DelayGuard Protocol

**Flight Insurance on GenLayer Bradbury Testnet**

Decentralized flight delay insurance. Purchase a policy, and if your flight is delayed by 30+ minutes, receive an automatic payout. If on time, the depositor gets a refund.

**Live:** https://adebisi1111.github.io/delayguard-protocol/
**Contract:** [`0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883`](https://explorer-bradbury.genlayer.com/address/0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883)

---

## How It Works

1. **Purchase Policy** — Enter flight number, date, and coverage amount (in GEN). Submit the transaction.
2. **Wait** — After the flight date, evaluate the policy with the actual flight status.
3. **Evaluate** — If DELAYED ≥ 30 min, the claimant receives the payout. If ON_TIME, the depositor gets a refund.
4. **Transfer Recorded** — All payouts and refunds are recorded on-chain with full details.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (index.html)                                  │
│  ─ MetaMask wallet connection                           │
│  ─ Bradbury testnet (chain ID 72013)                    │
│  ─ ABI-encoded contract calls                           │
└────────────────────────┬────────────────────────────────┘
                         │ eth_sendTransaction / eth_call
┌────────────────────────▼────────────────────────────────┐
│  GenLayer Bradbury Testnet                              │
│                                                         │
│  Contract: DelayGuardProtocol                           │
│  Address: 0x318CBF3A...cb883                            │
│                                                         │
│  Methods:                                               │
│    purchasePolicy(flight_number, flight_date, claimant) │
│    evaluatePolicy(policy_id, flight_status, delay_min)  │
│    getPolicy(policy_id) → JSON                          │
│    getTransferCount() → {count}                         │
│    getEmittedTransfers() → {key: JSON}                  │
│                                                         │
│  Storage:                                               │
│    policies: TreeMap<u256, str>                         │
│    emitted_transfers: TreeMap<str, str>                 │
│    next_policy_id: u256                                 │
│    transfer_count: u256                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Contract | Python (GenVM) |
| Network | GenLayer Bradbury Testnet |
| Frontend | Vanilla HTML/JS (no build) |
| Wallet | MetaMask / injected Web3 |
| Storage | GenLayer TreeMap (on-chain) |
| Verification | 5/5 validators consensus |

---

## Quick Start

### Try It Live
1. Open https://adebisi1111.github.io/delayguard-protocol/
2. Connect MetaMask (switch to Bradbury testnet)
3. Purchase a policy
4. Evaluate it after your flight date

### Local Development

```bash
# Clone
git clone https://github.com/Adebisi1111/delayguard-protocol.git
cd delayguard-protocol

# Run direct tests (fast, no Studio needed)
cd genlayer-project  # or your genlayer dev environment
pytest ../delayguard-protocol/tests/test_delayguard.py -v
```

### Deploy Your Own Contract

```bash
cd delayguard-protocol

# Requires Node.js + genlayer-js
npm install

# Deploy to Bradbury (requires private key with Bradbury GEN)
node deploy_and_verify.mjs
```

---

## Contract Details

### Networks

| Network | Chain ID | RPC | Explorer |
|---------|----------|-----|----------|
| **Bradbury Testnet** | 72013 (0x1194D) | https://studio.genlayer.com/api | https://explorer-bradbury.genlayer.com |

### Contract Addresses

| Network | Address | Deployer |
|---------|---------|----------|
| Bradbury Testnet | `0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883` | `0x782abaE1...0991Fa01A` |

---

## Testing

### Direct Mode (local, fast)
```bash
cd genlayer-project
.venv/bin/python -m pytest ../delayguard-protocol/tests/test_delayguard.py -v
```

**6 tests** covering:
- Policy purchase with funds
- Policy rejection without funds
- DELAYED evaluation → payout
- ON_TIME evaluation → refund
- Non-existent policy handling
- Transfer count incrementing

### On-Chain Verification
- Both payout and refund paths tested on Bradbury testnet
- Consensus: 5/5 validators agree
- Transactions finalized within ~30 seconds

---

## Roadmap

- [ ] LLM oracle integration for automatic flight status verification
- [ ] Multi-chain deployment (Asimov, Studio)
- [ ] Governance for parameter tuning (thresholds, fees)
- [ ] Advanced frontend with React + proper wallet management
- [ ] Mobile-optimized PWA

---

## License

MIT
