# RUG MASTER — Wallet Security Lab

A React + Vite EVM wallet-security demo designed for a hackathon. It connects to an injected browser wallet, reads native ETH balance, scans ERC-20 balances by contract address, and demonstrates a **local-only simulated incident and return workflow**.

## Safety scope

- Sepolia testnet is the intended network for token scans.
- The app never requests seed phrases or private keys.
- It does not execute a real “drain”, send tokens, request token approvals, or deploy a malicious contract.
- “Run safe simulation” snapshots the balances shown in the UI. “Return simulation” changes only local UI state; neither button sends a blockchain transaction.
- Public addresses and balances are read-only information. Only connect a wallet you control.

## Requirements

- Node.js 20+ recommended
- npm
- MetaMask or another injected EVM wallet (Trust Wallet's DApp browser may expose `window.ethereum`)
- Sepolia testnet configured in the wallet for the intended test environment

## Run locally

```bash
npm install
npm run dev
```

Open the local URL printed by Vite.

## Production build

```bash
npm run build
npm run preview
```

## How to demo

1. Open the app in a browser with an injected wallet.
2. Click **Connect wallet** and approve the standard account connection prompt.
3. Switch to Sepolia if the app detects another network.
4. Click **Refresh** to read the connected address's Sepolia ETH balance.
5. Paste a verified ERC-20 contract address deployed on Sepolia and click **Scan token balance**. The app calls only `balanceOf`, `decimals`, `symbol`, and `name` read methods.
6. Click **Run safe simulation**, then **Return simulation** to demonstrate a local incident lifecycle.

## Tech stack

- React 18 + Vite
- ethers v6
- lucide-react icons

## Limitations

- ERC-20 scanning is by contract address; it is not an exhaustive wallet-wide token discovery service.
- Browser state and activity log are temporary and clear on reload.
- No smart contract is deployed by this frontend.
- If no injected provider is available, open the site in a compatible wallet browser or add a WalletConnect integration separately.
