#!/usr/bin/env node
// deploy_and_verify.mjs — Deploy DelayGuard to Bradbury and verify on-chain
import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONTRACT_PATH = path.join(__dirname, '..', 'contracts', 'delayguard_protocol.json');

// Default to agent wallet (has funds on Bradbury)
const PRIVATE_KEY = process.env.DEPLOYER_KEY || '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';

async function main() {
  const account = privateKeyToAccount(PRIVATE_KEY);
  console.log('Deployer:', account.address);

  const client = createClient({ chain: chains.testnetBradbury, account });

  // Check balance
  const balance = await client.getBalance({ address: account.address });
  const balanceGen = Number(balance) / 1e18;
  console.log('Balance:', balanceGen.toFixed(4), 'GEN');

  if (balanceGen < 0.01) {
    console.error('Insufficient balance. Need at least 0.01 GEN for deployment.');
    process.exit(1);
  }

  // Read contract
  const code = fs.readFileSync(CONTRACT_PATH.replace('.json', '.py'), 'utf8');

  // Deploy
  console.log('\n=== Deploying ===');
  const hash = await client.deployContract({ code, args: [] });
  console.log('Tx hash:', hash);

  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 120 });
  const address = receipt?.txDataDecoded?.contractAddress || receipt?.data?.contractAddress;
  
  if (!address) {
    console.error('Could not determine contract address');
    console.log('Full receipt:', JSON.stringify(receipt, null, 2));
    process.exit(1);
  }

  console.log('Contract deployed at:', address);
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + address);

  // Verify
  console.log('\n=== Verifying ===');
  
  // Check initial state
  const count0 = await client.readContract({
    address,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Initial transfer count:', count0);

  // Purchase policy
  console.log('\nPurchasing test policy (0.005 GEN)...');
  const purchaseHash = await client.writeContract({
    address,
    functionName: 'purchasePolicy',
    args: ['TEST001', '2026-12-31', account.address],
    value: 5000000000000000n,
  });
  console.log('Tx:', purchaseHash);
  await new Promise(r => setTimeout(r, 30000));

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
  console.log('\nPolicy after:', policyAfter);

  const countAfter = await client.readContract({
    address,
    functionName: 'getTransferCount',
    args: [],
  });
  console.log('Transfer count after:', countAfter);

  const transfers = await client.readContract({
    address,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('Transfers:', transfers);

  if (countAfter.count === 1) {
    console.log('\n✅ Verification successful!');
  } else {
    console.log('\n❌ Verification failed');
  }

  console.log('\n=== Deploy Complete ===');
  console.log('Contract:', address);
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + address);
}

main().catch(e => { console.error(e.message); process.exit(1); });
