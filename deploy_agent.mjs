import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Use the agent wallet which has more funds
const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
console.log('Deployer:', account.address);

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const balance = await client.getBalance({ address: account.address });
  console.log('Balance:', balance.toString(), 'wei =', Number(balance) / 1e18, 'GEN');

  // Deploy contract
  const fs = await import('fs');
  const code = fs.readFileSync('contracts/delayguard_protocol.py', 'utf8');

  console.log('Deploying...');
  const hash = await client.deployContract({ code, args: [] });
  console.log('Tx hash:', hash);

  console.log('Waiting...');
  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 60 });
  const address = receipt?.data?.contractAddress || receipt?.contractAddress;
  console.log('Contract at:', address);
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + address);
}

main().catch(e => { console.error(e.message); process.exit(1); });
