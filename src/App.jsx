import { useCallback, useMemo, useState } from 'react';
import { ethers } from 'ethers';
import {
  Activity, ArrowDownToLine, ArrowLeftRight, ArrowUpRight, Check, ChevronDown,
  CircleHelp, Clock3, Copy, ExternalLink, Eye, FlaskConical, LockKeyhole,
  RefreshCw, Shield, ShieldAlert, Wallet, Zap
} from 'lucide-react';
import './App.css';

const SEPOLIA_ID = 11155111;
const SEPOLIA_HEX = '0xaa36a7';
const ERC20_ABI = [
  'function balanceOf(address owner) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)',
  'function name() view returns (string)'
];

const shortAddress = (address) => address ? `${address.slice(0, 6)}…${address.slice(-4)}` : '';
const formatAmount = (value, max = 5) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '0';
  return n.toLocaleString(undefined, { maximumFractionDigits: max });
};

export default function App() {
  const [provider, setProvider] = useState(null);
  const [address, setAddress] = useState('');
  const [network, setNetwork] = useState('');
  const [nativeBalance, setNativeBalance] = useState('—');
  const [tokens, setTokens] = useState([]);
  const [tokenAddress, setTokenAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState('');
  const [noticeType, setNoticeType] = useState('info');
  const [events, setEvents] = useState([]);
  const [simulation, setSimulation] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

  const isSepolia = Number(network) === SEPOLIA_ID;
  const explorer = address ? `https://sepolia.etherscan.io/address/${address}` : 'https://sepolia.etherscan.io';

  const pushEvent = useCallback((title, detail, status = 'success') => {
    setEvents((prev) => [{ id: `${Date.now()}-${Math.random()}`, title, detail, status, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 8));
  }, []);

  const announce = (message, type = 'info') => {
    setNotice(message);
    setNoticeType(type);
  };

  const refreshWallet = useCallback(async (activeProvider, activeAddress) => {
    const [chainId, balance] = await Promise.all([
      activeProvider.send('eth_chainId', []),
      activeProvider.getBalance(activeAddress)
    ]);
    setNetwork(Number(BigInt(chainId)));
    setNativeBalance(ethers.formatEther(balance));
  }, []);

  const connectWallet = async () => {
    if (!window.ethereum) {
      announce('No injected wallet found. Open this page in MetaMask or Trust Wallet’s DApp browser.', 'error');
      return;
    }
    try {
      setLoading(true);
      const nextProvider = new ethers.BrowserProvider(window.ethereum);
      const accounts = await nextProvider.send('eth_requestAccounts', []);
      if (!accounts?.length) throw new Error('No account was returned by your wallet.');
      setProvider(nextProvider);
      setAddress(ethers.getAddress(accounts[0]));
      await refreshWallet(nextProvider, accounts[0]);
      announce('Wallet connected. This demo never asks for your seed phrase or private key.', 'success');
      pushEvent('Wallet connected', shortAddress(accounts[0]));
    } catch (error) {
      announce(error?.shortMessage || error?.message || 'Could not connect wallet.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const switchToSepolia = async () => {
    if (!window.ethereum) return announce('Connect an injected wallet first.', 'error');
    try {
      await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: SEPOLIA_HEX }] });
      const nextProvider = new ethers.BrowserProvider(window.ethereum);
      setProvider(nextProvider);
      if (address) await refreshWallet(nextProvider, address);
      announce('Switched to Sepolia testnet.', 'success');
    } catch (error) {
      if (error?.code === 4902) announce('Add Sepolia to your wallet, then try switching again.', 'error');
      else announce(error?.message || 'Could not switch network.', 'error');
    }
  };

  const scanNative = async () => {
    if (!provider || !address) return announce('Connect your wallet before scanning.', 'error');
    try {
      setLoading(true);
      await refreshWallet(provider, address);
      pushEvent('Native balance scanned', 'Sepolia ETH balance refreshed');
      announce('Native balance refreshed from the connected network.', 'success');
    } catch (error) {
      announce(error?.shortMessage || error?.message || 'Balance scan failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const scanToken = async (event) => {
    event.preventDefault();
    if (!provider || !address) return announce('Connect your wallet before scanning assets.', 'error');
    if (!isSepolia) return announce('Switch to Sepolia before scanning token balances.', 'error');
    if (!ethers.isAddress(tokenAddress)) return announce('Enter a valid ERC-20 contract address.', 'error');
    try {
      setLoading(true);
      const contract = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
      const [rawBalance, decimals, symbol, name] = await Promise.all([
        contract.balanceOf(address), contract.decimals(), contract.symbol(), contract.name().catch(() => 'ERC-20 token')
      ]);
      const token = { address: ethers.getAddress(tokenAddress), name, symbol, balance: ethers.formatUnits(rawBalance, decimals) };
      setTokens((prev) => [token, ...prev.filter((item) => item.address.toLowerCase() !== token.address.toLowerCase())]);
      pushEvent('ERC-20 balance scanned', `${token.symbol}: ${formatAmount(token.balance)}`);
      announce(`Read ${token.symbol} balance successfully. No transaction was sent.`, 'success');
      setTokenAddress('');
    } catch (error) {
      announce(error?.shortMessage || error?.message || 'Token scan failed. Check the contract and network.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = () => {
    if (!address) return announce('Connect a wallet to create a local simulation.', 'error');
    const snapshot = {
      id: `SIM-${Date.now().toString().slice(-6)}`,
      wallet: address,
      native: nativeBalance,
      tokens: tokens.map((token) => ({ ...token })),
      createdAt: new Date().toLocaleTimeString()
    };
    setSimulation({ ...snapshot, state: 'simulated' });
    pushEvent('Simulation started', 'Local-only dry run · no transaction sent', 'warning');
    announce('Simulation created locally. No funds were moved, approved, or exposed.', 'success');
  };

  const returnSimulation = () => {
    if (!simulation) return;
    setSimulation((prev) => ({ ...prev, state: 'returned', returnedAt: new Date().toLocaleTimeString() }));
    pushEvent('Simulated return complete', 'Restored the demo snapshot in the UI only');
    announce('Simulation returned. This only resets demo state; it does not submit a blockchain transaction.', 'success');
  };

  const resetDemo = () => {
    setSimulation(null);
    setTokens([]);
    setEvents([]);
    announce('Local demo state cleared. Your wallet and on-chain balances were not changed.', 'success');
  };

  const stats = useMemo(() => [
    { label: 'Network', value: isSepolia ? 'Sepolia' : network ? 'Wrong network' : 'Not connected', icon: Activity },
    { label: 'Assets scanned', value: String(tokens.length + (address && nativeBalance !== '—' ? 1 : 0)).padStart(2, '0'), icon: Eye },
    { label: 'Simulation', value: simulation ? (simulation.state === 'returned' ? 'Returned' : 'Active') : 'Ready', icon: FlaskConical }
  ], [address, isSepolia, nativeBalance, network, simulation, tokens.length]);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="RUG MASTER home">
          <span className="brand-mark"><Shield size={22} strokeWidth={2.5} /></span>
          <span><b>RUG MASTER</b><small>WALLET SECURITY LAB</small></span>
        </a>
        <div className="side-label">WORKSPACE</div>
        <a className="nav-item active" href="#overview"><Activity size={17} /> Overview <span className="nav-dot" /></a>
        <a className="nav-item" href="#assets"><Wallet size={17} /> Asset scanner</a>
        <a className="nav-item" href="#simulation"><ArrowLeftRight size={17} /> Dry-run simulator</a>
        <a className="nav-item" href="#activity"><Clock3 size={17} /> Activity log</a>
        <div className="sidebar-bottom">
          <div className="testnet-card">
            <span className="pulse-dot" />
            <div><b>TESTNET MODE</b><small>Sepolia · No real funds</small></div>
          </div>
          <div className="sidebar-note"><LockKeyhole size={15} /> Your keys stay in your wallet. Never share a seed phrase.</div>
          <span className="version">RUG MASTER <span>v1.0.0</span></span>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> <b>Overview</b></div>
          <div className="top-actions">
            <span className="network-pill"><span className="pulse-dot" /> Sepolia testnet</span>
            <button className={address ? 'wallet-button connected' : 'wallet-button'} onClick={connectWallet} disabled={loading}>
              <Wallet size={16} /> {loading ? 'Working…' : address ? shortAddress(address) : 'Connect wallet'} <ChevronDown size={14} />
            </button>
          </div>
        </header>

        <div className="page-wrap" id="overview">
          <div className="eyebrow"><span className="eyebrow-line" /> EVM SECURITY PLAYGROUND <span className="version-tag">HACKATHON BUILD</span></div>
          <div className="hero-row">
            <div>
              <h1>See the risk.<br /><span>Keep control.</span></h1>
              <p className="hero-copy">A transparent wallet-security demo for scanning public balances and rehearsing a rug-pull response — without putting real assets at risk.</p>
            </div>
            <div className="hero-art" aria-hidden="true">
              <div className="orbit orbit-one" /><div className="orbit orbit-two" />
              <div className="shield-glow"><Shield size={68} strokeWidth={1.25} /></div>
              <div className="orbit-node node-one"><LockKeyhole size={15} /></div>
              <div className="orbit-node node-two"><Zap size={15} /></div>
              <div className="orbit-node node-three"><Activity size={15} /></div>
            </div>
          </div>

          {notice && <div className={`notice ${noticeType}`} role="status"><span>{noticeType === 'error' ? <ShieldAlert size={17} /> : <Check size={17} />}</span><p>{notice}</p><button onClick={() => setNotice('')} aria-label="Dismiss notice">×</button></div>}

          <div className="stats-grid">
            {stats.map(({ label, value, icon: Icon }) => <div className="stat-card" key={label}><div className="stat-top"><span>{label}</span><Icon size={17} /></div><strong>{value}</strong><small>{label === 'Network' ? (isSepolia ? 'Chain ID 11155111' : 'Sepolia required for scans') : label === 'Assets scanned' ? 'Native + ERC-20 reads' : 'No on-chain movement'}</small></div>)}
          </div>

          <div className="section-heading" id="assets"><div><span className="section-kicker">01 / INSPECT</span><h2>Wallet & asset scanner</h2><p>Read-only balance checks. Nothing is approved or transferred.</p></div><button className="subtle-button" onClick={scanNative} disabled={!address || loading}><RefreshCw size={15} /> Refresh</button></div>
          <div className="scanner-grid">
            <div className="panel wallet-panel">
              <div className="panel-title"><span className="panel-icon purple"><Wallet size={18} /></span><div><h3>Connected wallet</h3><small>Injected EVM wallet</small></div><span className={address ? 'status-chip good' : 'status-chip'}>{address ? 'CONNECTED' : 'DISCONNECTED'}</span></div>
              {address ? <><div className="address-box"><div><small>PUBLIC ADDRESS</small><b>{shortAddress(address)}</b></div><button onClick={() => { navigator.clipboard?.writeText(address); announce('Public address copied.', 'success'); }} aria-label="Copy address"><Copy size={15} /></button><a href={explorer} target="_blank" rel="noreferrer" aria-label="Open address on Sepolia Etherscan"><ExternalLink size={15} /></a></div><div className="balance-row"><div><small>SEPOLIA ETH BALANCE</small><strong>{formatAmount(nativeBalance, 6)} <em>ETH</em></strong></div><div className="eth-icon">Ξ</div></div>{!isSepolia && <button className="primary-button full" onClick={switchToSepolia}>Switch to Sepolia <ArrowUpRight size={16} /></button>}</> : <div className="empty-wallet"><div className="empty-icon"><Wallet size={25} /></div><b>No wallet connected</b><p>Connect MetaMask or a wallet with an injected EVM provider to read its public address and balance.</p><button className="primary-button" onClick={connectWallet} disabled={loading}>Connect wallet <ArrowUpRight size={16} /></button></div>}
              <div className="panel-foot"><LockKeyhole size={14} /> Read-only access · No signature requested</div>
            </div>

            <div className="panel token-panel">
              <div className="panel-title"><span className="panel-icon green"><Eye size={18} /></span><div><h3>ERC-20 token lookup</h3><small>Scan one contract at a time</small></div></div>
              <form onSubmit={scanToken} className="token-form">
                <label htmlFor="token-address">TOKEN CONTRACT ADDRESS</label>
                <input id="token-address" value={tokenAddress} onChange={(e) => setTokenAddress(e.target.value)} placeholder="0x…" spellCheck="false" autoComplete="off" />
                <button className="primary-button full" type="submit" disabled={loading || !address}><Eye size={16} /> {loading ? 'Scanning…' : 'Scan token balance'}</button>
              </form>
              <div className="token-results">
                <div className="list-heading"><span>SCANNED TOKENS</span><span>{tokens.length} found</span></div>
                {tokens.length ? tokens.map((token) => <div className="token-row" key={token.address}><span className="token-symbol">{token.symbol.slice(0, 3).toUpperCase()}</span><div className="token-meta"><b>{token.name} <small>{token.symbol}</small></b><span>{shortAddress(token.address)}</span></div><strong>{formatAmount(token.balance)}</strong></div>) : <div className="empty-token">Token balances will appear here after a successful read.</div>}
              </div>
            </div>
          </div>

          <div className="section-heading simulation-heading" id="simulation"><div><span className="section-kicker">02 / REHEARSE</span><h2>Drain-and-return simulation</h2><p>Practice the incident flow using a local snapshot — not a real transfer.</p></div><span className="dry-run-badge"><FlaskConical size={14} /> DRY RUN ONLY</span></div>
          <div className="simulation-card">
            <div className="simulation-main">
              <div className="simulation-icon"><ArrowLeftRight size={22} /></div>
              <div><h3>Simulate an incident, then restore the snapshot</h3><p>Creates a local record of the balances currently displayed. The “drain” is only a visual state change; no contract calls, token approvals, or transactions occur.</p></div>
            </div>
            <div className="simulation-steps">
              <div className={simulation ? 'sim-step complete' : 'sim-step current'}><span>{simulation ? <Check size={15} /> : '1'}</span><div><b>Capture snapshot</b><small>Record current displayed balances</small></div></div>
              <div className="step-connector" />
              <div className={simulation?.state === 'returned' ? 'sim-step complete' : simulation ? 'sim-step current' : 'sim-step'}><span>{simulation?.state === 'returned' ? <Check size={15} /> : '2'}</span><div><b>Restore snapshot</b><small>Mark the demo as returned</small></div></div>
            </div>
            {simulation && <div className="snapshot-box"><div className="snapshot-head"><span><span className="pulse-dot" /> {simulation.state === 'returned' ? 'SIMULATION RETURNED' : 'SIMULATION ACTIVE'}</span><code>{simulation.id}</code></div><div className="snapshot-data"><div><small>WALLET</small><b>{shortAddress(simulation.wallet)}</b></div><div><small>SNAPSHOT ETH</small><b>{formatAmount(simulation.native, 6)} ETH</b></div><div><small>ERC-20 ASSETS</small><b>{simulation.tokens.length}</b></div><div><small>CREATED</small><b>{simulation.createdAt}</b></div></div>{simulation.returnedAt && <p className="returned-note"><Check size={14} /> Demo state marked returned at {simulation.returnedAt}. No on-chain funds moved.</p>}</div>}
            <div className="simulation-actions"><button className="primary-button" onClick={runSimulation} disabled={!address || simulation?.state === 'simulated'}><FlaskConical size={16} /> {simulation ? 'Snapshot captured' : 'Run safe simulation'}</button><button className="secondary-button" onClick={returnSimulation} disabled={!simulation || simulation.state === 'returned'}><ArrowDownToLine size={16} /> Return simulation</button><button className="text-button" onClick={resetDemo}>Reset demo</button></div>
          </div>

          <div className="section-heading activity-heading" id="activity"><div><span className="section-kicker">03 / AUDIT</span><h2>Activity log</h2><p>Recent actions in this browser session.</p></div><span className="activity-count">{events.length} EVENTS</span></div>
          <div className="panel activity-panel">
            {events.length ? events.map((item) => <div className="event-row" key={item.id}><span className={`event-icon ${item.status}`}>{item.status === 'warning' ? <FlaskConical size={16} /> : <Check size={16} />}</span><div className="event-copy"><b>{item.title}</b><small>{item.detail}</small></div><time>{item.time}</time></div>) : <div className="empty-events"><Clock3 size={20} /><b>No activity yet</b><span>Connect your wallet or run a scan to create an event.</span></div>}
          </div>

          <div className="safety-banner"><span><Shield size={20} /></span><div><b>Safety by design</b><p>RUG MASTER never requests seed phrases, private keys, unlimited approvals, or real-asset transfers. Only connect a wallet you control and use Sepolia testnet for this demo.</p></div><button onClick={() => setShowHelp((value) => !value)} aria-expanded={showHelp}><CircleHelp size={18} /></button></div>
          {showHelp && <div className="help-panel"><b>Quick setup</b><ol><li>Install MetaMask or open this site in a compatible wallet’s DApp browser.</li><li>Switch the wallet network to Sepolia and use test ETH only.</li><li>Connect, refresh the native balance, then enter a verified Sepolia ERC-20 contract address to scan its balance.</li><li>Run the simulation and return it to demonstrate the incident lifecycle. Both actions are local UI state only.</li></ol><a href="https://sepolia.etherscan.io" target="_blank" rel="noreferrer">Open Sepolia Etherscan <ExternalLink size={13} /></a></div>}
          <footer><span>© 2026 RUG MASTER LAB</span><span>BUILT FOR EDUCATION <span className="footer-dot">·</span> EVM / SEPOLIA</span></footer>
        </div>
      </section>
    </main>
  );
}