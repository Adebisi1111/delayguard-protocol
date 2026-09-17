import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const hash = '0x3fb58856919c1dafc155fc77d8a6ea8d5e5f0e630efa578c46e9064ef373324f';
  
  // Get the transaction
  const tx = await client.getTransaction({ hash });
  console.log('Transaction:', JSON.stringify(tx, (k, v) => typeof v === 'bigint' ? v.toString() : v, 2));
}

main().catch(e => { console.error(e.message); process.exit(1); });
