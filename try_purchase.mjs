import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const CONTRACT = '0x829FbDd2cE53B535a4a3A3A2aE383bf7025D0366';

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  console.log('Attempting purchasePolicy with explicit fees...');
  try {
    const hash = await client.writeContract({
      address: CONTRACT,
      functionName: 'purchasePolicy',
      args: ['BA173', '2026-09-15', account.address],
      value: 1000000000000000n,
      fees: {
        feeValue: '1000000000000000', // 0.001 GEN
      },
    });
    console.log('Tx hash:', hash);

    console.log('Waiting...');
    const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 60 });
    console.log('Receipt:', JSON.stringify(receipt, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2));
  } catch (e) {
    console.log('Error:', e.message);
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
