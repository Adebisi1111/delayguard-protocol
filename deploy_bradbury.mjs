#!/usr/bin/env node
// deploy_bradbury.mjs - Deploy DelayGuard to Bradbury testnet
import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';

// Bradbury testnet configuration
const BRADBURY_CHAIN_ID = 61999;
const BRADBURY_RPC = 'https://studio.genlayer.com/api';

// Private key (0x023d... -> 0x61fd00...)
const PRIVATE_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';

const account = privateKeyToAccount(PRIVATE_KEY);
console.log('Deployer address:', account.address);

const chain = {
  id: BRADBURY_CHAIN_ID,
  name: 'Bradbury',
  rpcUrls: { default: { http: [BRADBURY_RPC] } },
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  blockExplorers: { default: { name: 'GenLayer Explorer', url: 'https://explorer-studio.genlayer.com' } },
};

const client = createClient({ chain, account });

async function main() {
  console.log('Reading contract...');
  const code = fs.readFileSync('contracts/delayguard_protocol.py', 'utf8');

  console.log('Estimating fees...');
  const estimate = await client.estimateTransactionFees({ kind: 'deploy', code, args: [] });
  console.log('Fee estimate:', estimate);

  console.log('Deploying...');
  const result = await client.deployContract({
    code,
    args: [],
    fees: {
      distribution: estimate.distribution,
      feeValue: estimate.feeValue.toString(),
    },
  });

  console.log('Deploy tx hash:', result);
  console.log('Waiting for finalization...');

  const receipt = await client.waitForTransactionReceipt({
    hash: result,
    waitUntil: 'finalized',
    retries: 120,
  });

  console.log('Receipt:', receipt);

  const address = receipt?.data?.contractAddress || receipt?.contractAddress;
  console.log('Contract deployed at:', address);
  console.log('Explorer: https://explorer-studio.genlayer.com/address/' + address);
}

main().catch(e => { console.error(e); process.exit(1); });
