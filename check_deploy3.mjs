import { createClient, chains, simplifyTransactionReceipt } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const account = privateKeyToAccount(PRIVATE_KEY);
const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const hash = '0x8492d9b2173dfb6df8c37bcfb1f595c774f5dd484b33a19cf8b65f5f698a82e1';
  
  console.log('Waiting for receipt...');
  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 60 });
  const simplified = simplifyTransactionReceipt(receipt);
  console.log('Simplified:', JSON.stringify(simplified, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2));
}

main().catch(e => { console.error(e.message); process.exit(1); });
