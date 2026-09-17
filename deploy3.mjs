import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';

const PRIVATE_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const account = privateKeyToAccount(PRIVATE_KEY);
console.log('Deployer:', account.address);

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  const code = fs.readFileSync('contracts/delayguard_protocol.py', 'utf8');

  console.log('Deploying updated contract to Bradbury...');
  const hash = await client.deployContract({ code, args: [] });
  console.log('Tx hash:', hash);

  console.log('Waiting for finalization...');
  const receipt = await client.waitForTransactionReceipt({ hash, waitUntil: 'finalized', retries: 120 });
  const address = receipt?.data?.contractAddress || receipt?.contractAddress;
  console.log('Contract deployed at:', address);
  console.log('Explorer: https://explorer-bradbury.genlayer.com/address/' + address);
}

main().catch(e => { console.error(e.message); process.exit(1); });
