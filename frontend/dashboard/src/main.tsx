import React from "react";
import ReactDOM from "react-dom/client";
import { Activity, Gauge, GitBranch, Network, Server, ShieldCheck } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./styles.css";

type MigrationState = "S0_CLASSICAL" | "S1_PQC_READY" | "S2_HYBRID_KX" | "S3_HYBRID_FULL" | "S4_PQC_NATIVE";
type DataClass = "public" | "internal" | "confidential" | "secret" | "top-secret";

type ScanResponse = {
  endpoint: string;
  state: MigrationState;
  state_label: string;
  evidence: {
    negotiated_group: string;
    certificate_algorithm: string;
    certificate_chain_bytes: number;
    handshake_bytes: number;
    latency_ms: number;
  };
  recommendations: string[];
};

type RiskResponse = {
  risk_score: number;
  risk_band: string;
  crqc_probability: number;
  quantum_security_level: number;
  recommended_action: string;
};

type ComparisonRow = {
  profile: string;
  total_handshake: number;
  latency_ms: number;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const profileButtons = [
  { name: "Classical", port: 8445, color: "#64748b" },
  { name: "Hybrid", port: 8444, color: "#2563eb" },
  { name: "PQC Native", port: 8443, color: "#059669" },
  { name: "KEMTLS", port: 8446, color: "#b45309" },
];

const fallbackComparison = [
  { name: "Classical", bytes: 5100, latency: 18, color: "#64748b" },
  { name: "Hybrid", bytes: 18400, latency: 31, color: "#2563eb" },
  { name: "PQC-Native", bytes: 18100, latency: 34, color: "#059669" },
  { name: "KEMTLS", bytes: 15800, latency: 39, color: "#b45309" },
];

const stateNodes = [
  { id: "S0", label: "Classical", x: 50, y: 70 },
  { id: "S1", label: "PQC Ready", x: 190, y: 70 },
  { id: "S2", label: "Hybrid KX", x: 330, y: 70 },
  { id: "S3", label: "Hybrid Full", x: 470, y: 70 },
  { id: "S4", label: "PQC Native", x: 610, y: 70 },
];

const riskTimeline = [
  { year: 2026, internal: 0.12, confidential: 0.6, secret: 3 },
  { year: 2030, internal: 0.31, confidential: 1.55, secret: 7.75 },
  { year: 2034, internal: 0.69, confidential: 3.45, secret: 17.25 },
  { year: 2038, internal: 1, confidential: 5, secret: 25 },
  { year: 2042, internal: 1.31, confidential: 6.55, secret: 32.75 },
];

function stateShort(state: MigrationState): string {
  return state.replace("_CLASSICAL", "").replace("_PQC_READY", "").replace("_HYBRID_KX", "").replace("_HYBRID_FULL", "").replace("_PQC_NATIVE", "");
}

function App() {
  const [scan, setScan] = React.useState<ScanResponse | null>(null);
  const [risk, setRisk] = React.useState<RiskResponse | null>(null);
  const [comparison, setComparison] = React.useState(fallbackComparison);
  const [liveConnections, setLiveConnections] = React.useState<Record<string, ScanResponse>>({});
  const [sseConnected, setSseConnected] = React.useState(false);
  const [sshScan, setSshScan] = React.useState<ScanResponse | null>(null);
  const [dataClass, setDataClass] = React.useState<DataClass>("confidential");
  const [lifetime, setLifetime] = React.useState(30);
  const [selectedPort, setSelectedPort] = React.useState(8444);

  React.useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const scanResponse = await fetch(`${API_BASE}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hostname: "localhost", port: selectedPort }),
        signal: controller.signal,
      });
      const scanData: ScanResponse = await scanResponse.json();
      setScan(scanData);

      const riskResponse = await fetch(`${API_BASE}/risk-score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: scanData.state, data_class: dataClass, lifetime_years: lifetime }),
        signal: controller.signal,
      });
      setRisk(await riskResponse.json());
    }
    load().catch((error) => {
      if (error.name !== "AbortError") console.error(error);
    });
    return () => controller.abort();
  }, [selectedPort, dataClass, lifetime]);

  React.useEffect(() => {
    const controller = new AbortController();
    async function loadTelemetry() {
      const comparisonResponse = await fetch(`${API_BASE}/handshake-comparison`, { signal: controller.signal });
      const comparisonRows: ComparisonRow[] = await comparisonResponse.json();
      setComparison(
        comparisonRows.map((row, index) => ({
          name: row.profile,
          bytes: row.total_handshake,
          latency: row.latency_ms,
          color: profileButtons[index]?.color ?? "#2563eb",
        })),
      );

      const sshResponse = await fetch(`${API_BASE}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hostname: "localhost", port: 2222 }),
        signal: controller.signal,
      });
      setSshScan(await sshResponse.json());
    }
    loadTelemetry().catch((error) => {
      if (error.name !== "AbortError") console.error(error);
    });
    return () => controller.abort();
  }, []);

  React.useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/scan/live`);
    eventSource.addEventListener("scan", (event) => {
      try {
        const data: ScanResponse = JSON.parse(event.data);
        setLiveConnections((prev) => ({ ...prev, [data.endpoint]: data }));
      } catch {
        console.error("Failed to parse SSE event:", event.data);
      }
    });
    eventSource.onopen = () => setSseConnected(true);
    eventSource.onerror = () => setSseConnected(false);
    return () => {
      eventSource.close();
      setSseConnected(false);
    };
  }, []);

  const currentState = scan?.state ?? "S0_CLASSICAL";
  const activeIndex = ["S0_CLASSICAL", "S1_PQC_READY", "S2_HYBRID_KX", "S3_HYBRID_FULL", "S4_PQC_NATIVE"].indexOf(currentState);

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <h1>Post-Quantum Migration Control Plane</h1>
          <p>SMSM verification, HNDL scoring, handshake telemetry, and PQC readiness tracking.</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span className={`live-dot ${sseConnected ? "connected" : ""}`}>
            {sseConnected ? "LIVE" : "OFFLINE"}
          </span>
          <div className="status-pill">
            <ShieldCheck size={18} />
            {scan?.state_label ?? "Loading"}
          </div>
        </div>
      </header>

      <section className="toolbar">
        {profileButtons.map((profile) => (
          <button
            key={profile.port}
            className={selectedPort === profile.port ? "selected" : ""}
            onClick={() => setSelectedPort(profile.port)}
            title={`Scan port ${profile.port}`}
          >
            <Network size={16} />
            {profile.name}
          </button>
        ))}
      </section>

      <section className="kpis">
        <div className="panel">
          <div className="panel-title"><Activity size={18} /> Endpoint</div>
          <strong>{scan?.endpoint ?? "localhost"}</strong>
          <span>{scan?.evidence.negotiated_group ?? "Detecting group"}</span>
        </div>
        <div className="panel">
          <div className="panel-title"><Gauge size={18} /> Risk</div>
          <strong>{risk?.risk_band ?? "loading"}</strong>
          <span>{risk ? `${risk.risk_score.toFixed(3)} score` : "Computing"}</span>
        </div>
        <div className="panel">
          <div className="panel-title"><ShieldCheck size={18} /> Certificate</div>
          <strong>{scan?.evidence.certificate_algorithm ?? "Unknown"}</strong>
          <span>{scan ? `${scan.evidence.certificate_chain_bytes.toLocaleString()} bytes` : "Loading"}</span>
        </div>
        <div className="panel">
          <div className="panel-title"><GitBranch size={18} /> Handshake</div>
          <strong>{scan ? `${scan.evidence.handshake_bytes.toLocaleString()} bytes` : "Loading"}</strong>
          <span>{scan ? `${scan.evidence.latency_ms.toFixed(1)} ms` : "Measuring"}</span>
        </div>
        <div className="panel">
          <div className="panel-title"><Server size={18} /> SSH State</div>
          <strong>{sshScan?.state_label ?? "Loading"}</strong>
          <span>{sshScan?.evidence.negotiated_group ?? "Port 2222"}</span>
        </div>
      </section>

      <section className="grid">
        <div className="panel wide">
          <h2>Handshake Comparison</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={comparison}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="bytes" radius={[4, 4, 0, 0]}>
                {comparison.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>HNDL Risk Gauge</h2>
          <ResponsiveContainer width="100%" height={260}>
            <RadialBarChart innerRadius="55%" outerRadius="95%" data={[{ name: "risk", value: Math.min((risk?.risk_score ?? 0) * 8, 100), fill: "#dc2626" }]} startAngle={180} endAngle={0}>
              <RadialBar dataKey="value" cornerRadius={8} />
              <Tooltip />
            </RadialBarChart>
          </ResponsiveContainer>
          <p className="action">{risk?.recommended_action ?? "Loading recommendation."}</p>
        </div>

        <div className="panel wide">
          <h2>Migration State Machine</h2>
          <svg className="state-diagram" viewBox="0 0 700 150" role="img" aria-label="SMSM state diagram">
            {stateNodes.slice(0, -1).map((node, index) => (
              <line key={node.id} x1={node.x + 44} y1={node.y} x2={stateNodes[index + 1].x - 44} y2={node.y} />
            ))}
            {stateNodes.map((node, index) => (
              <g key={node.id}>
                <circle className={index <= activeIndex ? "active-node" : ""} cx={node.x} cy={node.y} r="39" />
                <text x={node.x} y={node.y - 4} textAnchor="middle">{node.id}</text>
                <text x={node.x} y={node.y + 15} textAnchor="middle">{node.label}</text>
              </g>
            ))}
          </svg>
        </div>

        <div className="panel">
          <h2>Risk Analysis</h2>
          <label>
            Data class
            <select value={dataClass} onChange={(event) => setDataClass(event.target.value as DataClass)}>
              <option value="public">Public</option>
              <option value="internal">Internal</option>
              <option value="confidential">Confidential</option>
              <option value="secret">Secret</option>
              <option value="top-secret">Top Secret</option>
            </select>
          </label>
          <label>
            Lifetime: {lifetime} years
            <input type="range" min="0" max="60" value={lifetime} onChange={(event) => setLifetime(Number(event.target.value))} />
          </label>
          <div className="metric-line">CRQC probability: {risk ? `${(risk.crqc_probability * 100).toFixed(1)}%` : "..."}</div>
          <div className="metric-line">Quantum level: {risk ? risk.quantum_security_level.toFixed(1) : "..."}</div>
        </div>

        <div className="panel wide">
          <h2>Latency Timeline</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={comparison}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="latency" stroke="#2563eb" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>Risk Timeline</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={riskTimeline}>
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Area dataKey="confidential" stroke="#2563eb" fill="#93c5fd" />
              <Area dataKey="secret" stroke="#dc2626" fill="#fecaca" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="panel full">
          <h2>Live Connection Evidence</h2>
          <table>
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>State</th>
                <th>Group</th>
                <th>Certificate</th>
                <th>Handshake</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {(Object.values(liveConnections).length ? Object.values(liveConnections) : scan ? [{
                endpoint: scan.endpoint,
                state: currentState,
                state_label: scan.state_label,
                evidence: scan.evidence,
                recommendations: scan.recommendations,
              }] : []).map((connection) => (
                <tr key={connection.endpoint}>
                  <td>{connection.endpoint}</td>
                  <td>{stateShort(connection.state)}</td>
                  <td>{connection.evidence.negotiated_group}</td>
                  <td>{connection.evidence.certificate_algorithm}</td>
                  <td>{connection.evidence.handshake_bytes.toLocaleString()} bytes</td>
                  <td>{connection.evidence.latency_ms.toFixed(1)} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
