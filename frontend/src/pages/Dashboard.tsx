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
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  MoreVert,
  CheckCircle,
  Warning,
  Error,
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

const Dashboard: React.FC = () => {
  const complianceData = [
    { month: 'Jan', score: 78 },
    { month: 'Feb', score: 82 },
    { month: 'Mar', score: 85 },
    { month: 'Apr', score: 87 },
    { month: 'May', score: 89 },
    { month: 'Jun', score: 92 },
  ];

  const riskDistribution = [
    { name: 'Critical', value: 3, color: '#f44336' },
    { name: 'High', value: 8, color: '#ff9800' },
    { name: 'Medium', value: 15, color: '#ffc107' },
    { name: 'Low', value: 24, color: '#4caf50' },
  ];

  const regulatoryStatus = [
    { name: 'GDPR', compliance: 92, target: 95 },
    { name: 'SOX', compliance: 88, target: 90 },
    { name: 'FINRA', compliance: 94, target: 95 },
    { name: 'SEC', compliance: 85, target: 90 },
  ];

  const StatCard = ({ title, value, change, trend, color }: any) => (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="text.secondary" variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {trend === 'up' ? (
                <ArrowUpward sx={{ fontSize: 16, color: 'success.main' }} />
              ) : (
                <ArrowDownward sx={{ fontSize: 16, color: 'error.main' }} />
              )}
              <Typography
                variant="body2"
                sx={{
                  color: trend === 'up' ? 'success.main' : 'error.main',
                  fontWeight: 600,
                }}
              >
                {change}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                vs last month
              </Typography>
            </Box>
          </Box>
          <Box
            sx={{
              width: 60,
              height: 60,
              borderRadius: 3,
              background: `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {trend === 'up' ? (
              <TrendingUp sx={{ color: color, fontSize: 28 }} />
            ) : (
              <TrendingDown sx={{ color: color, fontSize: 28 }} />
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Compliance Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor your organization's compliance health and risk metrics
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Overall Compliance"
            value="92%"
            change="+3%"
            trend="up"
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Risks"
            value="50"
            change="-12%"
            trend="down"
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Open Gaps"
            value="15"
            change="-5"
            trend="down"
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Audit Readiness"
            value="87%"
            change="+8%"
            trend="up"
            color="#9c27b0"
          />
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Compliance Trend
                </Typography>
                <Chip label="Last 6 Months" size="small" />
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={complianceData}>
                  <defs>
                    <linearGradient id="colorCompliance" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4caf50" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#4caf50" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" stroke="#666" />
                  <YAxis stroke="#666" domain={[70, 100]} />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#4caf50"
                    strokeWidth={2}
                    fill="url(#colorCompliance)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Risk Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 2 }}>
                {riskDistribution.map((item) => (
                  <Box
                    key={item.name}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          borderRadius: 1,
                          backgroundColor: item.color,
                        }}
                      />
                      <Typography variant="body2">{item.name}</Typography>
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
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Regulatory Compliance
              </Typography>
              {regulatoryStatus.map((reg) => (
                <Box key={reg.name} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {reg.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {reg.compliance}% / {reg.target}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={reg.compliance}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: '#e0e0e0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor:
                          reg.compliance >= reg.target ? '#4caf50' : '#ff9800',
                        borderRadius: 4,
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
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Recent Activities
                </Typography>
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              </Box>
              <List>
                <ListItem sx={{ px: 0 }}>
                  <Avatar sx={{ bgcolor: '#4caf50', width: 36, height: 36, mr: 2 }}>
                    <CheckCircle sx={{ fontSize: 20 }} />
                  </Avatar>
                  <ListItemText
                    primary="GDPR Audit Completed"
                    secondary="2 hours ago"
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <Avatar sx={{ bgcolor: '#ff9800', width: 36, height: 36, mr: 2 }}>
                    <Warning sx={{ fontSize: 20 }} />
                  </Avatar>
                  <ListItemText
                    primary="New Risk Identified"
                    secondary="5 hours ago"
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <Avatar sx={{ bgcolor: '#2196f3', width: 36, height: 36, mr: 2 }}>
                    <Schedule sx={{ fontSize: 20 }} />
                  </Avatar>
                  <ListItemText
                    primary="Policy Review Scheduled"
                    secondary="1 day ago"
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <Avatar sx={{ bgcolor: '#f44336', width: 36, height: 36, mr: 2 }}>
                    <Error sx={{ fontSize: 20 }} />
                  </Avatar>
                  <ListItemText
                    primary="Critical Gap Detected"
                    secondary="2 days ago"
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;