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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  IconButton,
  CircularProgress,
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
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { complianceAPI } from '../services/api';

const Compliance: React.FC = () => {
  const [selectedRegulation, setSelectedRegulation] = useState('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const { enqueueSnackbar } = useSnackbar();

  const { data: regulationsData, isLoading: regulationsLoading } = useQuery({
    queryKey: ['regulations'],
    queryFn: () => complianceAPI.getRegulations().then(res => res.data),
  });

  const analyzeMutation = useMutation({
    mutationFn: (regulationType: string) =>
      complianceAPI.analyze({
        regulation_type: regulationType,
        document_ids: [],
        include_evidence: true,
        generate_report: true,
      }),
    onSuccess: (res) => {
      setAnalysisResult(res.data);
      enqueueSnackbar('Compliance analysis completed!', { variant: 'success' });
    },
    onError: () => {
      enqueueSnackbar('Analysis failed. Please try again.', { variant: 'error' });
    },
  });

  const steps = [
    { label: 'Select Regulations', description: 'Choose regulatory frameworks for analysis' },
    { label: 'Upload Documents', description: 'Upload relevant compliance documents' },
    { label: 'Map Policies', description: 'Map internal policies to regulations' },
    { label: 'Validate Evidence', description: 'Validate compliance evidence' },
    { label: 'Generate Report', description: 'Generate compliance assessment report' },
  ];

  const regulations = regulationsData?.regulations || [];
  const results = analysisResult?.results;
  const gaps = results?.gaps || [];
  const risks = results?.risks || [];
  const recommendations = results?.recommendations || [];
  const complianceScore = results?.compliance_score;

  const activeStep = analyzeMutation.isPending ? 2 : analysisResult ? 4 : 0;

  const handleStartAnalysis = () => {
    if (selectedRegulation) {
      setAnalysisResult(null);
      analyzeMutation.mutate(selectedRegulation);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'partial': return 'warning';
      case 'non-compliant': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle sx={{ color: '#4caf50' }} />;
      case 'partial': return <Warning sx={{ color: '#ff9800' }} />;
      case 'non-compliant': return <Error sx={{ color: '#f44336' }} />;
      default: return <Info />;
    }
  };

  const getSeverityStatus = (severity: string) => {
    if (severity === 'high') return 'non-compliant';
    if (severity === 'medium') return 'partial';
    return 'compliant';
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

      {analyzeMutation.isPending && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Compliance analysis in progress...
            </Typography>
            <LinearProgress sx={{ mt: 1 }} />
          </Box>
        </Alert>
      )}

      {analysisResult && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Compliance analysis completed! Score: {complianceScore}%
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
                  {regulationsLoading ? (
                    <MenuItem disabled>Loading...</MenuItem>
                  ) : (
                    regulations.map((reg: any) => (
                      <MenuItem key={reg.id} value={reg.id}>
                        {reg.name}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>

              <Button
                variant="contained"
                fullWidth
                startIcon={analyzeMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
                onClick={handleStartAnalysis}
                disabled={!selectedRegulation || analyzeMutation.isPending}
                sx={{ mb: 2 }}
              >
                {analyzeMutation.isPending ? 'Analyzing...' : 'Start Analysis'}
              </Button>

              <Stepper activeStep={activeStep} orientation="vertical">
                {steps.map((step) => (
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
                  {analysisResult ? 'Analysis Results' : 'Compliance Status'}
                </Typography>
                <Box>
                  <IconButton size="small">
                    <FilterList />
                  </IconButton>
                  <IconButton size="small" onClick={() => { setAnalysisResult(null); setSelectedRegulation(''); }}>
                    <Refresh />
                  </IconButton>
                  <IconButton size="small">
                    <Download />
                  </IconButton>
                </Box>
              </Box>

              {analysisResult ? (
                <Grid container spacing={2}>
                  {gaps.map((gap: any) => {
                    const status = getSeverityStatus(gap.severity);
                    return (
                      <Grid item xs={12} key={gap.id}>
                        <Paper
                          sx={{
                            p: 2,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            borderLeft: `4px solid ${
                              status === 'non-compliant' ? '#f44336' :
                              status === 'partial' ? '#ff9800' : '#4caf50'
                            }`,
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            {getStatusIcon(status)}
                            <Box>
                              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                {gap.description}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Gap ID: {gap.id} • Severity: {gap.severity}
                              </Typography>
                            </Box>
                          </Box>
                          <Chip
                            label={gap.severity}
                            size="small"
                            color={getStatusColor(status) as any}
                          />
                        </Paper>
                      </Grid>
                    );
                  })}
                  {recommendations.map((rec: any, idx: number) => (
                    <Grid item xs={12} key={idx}>
                      <Paper
                        sx={{
                          p: 2,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 2,
                          borderLeft: '4px solid #2196f3',
                        }}
                      >
                        <Info sx={{ color: '#2196f3' }} />
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {rec.action}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Priority: {rec.priority}
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  Select a regulation and click "Start Analysis" to begin.
                </Typography>
              )}
            </CardContent>
          </Card>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Compliance Score
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#4caf50' }}>
                    {complianceScore ? `${complianceScore}%` : '--'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Gaps Found
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#ff9800' }}>
                    {gaps.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Risks Identified
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f44336' }}>
                    {risks.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" sx={{ mb: 1 }}>
                    Recommendations
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#2196f3' }}>
                    {recommendations.length}
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
