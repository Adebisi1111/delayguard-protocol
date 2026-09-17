import { createClient, chains, createFeesDistribution } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const code = fs.readFileSync('contracts/delayguard_protocol.py', 'utf8');

  console.log('Estimating fees...');
  const estimate = await client.estimateTransactionGas({ kind: 'deploy', code, args: [] });
  console.log('Gas estimate:', estimate);

  const distribution = createFeesDistribution({
    leaderTimeunitsAllocation: estimate.distribution?.leaderTimeunitsAllocation || '100',
    validatorTimeunitsAllocation: estimate.distribution?.validatorTimeunitsAllocation || '200',
    rotations: estimate.distribution?.rotations || ['0'],
  });

  console.log('Deploying with fees...');
  const hash = await client.deployContract({
    code,
    args: [],
    fees: {
      distribution,
      feeValue: typeof estimate.feeValue === 'bigint' ? estimate.feeValue.toString() : estimate.feeValue,
    },
  });
  console.log('Tx hash:', hash);

  console.log('Waiting...');
  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 120 });
  const simplified = simplifyTransactionReceipt(receipt);
  console.log('Deployed at:', simplified.contractAddress || receipt?.data?.contractAddress);
}

main().catch(e => { console.error(e.message); process.exit(1); });
