import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Chip,
  LinearProgress,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Error,
  Warning,
  Info,
  Download,
  Refresh,
  FilterList,
} from '@mui/icons-material';

const Compliance: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedRegulation, setSelectedRegulation] = useState('');
  const [analysisStatus, setAnalysisStatus] = useState('idle');

  const steps = [
    {
      label: 'Select Regulations',
      description: 'Choose regulatory frameworks for analysis',
    },
    {
      label: 'Upload Documents',
      description: 'Upload relevant compliance documents',
    },
    {
      label: 'Map Policies',
      description: 'Map internal policies to regulations',
    },
    {
      label: 'Validate Evidence',
      description: 'Validate compliance evidence',
    },
    {
      label: 'Generate Report',
      description: 'Generate compliance assessment report',
    },
  ];

  const regulations = [
    { id: 'GDPR', name: 'General Data Protection Regulation', jurisdiction: 'EU' },
    { id: 'SOX', name: 'Sarbanes-Oxley Act', jurisdiction: 'US' },
    { id: 'FINRA', name: 'Financial Industry Regulatory Authority', jurisdiction: 'US' },
    { id: 'SEC', name: 'Securities and Exchange Commission', jurisdiction: 'US' },
  ];

  const complianceItems = [
    {
      id: '1',
      regulation: 'GDPR',
      requirement: 'Data Protection Officer',
      status: 'compliant',
      score: 95,
      lastAssessed: '2024-01-15',
    },
    {
      id: '2',
      regulation: 'GDPR',
      requirement: 'Privacy Policy',
      status: 'partial',
      score: 75,
      lastAssessed: '2024-01-14',
    },
    {
      id: '3',
      regulation: 'SOX',
      requirement: 'Internal Controls',
      status: 'non-compliant',
      score: 45,
      lastAssessed: '2024-01-10',
    },
    {
      id: '4',
      regulation: 'FINRA',
      requirement: 'Record Keeping',
      status: 'compliant',
      score: 92,
      lastAssessed: '2024-01-12',
    },
  ];

  const handleStartAnalysis = () => {
    setAnalysisStatus('running');
    setTimeout(() => {
      setAnalysisStatus('completed');
    }, 3000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'success';
      case 'partial':
        return 'warning';
      case 'non-compliant':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle sx={{ color: '#4caf50' }} />;
      case 'partial':
        return <Warning sx={{ color: '#ff9800' }} />;
      case 'non-compliant':
        return <Error sx={{ color: '#f44336' }} />;
      default:
        return <Info />;
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Compliance Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Analyze and manage regulatory compliance across your organization
        </Typography>
      </Box>

      {analysisStatus === 'running' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Compliance analysis in progress...
            </Typography>
            <LinearProgress sx={{ mt: 1 }} />
          </Box>
        </Alert>
      )}

      {analysisStatus === 'completed' && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Compliance analysis completed successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Quick Analysis
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Regulation Type</InputLabel>
                <Select
                  value={selectedRegulation}
                  onChange={(e) => setSelectedRegulation(e.target.value)}
                  label="Regulation Type"
                >
                  {regulations.map((reg) => (
                    <MenuItem key={reg.id} value={reg.id}>
                      {reg.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Button
                variant="contained"
                fullWidth
                startIcon={<PlayArrow />}
                onClick={handleStartAnalysis}
                disabled={!selectedRegulation || analysisStatus === 'running'}
                sx={{ mb: 2 }}
              >
                Start Analysis
              </Button>

              <Stepper activeStep={activeStep} orientation="vertical">
                {steps.map((step, index) => (
                  <Step key={step.label}>
                    <StepLabel>{step.label}</StepLabel>
                    <StepContent>
                      <Typography variant="body2" color="text.secondary">
                        {step.description}
                      </Typography>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Compliance Status
                </Typography>
                <Box>
                  <IconButton size="small">
                    <FilterList />
                  </IconButton>
                  <IconButton size="small">
                    <Refresh />
                  </IconButton>
                  <IconButton size="small">
                    <Download />
                  </IconButton>
                </Box>
              </Box>

              <Grid container spacing={2}>
                {complianceItems.map((item) => (
                  <Grid item xs={12} key={item.id}>
                    <Paper
                      sx={{
                        p: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        borderLeft: `4px solid ${
                          item.status === 'compliant' ? '#4caf50' :
                          item.status === 'partial' ? '#ff9800' : '#f44336'
                        }`,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        {getStatusIcon(item.status)}
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {item.requirement}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {item.regulation} • Last assessed: {item.lastAssessed}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ textAlign: 'right' }}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {item.score}%
                          </Typography>
                          <Chip
                            label={item.status.replace('-', ' ')}
                            size="small"
                            color={getStatusColor(item.status) as any}
                          />
                        </Box>
                      </Box>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Total Requirements
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    247
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Compliant
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#4caf50' }}>
                    198
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Partial
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#ff9800' }}>
                    32
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Non-Compliant
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f44336' }}>
                    17
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Compliance;