import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const CONTRACT = '0x318CBF3Ad6B0c57F6BFCA096C9b55665e08cb883';

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  console.log('=== Testing Refund Path ===');

  // Check current count
  const countBefore = await client.readContract({
    address: CONTRACT,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count before:', countBefore);

  // Purchase policy 2 (0.003 GEN)
  console.log('\nPurchasing policy 2 (0.003 GEN)...');
  const purchaseHash = await client.writeContract({
    address: CONTRACT,
    functionName: 'purchasePolicy',
    args: ['UA999', '2026-09-20', account.address],
    value: 3000000000000000n,
  });
  console.log('Tx:', purchaseHash);
  await new Promise(r => setTimeout(r, 30000));

  const policy = await client.readContract({
    address: CONTRACT,
    functionName: 'getPolicy',
    args: [1],
  });
  console.log('Policy:', policy);

  // Evaluate ON_TIME (should trigger refund)
  console.log('\nEvaluating (ON_TIME, 0 min)...');
  const evalHash = await client.writeContract({
    address: CONTRACT,
    functionName: 'evaluatePolicy',
    args: [1, 'ON_TIME', 0],
    value: 0n,
  });
  console.log('Tx:', evalHash);
  await new Promise(r => setTimeout(r, 30000));

  // Check results
  const policyAfter = await client.readContract({
    address: CONTRACT,
    functionName: 'getPolicy',
    args: [1],
  });
  console.log('Policy after:', policyAfter);

  const transfers = await client.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('All transfers:', transfers);

  const countAfter = await client.readContract({
    address: CONTRACT,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count after:', countAfter);

  console.log('\n=== Refund Path Complete ===');
}

main().catch(e => { console.error(e.message); process.exit(1); });
