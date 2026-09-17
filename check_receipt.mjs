import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const account = privateKeyToAccount(PRIVATE_KEY);
const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const hash = '0xd04a0d4b832f4b787d572a02d0afc1942154d1fb9ae7cf3418c6b231409f816f';
  
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 10000));
    try {
      const receipt = await client.getTransactionReceipt({ hash });
      if (receipt) {
        console.log('Receipt:', JSON.stringify(receipt, null, 2));
        return;
      }
    } catch (e) {
      console.log(`Attempt ${i+1}:`, e.message);
    }
  }
  console.log('Receipt not found after 30 attempts');
}

main().catch(e => { console.error(e.message); process.exit(1); });
