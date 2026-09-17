import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const PRIVATE_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const account = privateKeyToAccount(PRIVATE_KEY);
const CONTRACT = '0x829FbDd2cE53B535a4a3A3A2aE383bf7025D0366';

const client = createClient({ chain: chains.testnetBradbury, account });

async function main() {
  // Check if contract exists
  console.log('Checking contract code...');
  try {
    const code = await client.getBytecode({ address: CONTRACT });
    console.log('Contract bytecode length:', code?.length || 0);
  } catch (e) {
    console.log('Error getting bytecode:', e.message);
  }

  // Check contract schema
  console.log('Checking contract schema...');
  try {
    const schema = await client.getContractSchema({ address: CONTRACT });
    console.log('Schema:', JSON.stringify(schema, null, 2));
  } catch (e) {
    console.log('Error getting schema:', e.message);
  }

  // Try read
  console.log('Trying read...');
  try {
    const count = await client.readContract({
      address: CONTRACT,
      functionName: 'getTransferCount',
      args: [],
    });
    console.log('Transfer count:', count);
  } catch (e) {
    console.log('Read error:', e.message);
  }

  // Try estimate gas for purchasePolicy
  console.log('Estimating gas for purchasePolicy...');
  try {
    const estimate = await client.estimateTransactionGas({
      kind: 'write',
      address: CONTRACT,
      functionName: 'purchasePolicy',
      args: ['BA173', '2026-09-15', account.address],
      value: 1000000000000000n,
    });
    console.log('Gas estimate:', estimate);
  } catch (e) {
    console.log('Estimate error:', e.message);
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
