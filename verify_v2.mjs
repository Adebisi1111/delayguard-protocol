import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const CONTRACT = '0x70Fd41D09dF03eea296647d30F85F151a12d6211';

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  console.log('=== DelayGuard On-Chain Verification ===');
  console.log('Contract:', CONTRACT);
  console.log('Deployer:', account.address);

  const balance = await client.getBalance({ address: account.address });
  console.log('Balance:', Number(balance) / 1e18, 'GEN');
  console.log('');

  // Check initial state
  const count = await client.readContract({
    address: CONTRACT,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count:', count);

  // Purchase policy with small amount
  console.log('Purchasing policy (0.001 GEN)...');
  const hash = await client.writeContract({
    address: CONTRACT,
    functionName: 'purchasePolicy',
    args: ['BA173', '2026-09-15', account.address],
    value: 1000000000000000n, // 0.001 GEN
  });
  console.log('Tx:', hash);

  await new Promise(r => setTimeout(r, 30000));

  const policy = await client.readContract({
    address: CONTRACT,
    functionName: 'getPolicy',
    args: [0],
  });
  console.log('Policy:', policy);

  // Evaluate DELAYED
  console.log('Evaluating (DELAYED, 75 min)...');
  const evalHash = await client.writeContract({
    address: CONTRACT,
    functionName: 'evaluatePolicy',
    args: [0, 'DELAYED', 75],
    value: 0n,
  });
  console.log('Tx:', evalHash);

  await new Promise(r => setTimeout(r, 30000));

  const policyAfter = await client.readContract({
    address: CONTRACT,
    functionName: 'getPolicy',
    args: [0],
  });
  console.log('Policy after:', policyAfter);

  const transfers = await client.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('Transfers:', transfers);

  const countAfter = await client.readContract({
    address: CONTRACT,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count:', countAfter);
}

main().catch(e => { console.error(e.message); process.exit(1); });
