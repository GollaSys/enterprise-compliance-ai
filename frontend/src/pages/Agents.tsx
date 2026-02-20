import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Paper,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Search,
  AccountTree,
  VerifiedUser,
  Assessment,
  Summarize,
  ExpandMore,
  ExpandLess,
  CheckCircle,
  ArrowForward,
  SmartToy,
  Speed,
  TaskAlt,
  Timer,
  Group,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { agentsAPI, documentsAPI } from '../services/api';

const AGENT_ICONS: Record<string, React.ReactNode> = {
  search: <Search />,
  account_tree: <AccountTree />,
  verified_user: <VerifiedUser />,
  assessment: <Assessment />,
  summarize: <Summarize />,
};

const AGENT_COLORS: Record<string, string> = {
  regulatory_analyst: '#1976d2',
  policy_mapper: '#7b1fa2',
  evidence_validator: '#388e3c',
  risk_scorer: '#f57c00',
  executive_reporter: '#c62828',
};

const BAR_COLORS = ['#1976d2', '#7b1fa2', '#388e3c', '#f57c00', '#c62828'];

interface TimelineStep {
  order: number;
  agent_id: string;
  agent_name: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration: number;
  output_snippet: string;
}

// --- Pipeline Node ---
const PipelineNode = ({
  agent,
  isActive,
  isCompleted,
  isIdle,
}: {
  agent: any;
  isActive: boolean;
  isCompleted: boolean;
  isIdle: boolean;
}) => {
  const color = AGENT_COLORS[agent.id] || '#1976d2';
  const icon = AGENT_ICONS[agent.icon] || <SmartToy />;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
        minWidth: 140,
      }}
    >
      <Box
        sx={{
          width: 80,
          height: 80,
          borderRadius: 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: isActive
            ? `3px solid ${color}`
            : isCompleted
            ? '3px solid #4caf50'
            : '2px solid #e0e0e0',
          background: isActive
            ? `linear-gradient(135deg, ${color}15 0%, ${color}30 100%)`
            : isCompleted
            ? 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)'
            : '#fafafa',
          transition: 'all 0.4s ease',
          animation: isActive ? 'agentPulse 1.5s infinite' : 'none',
          '@keyframes agentPulse': {
            '0%': { boxShadow: `0 0 0 0 ${color}66` },
            '70%': { boxShadow: `0 0 0 12px ${color}00` },
            '100%': { boxShadow: `0 0 0 0 ${color}00` },
          },
        }}
      >
        {isActive ? (
          <CircularProgress size={28} sx={{ color: color }} />
        ) : isCompleted ? (
          <CheckCircle sx={{ fontSize: 32, color: '#4caf50' }} />
        ) : (
          <Box sx={{ color: color, display: 'flex' }}>
            {React.cloneElement(icon as React.ReactElement, { sx: { fontSize: 32 } })}
          </Box>
        )}
      </Box>
      <Typography
        variant="caption"
        sx={{
          mt: 1,
          fontWeight: isActive ? 700 : 500,
          color: isActive ? color : isCompleted ? '#4caf50' : 'text.secondary',
          textAlign: 'center',
          fontSize: '0.75rem',
          maxWidth: 120,
        }}
      >
        {agent.name}
      </Typography>
      {isActive && (
        <Chip
          label="Processing..."
          size="small"
          sx={{
            mt: 0.5,
            height: 20,
            fontSize: '0.65rem',
            bgcolor: `${color}20`,
            color: color,
            fontWeight: 600,
          }}
        />
      )}
      {isCompleted && (
        <Chip
          label="Done"
          size="small"
          sx={{
            mt: 0.5,
            height: 20,
            fontSize: '0.65rem',
            bgcolor: '#e8f5e9',
            color: '#388e3c',
            fontWeight: 600,
          }}
        />
      )}
    </Box>
  );
};

// --- Pipeline Arrow ---
const PipelineArrow = ({ label, isActive }: { label: string; isActive: boolean }) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      mx: { xs: 0, md: 0.5 },
      my: { xs: 1, md: 0 },
    }}
  >
    <Box
      sx={{
        display: { xs: 'none', md: 'flex' },
        alignItems: 'center',
        gap: 0,
      }}
    >
      <Box
        sx={{
          width: 40,
          height: 2,
          bgcolor: isActive ? '#1976d2' : '#e0e0e0',
          transition: 'background-color 0.4s ease',
        }}
      />
      <ArrowForward
        sx={{
          fontSize: 18,
          color: isActive ? '#1976d2' : '#bdbdbd',
          transition: 'color 0.4s ease',
        }}
      />
    </Box>
    <Typography
      variant="caption"
      sx={{
        fontSize: '0.6rem',
        color: isActive ? 'primary.main' : 'text.disabled',
        textAlign: 'center',
        maxWidth: 80,
        mt: 0.5,
        lineHeight: 1.2,
        display: { xs: 'none', lg: 'block' },
      }}
    >
      {label}
    </Typography>
  </Box>
);

// --- Stat Card ---
const MetricCard = ({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography color="text.secondary" variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
            {title}
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            background: `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {React.cloneElement(icon as React.ReactElement, { sx: { color, fontSize: 24 } })}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

// --- Main Agents Page ---
const Agents: React.FC = () => {
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [selectedRegulation, setSelectedRegulation] = useState('GDPR');
  const [selectedDocument, setSelectedDocument] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState<TimelineStep[]>([]);
  const [demoTimeline, setDemoTimeline] = useState<TimelineStep[]>([]);
  const [totalDuration, setTotalDuration] = useState(0);
  const logEndRef = useRef<HTMLDivElement>(null);
  const { enqueueSnackbar } = useSnackbar();

  const { data: detailsData, isLoading: detailsLoading } = useQuery({
    queryKey: ['agents-details'],
    queryFn: () => agentsAPI.getDetails().then((res) => res.data),
  });

  const { data: orchestrationData } = useQuery({
    queryKey: ['agents-orchestration'],
    queryFn: () => agentsAPI.getOrchestration().then((res) => res.data),
  });

  const { data: metricsData } = useQuery({
    queryKey: ['agents-metrics'],
    queryFn: () => agentsAPI.getMetrics().then((res) => res.data),
  });

  const { data: documentsData } = useQuery({
    queryKey: ['documents-for-demo'],
    queryFn: () => documentsAPI.list().then((res) => res.data),
  });

  const uploadedDocs = documentsData?.documents || [];

  const runMutation = useMutation({
    mutationFn: (params: { regulation_type: string; document_id?: string }) => agentsAPI.startRun(params),
    onSuccess: async (res) => {
      const runId = res.data.run_id;
      const timelineRes = await agentsAPI.getTimeline(runId);
      const timeline = timelineRes.data;
      setDemoTimeline(timeline.steps);
      setTotalDuration(timeline.total_duration);
      setCurrentStep(0);
      setIsRunning(true);
      setCompletedSteps([]);
    },
    onError: () => {
      enqueueSnackbar('Failed to start orchestration demo.', { variant: 'error' });
    },
  });

  const advanceStep = useCallback(() => {
    setCurrentStep((prev) => {
      const nextStep = prev + 1;
      if (prev >= 0 && prev < demoTimeline.length) {
        setCompletedSteps((cs) => [...cs, demoTimeline[prev]]);
      }
      if (nextStep >= demoTimeline.length) {
        setIsRunning(false);
        enqueueSnackbar('Orchestration pipeline completed successfully!', { variant: 'success' });
        return nextStep;
      }
      return nextStep;
    });
  }, [demoTimeline, enqueueSnackbar]);

  useEffect(() => {
    if (!isRunning || currentStep < 0 || currentStep >= demoTimeline.length) return;
    const delay = (demoTimeline[currentStep]?.duration || 3) * 1000;
    const timer = setTimeout(advanceStep, delay);
    return () => clearTimeout(timer);
  }, [isRunning, currentStep, demoTimeline, advanceStep]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [completedSteps]);

  const handleRunDemo = () => {
    setCurrentStep(-1);
    setCompletedSteps([]);
    setDemoTimeline([]);
    setTotalDuration(0);
    runMutation.mutate({
      regulation_type: selectedRegulation,
      ...(selectedDocument ? { document_id: selectedDocument } : {}),
    });
  };

  const agents = detailsData?.agents || [];
  const connections = orchestrationData?.connections || [];
  const metrics = metricsData;
  const perAgent = metrics?.per_agent || [];

  const chartData = perAgent.map((a: any) => ({
    name: a.name.split(' ')[0],
    tasks: a.tasks,
    avgTime: a.avg_time,
  }));

  if (detailsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  const demoFinished = currentStep >= demoTimeline.length && demoTimeline.length > 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          AI Agent Orchestration
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Visualize how CrewAI agents collaborate in a sequential pipeline to automate compliance analysis
        </Typography>
      </Box>

      {/* Section A: Pipeline Visualization */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Agent Pipeline
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sequential orchestration — data flows left to right through 5 specialized agents
              </Typography>
            </Box>
            <Chip
              label={orchestrationData?.pipeline_type?.toUpperCase() || 'SEQUENTIAL'}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: { xs: 'column', md: 'row' },
              gap: { xs: 0, md: 0 },
              py: 2,
              overflowX: 'auto',
            }}
          >
            {agents.map((agent: any, idx: number) => (
              <React.Fragment key={agent.id}>
                <PipelineNode
                  agent={agent}
                  isActive={isRunning && currentStep === idx}
                  isCompleted={currentStep > idx}
                  isIdle={!isRunning && currentStep <= idx}
                />
                {idx < agents.length - 1 && (
                  <PipelineArrow
                    label={connections[idx]?.data_label || ''}
                    isActive={currentStep > idx}
                  />
                )}
              </React.Fragment>
            ))}
          </Box>

          {demoFinished && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Pipeline completed in {totalDuration}s — all 5 agents executed successfully for {selectedRegulation} analysis
              {selectedDocument ? ` on "${uploadedDocs.find((d: any) => d.id === selectedDocument)?.filename}"` : ''}.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Section C: Live Orchestration Demo */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Live Orchestration Demo
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select a regulation and an uploaded document, then run the agent pipeline in real-time
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Regulation</InputLabel>
              <Select
                value={selectedRegulation}
                onChange={(e) => setSelectedRegulation(e.target.value)}
                label="Regulation"
                disabled={isRunning}
              >
                <MenuItem value="GDPR">GDPR</MenuItem>
                <MenuItem value="SOX">SOX</MenuItem>
                <MenuItem value="FINRA">FINRA</MenuItem>
                <MenuItem value="SEC">SEC</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 260 }}>
              <InputLabel>Document</InputLabel>
              <Select
                value={selectedDocument}
                onChange={(e) => setSelectedDocument(e.target.value)}
                label="Document"
                disabled={isRunning}
              >
                {uploadedDocs.length === 0 ? (
                  <MenuItem disabled value="">
                    No documents uploaded yet
                  </MenuItem>
                ) : (
                  uploadedDocs.map((doc: any) => (
                    <MenuItem key={doc.id} value={doc.id}>
                      {doc.filename}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={isRunning ? <CircularProgress size={18} color="inherit" /> : <PlayArrow />}
              onClick={handleRunDemo}
              disabled={isRunning || runMutation.isPending || !selectedDocument}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5a6fd6 0%, #6a4196 100%)',
                },
              }}
            >
              {isRunning ? 'Running Pipeline...' : 'Run Demo'}
            </Button>
          </Box>

          {uploadedDocs.length === 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Upload a document on the Documents page first to run the agent pipeline.
            </Alert>
          )}

          {isRunning && (
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  Step {Math.min(currentStep + 1, 5)} of 5 — {demoTimeline[currentStep]?.agent_name || 'Completing...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {Math.round(((currentStep + 1) / 5) * 100)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={((currentStep + 1) / 5) * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    background: 'linear-gradient(90deg, #667eea, #764ba2)',
                    borderRadius: 4,
                  },
                }}
              />
            </Box>
          )}

          {/* Activity Log */}
          {(completedSteps.length > 0 || isRunning) && (
            <Paper
              variant="outlined"
              sx={{
                maxHeight: 320,
                overflow: 'auto',
                bgcolor: '#fafafa',
                p: 0,
              }}
            >
              <List dense sx={{ py: 0 }}>
                {completedSteps.map((step, idx) => {
                  const color = AGENT_COLORS[step.agent_id] || '#1976d2';
                  const icon = AGENT_ICONS[
                    agents.find((a: any) => a.id === step.agent_id)?.icon || 'search'
                  ] || <SmartToy />;
                  return (
                    <React.Fragment key={step.order}>
                      <ListItem
                        sx={{
                          alignItems: 'flex-start',
                          animation: 'fadeInUp 0.3s ease-out',
                          '@keyframes fadeInUp': {
                            from: { opacity: 0, transform: 'translateY(10px)' },
                            to: { opacity: 1, transform: 'translateY(0)' },
                          },
                        }}
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: color, width: 36, height: 36 }}>
                            {React.cloneElement(icon as React.ReactElement, {
                              sx: { fontSize: 18 },
                            })}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {step.agent_name}
                              </Typography>
                              <Chip
                                label={`${step.duration}s`}
                                size="small"
                                sx={{
                                  height: 20,
                                  fontSize: '0.65rem',
                                  bgcolor: `${color}15`,
                                  color: color,
                                }}
                              />
                              <CheckCircle sx={{ fontSize: 16, color: '#4caf50' }} />
                            </Box>
                          }
                          secondary={
                            <Typography
                              variant="body2"
                              sx={{ color: 'text.secondary', fontSize: '0.8rem', lineHeight: 1.5 }}
                            >
                              {step.output_snippet}
                            </Typography>
                          }
                        />
                      </ListItem>
                      {idx < completedSteps.length - 1 && <Divider variant="inset" component="li" />}
                    </React.Fragment>
                  );
                })}
                {isRunning && currentStep < demoTimeline.length && (
                  <ListItem sx={{ alignItems: 'center' }}>
                    <ListItemAvatar>
                      <Avatar
                        sx={{
                          bgcolor:
                            AGENT_COLORS[demoTimeline[currentStep]?.agent_id] || '#1976d2',
                          width: 36,
                          height: 36,
                        }}
                      >
                        <CircularProgress size={18} sx={{ color: 'white' }} />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {demoTimeline[currentStep]?.agent_name} is processing...
                        </Typography>
                      }
                    />
                  </ListItem>
                )}
              </List>
              <div ref={logEndRef} />
            </Paper>
          )}
        </CardContent>
      </Card>

      {/* Section B: Agent Detail Cards */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
        Agent Details
      </Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {agents.map((agent: any) => {
          const color = AGENT_COLORS[agent.id] || '#1976d2';
          const icon = AGENT_ICONS[agent.icon] || <SmartToy />;
          const isExpanded = expandedAgent === agent.id;
          return (
            <Grid item xs={12} sm={6} md={4} key={agent.id}>
              <Card
                sx={{
                  height: '100%',
                  borderTop: `3px solid ${color}`,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: `${color}20`,
                        color: color,
                        width: 44,
                        height: 44,
                      }}
                    >
                      {icon}
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, lineHeight: 1.3 }}>
                        {agent.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {agent.role}
                      </Typography>
                    </Box>
                    <Chip
                      label={agent.status}
                      size="small"
                      sx={{
                        bgcolor: agent.status === 'active' ? '#e8f5e9' : '#fff3e0',
                        color: agent.status === 'active' ? '#388e3c' : '#f57c00',
                        fontWeight: 600,
                        fontSize: '0.7rem',
                      }}
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontSize: '0.8rem' }}>
                    {agent.goal}
                  </Typography>

                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                    {agent.tools.map((tool: any) => (
                      <Chip
                        key={tool.name}
                        label={tool.name.replace(/_/g, ' ')}
                        size="small"
                        variant="outlined"
                        sx={{
                          fontSize: '0.65rem',
                          height: 24,
                          borderColor: `${color}40`,
                          color: color,
                        }}
                      />
                    ))}
                  </Box>

                  <Divider sx={{ mb: 1.5 }} />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', gap: 3 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Tasks
                        </Typography>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                          {agent.tasks_completed}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Avg Time
                        </Typography>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                          {agent.avg_execution_time}s
                        </Typography>
                      </Box>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => setExpandedAgent(isExpanded ? null : agent.id)}
                    >
                      {isExpanded ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>

                  <Collapse in={isExpanded}>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" sx={{ fontWeight: 600, mb: 1, display: 'block' }}>
                        Backstory
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem', mb: 2 }}>
                        {agent.backstory}
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, mb: 1, display: 'block' }}>
                        Tool Details
                      </Typography>
                      {agent.tools.map((tool: any) => (
                        <Box key={tool.name} sx={{ mb: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600, color }}>
                            {tool.name.replace(/_/g, ' ')}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            {tool.description}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Section D: Agent Metrics */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
        Performance Metrics
      </Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Tasks"
            value={metrics?.total_tasks || 0}
            icon={<TaskAlt />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Success Rate"
            value={`${((metrics?.success_rate || 0) * 100).toFixed(0)}%`}
            icon={<Speed />}
            color="#388e3c"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Execution"
            value={`${metrics?.average_execution_time || 0}s`}
            icon={<Timer />}
            color="#f57c00"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Agents"
            value="5/5"
            icon={<Group />}
            color="#7b1fa2"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Tasks by Agent
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" stroke="#666" fontSize={12} />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="tasks" radius={[6, 6, 0, 0]}>
                    {chartData.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Average Execution Time (seconds)
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" stroke="#666" fontSize={12} />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="avgTime" radius={[6, 6, 0, 0]}>
                    {chartData.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Agents;
