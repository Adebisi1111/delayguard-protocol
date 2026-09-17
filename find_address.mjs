import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const account = privateKeyToAccount(PRIVATE_KEY);
const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const hash = '0x8492d9b2173dfb6df8c37bcfb1f595c774f5dd484b33a19cf8b65f5f698a82e1';
  
  // Get transaction
  const tx = await client.getTransaction({ hash });
  console.log('Transaction:', JSON.stringify(tx, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2));
  
  // Also try to get receipt with different method
  try {
    const receipt = await client.getTransactionReceipt({ hash });
    if (receipt) {
      console.log('Receipt:', JSON.stringify(receipt, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2));
    }
  } catch (e) {
    console.log('Receipt error:', e.message);
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
