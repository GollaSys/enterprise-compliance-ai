/**
 * AgentDemo — Live Agent Pipeline Demo page.
 *
 * Shows the 5-agent LangGraph pipeline running in real time via SSE.
 * Displays: agent status pipeline, A2A task log, memory events, trace links.
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  Link,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  AccountTree as GraphIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Memory as MemoryIcon,
  OpenInNew as OpenInNewIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  Stop as StopIcon,
  Sync as RunningIcon,
} from '@mui/icons-material';

import { useAgentStream, AgentStatus } from '../hooks/useAgentStream';

const AGENT_LABELS: Record<string, string> = {
  regulatory_analyst: 'Regulatory Analyst',
  policy_mapper: 'Policy Mapper',
  evidence_validator: 'Evidence Validator',
  risk_scorer: 'Risk Scorer',
  executive_reporter: 'Executive Reporter',
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
  regulatory_analyst: 'RAG + MCP filesystem/GitHub → extracts GDPR requirements',
  policy_mapper: 'Maps requirements to policies → identifies gaps via A2A',
  evidence_validator: 'Validates evidence + queries mem0 long-term memory',
  risk_scorer: 'Scores risks (impact × likelihood) + writes findings to mem0',
  executive_reporter: 'Generates board-ready report + emits LangSmith/Langfuse links',
};

function StatusIcon({ status }: { status: AgentStatus }) {
  switch (status) {
    case 'running':
      return <RunningIcon fontSize="small" sx={{ color: 'warning.main', animation: 'spin 1s linear infinite' }} />;
    case 'completed':
      return <CheckIcon fontSize="small" sx={{ color: 'success.main' }} />;
    case 'error':
      return <ErrorIcon fontSize="small" sx={{ color: 'error.main' }} />;
    default:
      return <PendingIcon fontSize="small" sx={{ color: 'text.disabled' }} />;
  }
}

function AgentCard({ name, status }: { name: string; status: AgentStatus }) {
  const isActive = status === 'running';
  const isDone = status === 'completed';
  const isError = status === 'error';

  return (
    <Card
      variant="outlined"
      sx={{
        borderColor: isActive ? 'warning.main' : isDone ? 'success.main' : isError ? 'error.main' : 'divider',
        bgcolor: isActive ? 'warning.main' : isDone ? 'success.main' : 'background.paper',
        opacity: isDone ? 0.95 : 1,
        transition: 'all 0.3s ease',
        '& .MuiCardContent-root': { p: '10px 14px !important' },
      }}
    >
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1}>
          <StatusIcon status={status} />
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="body2" fontWeight={600} sx={{ color: (isActive || isDone) ? 'white' : 'text.primary' }}>
              {AGENT_LABELS[name]}
            </Typography>
            <Typography variant="caption" sx={{ color: (isActive || isDone) ? 'rgba(255,255,255,0.8)' : 'text.secondary' }} noWrap>
              {AGENT_DESCRIPTIONS[name]}
            </Typography>
          </Box>
          <Chip
            label={status}
            size="small"
            sx={{
              fontSize: '10px',
              height: 20,
              bgcolor: isActive ? 'rgba(255,255,255,0.2)' : isDone ? 'rgba(255,255,255,0.2)' : undefined,
              color: (isActive || isDone) ? 'white' : undefined,
            }}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function AgentDemo() {
  const [regulationType, setRegulationType] = useState('GDPR');
  const [documentPath, setDocumentPath] = useState('');

  const { isRunning, runId, events, agentStatuses, traceUrls, error, start, stop } =
    useAgentStream();

  const handleRun = () => {
    start({ regulationType, documentPath: documentPath || undefined });
  };

  const memoryEvents = events.filter(
    (e) => (e.memory_hits && e.memory_hits > 0) || (e.memory_writes && e.memory_writes > 0)
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={2} mb={3}>
        <GraphIcon sx={{ fontSize: 32, color: 'primary.main' }} />
        <Box>
          <Typography variant="h5" fontWeight={700}>
            Live Agent Demo
          </Typography>
          <Typography variant="body2" color="text.secondary">
            LangGraph · A2A Protocol · MCP · mem0 · Langfuse
          </Typography>
        </Box>
        {runId && (
          <Chip label={`run: ${runId}`} size="small" sx={{ ml: 'auto', fontFamily: 'monospace' }} />
        )}
      </Stack>

      <Grid container spacing={3}>
        {/* Left column: controls + pipeline */}
        <Grid item xs={12} md={5}>
          {/* Controls */}
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight={600} mb={2}>
                Run Configuration
              </Typography>
              <Stack spacing={2}>
                <FormControl size="small" fullWidth>
                  <InputLabel>Regulation</InputLabel>
                  <Select
                    value={regulationType}
                    label="Regulation"
                    onChange={(e) => setRegulationType(e.target.value)}
                    disabled={isRunning}
                  >
                    <MenuItem value="GDPR">GDPR</MenuItem>
                    <MenuItem value="SOX">SOX</MenuItem>
                    <MenuItem value="FINRA">FINRA</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  label="Document path (optional)"
                  placeholder="Leave blank to use seeded GDPR sample"
                  value={documentPath}
                  onChange={(e) => setDocumentPath(e.target.value)}
                  disabled={isRunning}
                  helperText="Leave blank → uses data/samples/gdpr_policy_sample.txt"
                />
                <Stack direction="row" spacing={1}>
                  <Button
                    variant="contained"
                    startIcon={isRunning ? <CircularProgress size={16} sx={{ color: 'white' }} /> : <PlayIcon />}
                    onClick={handleRun}
                    disabled={isRunning}
                    fullWidth
                  >
                    {isRunning ? 'Running...' : 'Run with sample GDPR doc'}
                  </Button>
                  {isRunning && (
                    <Button variant="outlined" color="error" onClick={stop} startIcon={<StopIcon />}>
                      Stop
                    </Button>
                  )}
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          {/* Pipeline status */}
          <Typography variant="subtitle2" fontWeight={600} mb={1}>
            Agent Pipeline
          </Typography>
          <Stack spacing={1}>
            {Object.entries(AGENT_LABELS).map(([name]) => (
              <AgentCard key={name} name={name} status={agentStatuses[name] || 'pending'} />
            ))}
          </Stack>

          {/* Trace links */}
          {(traceUrls.langsmith || traceUrls.langfuse) && (
            <Card variant="outlined" sx={{ mt: 2, borderColor: 'primary.main' }}>
              <CardContent sx={{ pb: '12px !important' }}>
                <Typography variant="subtitle2" fontWeight={600} mb={1}>
                  Observability Traces
                </Typography>
                <Stack spacing={0.5}>
                  {traceUrls.langsmith && (
                    <Link href={traceUrls.langsmith} target="_blank" rel="noopener" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: 13 }}>
                      <OpenInNewIcon fontSize="inherit" /> LangSmith trace
                    </Link>
                  )}
                  {traceUrls.langfuse && (
                    <Link href={traceUrls.langfuse} target="_blank" rel="noopener" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: 13 }}>
                      <OpenInNewIcon fontSize="inherit" /> Langfuse trace (localhost:3001)
                    </Link>
                  )}
                </Stack>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Right column: A2A event log + memory */}
        <Grid item xs={12} md={7}>
          {/* Error */}
          {error && (
            <Card variant="outlined" sx={{ mb: 2, borderColor: 'error.main' }}>
              <CardContent>
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* A2A event log */}
          <Typography variant="subtitle2" fontWeight={600} mb={1}>
            A2A Event Log
          </Typography>
          <Card
            variant="outlined"
            sx={{ mb: 2, minHeight: 200, maxHeight: 320, overflow: 'auto', bgcolor: 'grey.900' }}
          >
            <CardContent sx={{ p: '12px !important' }}>
              {events.length === 0 ? (
                <Typography variant="caption" color="text.secondary">
                  Waiting for agent messages…
                </Typography>
              ) : (
                <Stack spacing={0.5}>
                  {events.map((ev, i) => (
                    <Box key={i} sx={{ fontFamily: 'monospace', fontSize: 12, color: 'grey.100' }}>
                      <span style={{ color: '#6b7280' }}>
                        [{ev.agent}]
                      </span>{' '}
                      <span style={{ color: ev.status === 'completed' ? '#6ee7b7' : ev.status === 'error' ? '#f87171' : '#fbbf24' }}>
                        {ev.status}
                      </span>
                      {ev.summary && (
                        <span style={{ color: '#94a3b8' }}> — {ev.summary}</span>
                      )}
                      {ev.task_id && (
                        <span style={{ color: '#64748b' }}> ({ev.task_id})</span>
                      )}
                    </Box>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>

          {/* Memory events */}
          <Stack direction="row" alignItems="center" spacing={1} mb={1}>
            <MemoryIcon fontSize="small" sx={{ color: 'secondary.main' }} />
            <Typography variant="subtitle2" fontWeight={600}>
              Memory Events
            </Typography>
          </Stack>
          <Card variant="outlined" sx={{ minHeight: 100, maxHeight: 180, overflow: 'auto' }}>
            <CardContent sx={{ p: '12px !important' }}>
              {memoryEvents.length === 0 ? (
                <Typography variant="caption" color="text.secondary">
                  {isRunning ? 'Watching for mem0 activity…' : 'No memory events yet. Run the pipeline to see long-term memory in action.'}
                </Typography>
              ) : (
                <Stack spacing={0.5}>
                  {memoryEvents.map((ev, i) => (
                    <Box key={i} sx={{ fontSize: 12 }}>
                      {ev.memory_hits ? (
                        <Typography variant="caption" color="warning.main">
                          🧠 <strong>{ev.agent}</strong>: {ev.memory_hits} prior finding(s) loaded from mem0
                        </Typography>
                      ) : null}
                      {ev.memory_writes ? (
                        <Typography variant="caption" color="secondary.main">
                          💾 <strong>{ev.agent}</strong>: stored {ev.memory_writes} finding(s) to mem0 for future runs
                        </Typography>
                      ) : null}
                    </Box>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>

          {/* Demo tips */}
          <Card variant="outlined" sx={{ mt: 2, borderColor: 'divider' }}>
            <CardContent sx={{ pb: '12px !important' }}>
              <Typography variant="caption" color="text.secondary" component="div">
                <strong>Demo tip:</strong> Run twice to see long-term memory in action —
                the 2nd run shows "prior findings loaded" in the Evidence Validator.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
