import { useState, useRef, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './App.css';

const initialNodes =[
  { id: 'primary', position: { x: 250, y: 50 }, data: { label: ' Primary Agent' }, type: 'input' },
  { id: 'gremlin', position: { x: 550, y: 50 }, data: { label: ' Chaos StressTestAgent' }, type: 'input', style: { border: '1px solid #f43f5e' } },
  
  { id: 'interceptor', position: { x: 250, y: 150 }, data: { label: ' FastMCP Interceptor' } },
  { id: 'engine', position: { x: 250, y: 250 }, data: { label: ' A2A Event Bus' } },
  
  { id: 'cache', position: { x: 250, y: 350 }, data: { label: ' Async Cache Check' } },
  { id: 'llm', position: { x: 500, y: 350 }, data: { label: ' Local Ollama LLM' } },
  
  { id: 'transform', position: { x: 250, y: 450 }, data: { label: ' Apply Transformations' } },
  
  { id: 'security', position: { x: 250, y: 550 }, data: { label: ' SecurityValidationAgent' } },
  
  { id: 'reexecute', position: { x: 250, y: 650 }, data: { label: ' Re-Execute API' } },
  { id: 'patcher', position: { x: 500, y: 650 }, data: { label: ' ASTPatchingAgent' }, type: 'output' },
];

const initialEdges =[
  { id: 'e-prim-int', source: 'primary', target: 'interceptor', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e-grem-int', source: 'gremlin', target: 'interceptor', markerEnd: { type: MarkerType.ArrowClosed } },
  
  { id: 'e-int-eng', source: 'interceptor', target: 'engine', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e-eng-cache', source: 'engine', target: 'cache', markerEnd: { type: MarkerType.ArrowClosed } },
  
  { id: 'e-cache-llm', source: 'cache', target: 'llm', label: 'Miss', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e-cache-trans', source: 'cache', target: 'transform', label: 'Hit', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e-llm-trans', source: 'llm', target: 'transform', markerEnd: { type: MarkerType.ArrowClosed } },
  
  { id: 'e-trans-sec', source: 'transform', target: 'security', markerEnd: { type: MarkerType.ArrowClosed } },
  
  { id: 'e-sec-re', source: 'security', target: 'reexecute', label: 'Safe', markerEnd: { type: MarkerType.ArrowClosed } },
  
  { id: 'e-re-prim', source: 'reexecute', target: 'primary', label: '200 OK', type: 'step', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e-re-patch', source: 'reexecute', target: 'patcher', label: 'on_success', markerEnd: { type: MarkerType.ArrowClosed } },
];

function App() {
  const[logs, setLogs] = useState([]);
  const[wsStatus, setWsStatus] = useState('connecting');
  
  const[nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const[edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  const terminalEndRef = useRef(null);
  const ws = useRef(null);

  // Live KPI Metrics
  const [metrics, setMetrics] = useState({
    errorsPrevented: 0,
    cacheHits: 0,
    llmInferences: 0
  });
  
  // Create an event queue so fast backend events are animated beautifully one-by-one
  const eventQueue = useRef([]);
  const isAnimating = useRef(false);
  const isIntentionalClose = useRef(false);

  useEffect(() => {
    isIntentionalClose.current = false;
    connectWebSocket();
    return () => {
      isIntentionalClose.current = true;
      if (ws.current) ws.current.close();
    };
  },[]);

  const connectWebSocket = () => {
    setWsStatus('connecting');
    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onopen = () => {
      setWsStatus('connected');
      addLog(' Connected to AutoHeal Telemetry Stream', 'success');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      eventQueue.current.push(data);
      processQueue();
    };

    ws.current.onclose = () => {
      if (isIntentionalClose.current) return;
      setWsStatus('offline');
      addLog(' SYSTEM OFFLINE: Backend Server Unreachable', 'error');
      setTimeout(connectWebSocket, 5000);
    };

    ws.current.onerror = () => {
      setWsStatus('offline');
    };
  };

  const processQueue = () => {
    if (isAnimating.current || eventQueue.current.length === 0) return;
    
    isAnimating.current = true;
    const data = eventQueue.current.shift();
    
    // 1. Add the log to the terminal instantly
    addLog(data.msg, data.type);

    // Update KPI Metrics based on telemetry content
    if (data.msg.includes("[400 CAUGHT]")) {
      setMetrics(m => ({ ...m, errorsPrevented: m.errorsPrevented + 1 }));
    } else if (data.msg.includes("[CACHE HIT]")) {
      setMetrics(m => ({ ...m, cacheHits: m.cacheHits + 1 }));
    } else if (data.msg.includes("[INFERENCE START]")) {
      setMetrics(m => ({ ...m, llmInferences: m.llmInferences + 1 }));
    }
    
    // 2. Animate the node graph if a node was specified
    if (data.node) {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === data.node) {
            return { ...n, style: { ...n.style, background: 'rgba(0, 240, 255, 0.2)', border: '2px solid #00f0ff', boxShadow: '0 0 20px rgba(0,240,255,0.4)', color: '#fff' } };
          }
          // Reset other nodes to default
          return { ...n, style: { ...n.style, background: '#1e293b', border: '1px solid #334155', boxShadow: 'none', color: '#f8fafc' } };
        })
      );
      
      setEdges((eds) =>
        eds.map((e) => {
          // Highlight edge flowing into or out of the active node
          if (e.target === data.node || e.source === data.node) {
            return { ...e, animated: true, style: { stroke: '#00f0ff', strokeWidth: 3 } };
          }
          return { ...e, animated: false, style: { stroke: '#475569', strokeWidth: 1 } };
        })
      );

      // Wait 800ms for the animation to play out before processing the next event
      setTimeout(() => {
        // Reset everything
        setNodes((nds) => nds.map((n) => ({ ...n, style: { ...n.style, background: '#1e293b', border: '1px solid #334155', boxShadow: 'none' } })));
        setEdges((eds) => eds.map((e) => ({ ...e, animated: false, style: { stroke: '#475569', strokeWidth: 1 } })));
        
        isAnimating.current = false;
        processQueue();
      }, 800);
    } else {
      // If no node mapping, instantly move to next
      isAnimating.current = false;
      processQueue();
    }
  };

  const addLog = (msg, type = 'info') => {
    setLogs(prev =>[...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
  };

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  },[logs]);

  const handleRunAgent = async () => {
    try {
      await fetch('http://localhost:8000/api/run_agent', { method: 'POST' });
    } catch (err) {
      addLog(`Failed to connect to backend: ${err.message}`, "error");
    }
  };

  const handleRunGremlin = async () => {
    try {
      await fetch('http://localhost:8000/api/run_stress_test', { method: 'POST' });
    } catch (err) {
      addLog(`Failed to connect to backend: ${err.message}`, "error");
    }
  };

  return (
    <div className="app-container">
      {wsStatus === 'offline' && (
        <div style={{ background: '#f43f5e', color: 'white', padding: '0.5rem', textAlign: 'center', fontWeight: 'bold', borderRadius: '8px' }}>
           BACKEND OFFLINE. Please start the FastAPI Server.
        </div>
      )}

      <header className="header">
        <h1>Enterprise Neural Control Plane</h1>
        <p>Live Multi-Agent AutoHeal Telemetry</p>
        <div className="metrics-dashboard" style={{ display: 'flex', gap: '2rem', justifyContent: 'center', marginTop: '1rem' }}>
          <div className="metric-card" style={{ background: '#1e293b', padding: '10px 20px', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Errors Prevented</div>
            <div style={{ color: '#f43f5e', fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.errorsPrevented}</div>
          </div>
          <div className="metric-card" style={{ background: '#1e293b', padding: '10px 20px', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Cache Hits (0ms)</div>
            <div style={{ color: '#22c55e', fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.cacheHits}</div>
          </div>
          <div className="metric-card" style={{ background: '#1e293b', padding: '10px 20px', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>LLM Inferences</div>
            <div style={{ color: '#a855f7', fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.llmInferences}</div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <section className="glass-panel left-panel">
          <div className="panel-title"> Command Center</div>
          
          <div className="controls">
            <button className="btn btn-primary" onClick={handleRunAgent} disabled={wsStatus !== 'connected'}>
              Run Primary Agent
            </button>
            <button className="btn btn-danger" onClick={handleRunGremlin} disabled={wsStatus !== 'connected'}>
              Run Chaos Test
            </button>
          </div>

          <div className="panel-title" style={{marginTop: '1rem'}}> Live Telemetry Stream</div>
          <div className="terminal">
            {logs.map((log, i) => (
              <div key={i} className="log-entry">
                <span className="log-time">[{log.time}]</span>
                <span className={`log-msg ${log.type}`}>{log.msg}</span>
              </div>
            ))}
            {logs.length === 0 && <div style={{color: '#666'}}>Awaiting telemetry stream...</div>}
            <div ref={terminalEndRef} />
          </div>
        </section>

        <section className="glass-panel right-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-right"
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#334155" gap={20} />
            <Controls style={{ background: '#1e293b', fill: '#fff' }} />
          </ReactFlow>
        </section>
      </main>
    </div>
  );
}

export default App;
