import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Avatar,
  CircularProgress,
  Alert,
  alpha,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  MoreVert,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Schedule,
  ArrowUpward,
  ArrowDownward,
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { dashboardAPI, agentsAPI } from '../services/api';
import { useThemeContext } from '../contexts/ThemeContext';

const RISK_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#eab308',
  low: '#10b981',
};

const SEVERITY_CONFIG: Record<string, { icon: React.ReactNode; color: string }> = {
  success: { icon: <CheckCircle sx={{ fontSize: 20 }} />, color: '#10b981' },
  warning: { icon: <Warning sx={{ fontSize: 20 }} />, color: '#f59e0b' },
  error: { icon: <ErrorIcon sx={{ fontSize: 20 }} />, color: '#ef4444' },
  info: { icon: <Schedule sx={{ fontSize: 20 }} />, color: '#3b82f6' },
};

const StatCard = ({ title, value, change, trend, color }: any) => (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5, fontWeight: 500, fontSize: '0.8rem' }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
              {value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {trend === 'up' ? (
                <ArrowUpward sx={{ fontSize: 14, color: '#10b981' }} />
              ) : (
                <ArrowDownward sx={{ fontSize: 14, color: '#ef4444' }} />
              )}
              <Typography
                variant="caption"
                sx={{ color: trend === 'up' ? '#10b981' : '#ef4444', fontWeight: 600 }}
              >
                {change}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                vs last month
              </Typography>
            </Box>
          </Box>
          <Box
            sx={{
              width: 52,
              height: 52,
              borderRadius: 3,
              background: alpha(color, 0.1),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {trend === 'up' ? (
              <TrendingUp sx={{ color: color, fontSize: 26 }} />
            ) : (
              <TrendingDown sx={{ color: color, fontSize: 26 }} />
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
);

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { accentColor, mode } = useThemeContext();
  const isLight = mode === 'light';

  const { data: metricsData, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => dashboardAPI.getMetrics().then(res => res.data),
  });

  const { data: activitiesData, isLoading: activitiesLoading } = useQuery({
    queryKey: ['dashboard-activities'],
    queryFn: () => dashboardAPI.getActivities().then(res => res.data),
  });

  const { data: agentsData } = useQuery({
    queryKey: ['agents-status'],
    queryFn: () => agentsAPI.getStatus().then(res => res.data),
  });

  const agents = Array.isArray(agentsData) ? agentsData : [];

  if (metricsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (metricsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboard metrics. Please ensure the backend server is running.
      </Alert>
    );
  }

  const metrics = metricsData;
  const complianceData = metrics?.trends?.compliance || [];
  const riskDist = metrics?.risk_distribution || {};
  const riskDistribution = Object.entries(riskDist).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
    color: RISK_COLORS[name] || '#9e9e9e',
  }));
  const regulatoryStatus = metrics?.regulatory_status || [];
  const activities = activitiesData?.activities || [];

  const chartStroke = isLight ? '#e2e8f0' : '#334155';
  const chartText = isLight ? '#64748b' : '#94a3b8';

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
          Compliance Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Monitor your organization's compliance health and risk metrics
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Overall Compliance"
            value={`${metrics?.overall_compliance || 0}%`}
            change="+3%"
            trend="up"
            color="#10b981"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Risks"
            value={metrics?.active_risks || 0}
            change="-12%"
            trend="down"
            color="#3b82f6"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Open Gaps"
            value={metrics?.open_gaps || 0}
            change="-5"
            trend="down"
            color="#f59e0b"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Audit Readiness"
            value={`${metrics?.audit_readiness || 0}%`}
            change="+8%"
            trend="up"
            color={accentColor.main}
          />
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Compliance Trend
                </Typography>
                <Chip label="Last 6 Months" size="small" variant="outlined" />
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={complianceData}>
                  <defs>
                    <linearGradient id="colorCompliance" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={accentColor.main} stopOpacity={0.2} />
                      <stop offset="95%" stopColor={accentColor.main} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartStroke} />
                  <XAxis dataKey="month" stroke={chartText} fontSize={12} />
                  <YAxis stroke={chartText} domain={[70, 100]} fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 12,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke={accentColor.main}
                    strokeWidth={2.5}
                    fill="url(#colorCompliance)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Risk Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 1 }}>
                {riskDistribution.map((item) => (
                  <Box
                    key={item.name}
                    sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: item.color }} />
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>{item.name}</Typography>
                    </Box>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {item.value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Regulatory Compliance
              </Typography>
              {regulatoryStatus.map((reg: any) => (
                <Box key={reg.name} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {reg.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      {reg.compliance}% / {reg.target}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={reg.compliance}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: isLight ? '#e2e8f0' : '#334155',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: reg.compliance >= reg.target ? '#10b981' : '#f59e0b',
                        borderRadius: 3,
                      },
                    }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Recent Activities
                </Typography>
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              </Box>
              {activitiesLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : activities.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No activities yet. Upload documents, run analyses, or generate reports to see activity here.
                </Typography>
              ) : (
                <List disablePadding>
                  {activities.map((activity: any) => {
                    const config = SEVERITY_CONFIG[activity.severity] || SEVERITY_CONFIG.info;
                    const timestamp = activity.timestamp
                      ? new Date(activity.timestamp).toLocaleString()
                      : '';
                    return (
                      <ListItem key={activity.id} sx={{ px: 0 }}>
                        <Avatar sx={{ bgcolor: alpha(config.color, 0.1), color: config.color, width: 36, height: 36, mr: 2 }}>
                          {config.icon}
                        </Avatar>
                        <ListItemText
                          primary={activity.title}
                          secondary={timestamp}
                          primaryTypographyProps={{ fontWeight: 500, fontSize: '0.875rem' }}
                          secondaryTypographyProps={{ fontSize: '0.75rem' }}
                        />
                      </ListItem>
                    );
                  })}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Agent Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Agent Status
                </Typography>
                <Chip
                  label="View All"
                  size="small"
                  clickable
                  color="primary"
                  variant="outlined"
                  onClick={() => navigate('/agents')}
                />
              </Box>
              {agents.map((agent: any) => (
                <Box
                  key={agent.name}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    py: 1.25,
                    '&:not(:last-child)': { borderBottom: `1px solid ${theme.palette.divider}` },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: agent.status === 'active' ? '#10b981' : '#f59e0b',
                      }}
                    />
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {agent.name}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {agent.tasks_completed} tasks
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
