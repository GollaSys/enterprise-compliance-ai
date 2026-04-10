/**
 * useAgentStream — EventSource SSE hook for the compliance demo pipeline.
 *
 * Connects to GET /api/v2/demo/stream and delivers real-time agent events
 * as the LangGraph pipeline progresses.
 */
import { useCallback, useRef, useState } from 'react';

export type AgentStatus = 'pending' | 'running' | 'completed' | 'error';

export interface AgentEvent {
  type: string;
  agent: string;
  status: AgentStatus;
  task_id?: string;
  summary?: string;
  memory_hits?: number;
  memory_writes?: number;
  trace_urls?: { langsmith: string; langfuse: string };
  error?: string;
  run_id?: string;
}

export interface AgentStreamState {
  isRunning: boolean;
  runId: string | null;
  events: AgentEvent[];
  agentStatuses: Record<string, AgentStatus>;
  traceUrls: { langsmith: string; langfuse: string };
  error: string | null;
  start: (params: { regulationType: string; documentPath?: string }) => void;
  stop: () => void;
}

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const AGENT_NAMES = [
  'regulatory_analyst',
  'policy_mapper',
  'evidence_validator',
  'risk_scorer',
  'executive_reporter',
];

export function useAgentStream(): AgentStreamState {
  const [isRunning, setIsRunning] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>(
    () => Object.fromEntries(AGENT_NAMES.map((n) => [n, 'pending']))
  );
  const [traceUrls, setTraceUrls] = useState({ langsmith: '', langfuse: '' });
  const [error, setError] = useState<string | null>(null);

  const esRef = useRef<EventSource | null>(null);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setIsRunning(false);
  }, []);

  const start = useCallback(
    ({ regulationType, documentPath }: { regulationType: string; documentPath?: string }) => {
      // Reset state
      setEvents([]);
      setError(null);
      setRunId(null);
      setTraceUrls({ langsmith: '', langfuse: '' });
      setAgentStatuses(Object.fromEntries(AGENT_NAMES.map((n) => [n, 'pending'])));
      esRef.current?.close();

      const params = new URLSearchParams({ regulation_type: regulationType });
      if (documentPath) params.set('document_path', documentPath);

      const url = `${API_BASE}/api/v2/demo/stream?${params}`;
      const es = new EventSource(url);
      esRef.current = es;
      setIsRunning(true);

      es.addEventListener('start', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          setRunId(data.run_id);
        } catch {}
      });

      es.addEventListener('agent_update', (e: MessageEvent) => {
        try {
          const event: AgentEvent = JSON.parse(e.data);
          setEvents((prev) => [...prev, event]);
          if (event.agent) {
            setAgentStatuses((prev) => ({ ...prev, [event.agent]: event.status }));
          }
        } catch {}
      });

      es.addEventListener('run_complete', (e: MessageEvent) => {
        try {
          const event: AgentEvent = JSON.parse(e.data);
          setEvents((prev) => [...prev, event]);
          if (event.agent) {
            setAgentStatuses((prev) => ({ ...prev, [event.agent]: 'completed' }));
          }
          if (event.trace_urls) {
            setTraceUrls(event.trace_urls);
          }
        } catch {}
      });

      es.addEventListener('done', () => {
        es.close();
        setIsRunning(false);
      });

      es.addEventListener('error', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          setError(data.error || 'Stream error');
        } catch {
          setError('Connection error');
        }
        es.close();
        setIsRunning(false);
      });

      es.onerror = () => {
        if (es.readyState === EventSource.CLOSED) {
          setIsRunning(false);
        }
      };
    },
    []
  );

  return { isRunning, runId, events, agentStatuses, traceUrls, error, start, stop };
}
