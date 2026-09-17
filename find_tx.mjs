import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const account = privateKeyToAccount(PRIVATE_KEY);
const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const hash = '0xd04a0d4b832f4b787d572a02d0afc1942154d1fb9ae7cf3418c6b231409f816f';
  
  // Try getting transaction instead of receipt
  try {
    const tx = await client.getTransaction({ hash });
    console.log('Transaction:', JSON.stringify(tx, null, 2));
  } catch (e) {
    console.log('getTransaction error:', e.message);
  }

  // Try with raw RPC
  try {
    const result = await client.request({
      method: 'eth_getTransactionByHash',
      params: [hash],
    });
    console.log('Raw result:', JSON.stringify(result, null, 2));
  } catch (e) {
    console.log('Raw RPC error:', e.message);
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
