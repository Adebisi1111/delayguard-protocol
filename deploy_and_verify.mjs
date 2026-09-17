import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
console.log('Deployer:', account.address);

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const code = fs.readFileSync('contracts/delayguard_protocol.py', 'utf8');

  console.log('Deploying fresh contract...');
  const hash = await client.deployContract({ code, args: [] });
  console.log('Tx hash:', hash);

  console.log('Waiting for finalization...');
  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 120 });
  
  // Extract address from the receipt - GenLayer format
  const address = receipt?.txDataDecoded?.contractAddress || receipt?.data?.contractAddress;
  console.log('Contract deployed at:', address);
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + address);

  // Verify contract exists
  console.log('\nVerifying contract...');
  const count = await client.readContract({
    address,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count:', count);

  // Purchase policy
  console.log('\nPurchasing policy (0.005 GEN)...');
  const purchaseHash = await client.writeContract({
    address,
    functionName: 'purchasePolicy',
    args: ['BA173', '2026-09-15', account.address],
    value: 5000000000000000n,
  });
  console.log('Tx:', purchaseHash);
  await new Promise(r => setTimeout(r, 30000));

  const policy = await client.readContract({
    address,
    functionName: 'getPolicy',
    args: [0],
  });
  console.log('Policy:', policy);

  // Evaluate DELAYED
  console.log('\nEvaluating (DELAYED, 75 min)...');
  const evalHash = await client.writeContract({
    address,
    functionName: 'evaluatePolicy',
    args: [0, 'DELAYED', 75],
    value: 0n,
  });
  console.log('Tx:', evalHash);
  await new Promise(r => setTimeout(r, 30000));

  // Check results
  const policyAfter = await client.readContract({
    address,
    functionName: 'getPolicy',
    args: [0],
  });
  console.log('Policy after:', policyAfter);

  const transfers = await client.readContract({
    address,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('Transfers:', transfers);

  const countAfter = await client.readContract({
    address,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count:', countAfter);

  console.log('\n=== COMPLETE ===');
  console.log('Contract:', address);
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + address);
}

main().catch(e => { console.error(e.message); process.exit(1); });
