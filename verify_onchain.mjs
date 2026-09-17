import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const CONTRACT = '0x829FbDd2cE53B535a4a3A3A2aE383bf7025D0366';

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  console.log('=== DelayGuard On-Chain Verification ===');
  console.log('Contract:', CONTRACT);
  console.log('Deployer:', account.address);
  console.log('')

  // Check balance
  const balance = await client.getBalance({ address: account.address });
  console.log('Balance:', Number(balance) / 1e18, 'GEN');
  console.log('')

  // Test 1: Read initial transfer count
  console.log('1. Reading transfer count...');
  const count0 = await client.readContract({
    address: CONTRACT,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('   Count:', count0);

  // Test 2: Purchase policy (0.001 GEN)
  console.log('2. Purchasing policy (0.001 GEN)...');
  const purchaseTx = await client.writeContract({
    address: CONTRACT,
    functionName: 'purchasePolicy',
    args: ['BA173', '2026-09-15', account.address],
    value: 1000000000000000n,
  });
  console.log('   Tx:', purchaseTx);

  console.log('   Waiting for consensus...');
  await new Promise(r => setTimeout(r, 30000));

  // Test 3: Read policy
  console.log('3. Reading policy...');
  const policy = await client.readContract({
    address: CONTRACT,
    functionName: 'getPolicy',
    args: [0],
  });
  console.log('   Policy:', policy);

  // Test 4: Evaluate (DELAYED with 75 min)
  console.log('4. Evaluating policy (DELAYED, 75 min)...');
  const evalTx = await client.writeContract({
    address: CONTRACT,
    functionName: 'evaluatePolicy',
    args: [0, 'DELAYED', 75],
    value: 0n,
  });
  console.log('   Tx:', evalTx);

  console.log('   Waiting for consensus...');
  await new Promise(r => setTimeout(r, 60000));

  // Check results
  const policyAfter = await client.readContract({
    address: CONTRACT,
    functionName: 'getPolicy',
    args: [0],
  });
  console.log('   Policy after:', policyAfter);

  const transfers = await client.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('   Transfers:', transfers);

  const countAfter = await client.readContract({
    address: CONTRACT,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('   Transfer count after:', countAfter);

  console.log('');
  console.log('=== Verification Complete ===');
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + CONTRACT);
}

main().catch(e => { console.error(e.message); process.exit(1); });
