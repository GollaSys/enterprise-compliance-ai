import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Download, Schedule, CheckCircle, Add } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { reportsAPI } from '../services/api';

const Reports: React.FC = () => {
  const [generateOpen, setGenerateOpen] = useState(false);
  const [reportType, setReportType] = useState('executive');
  const [period, setPeriod] = useState('Q4');
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const { data, isLoading, error } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsAPI.list().then(res => res.data),
  });

  const generateMutation = useMutation({
    mutationFn: (params: { report_type: string; period: string }) =>
      reportsAPI.generate(params),
    onSuccess: (res) => {
      enqueueSnackbar(`Report "${res.data.type} - ${res.data.period}" generated!`, { variant: 'success' });
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setGenerateOpen(false);
    },
    onError: () => {
      enqueueSnackbar('Failed to generate report', { variant: 'error' });
    },
  });

  const reports = data?.reports || [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle sx={{ color: '#10b981', fontSize: 20 }} />;
      case 'generating': return <Schedule sx={{ color: '#f59e0b', fontSize: 20 }} />;
      default: return <Schedule sx={{ color: 'text.secondary', fontSize: 20 }} />;
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load reports. Please ensure the backend server is running.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
            Reports
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generate and manage compliance reports
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setGenerateOpen(true)}>
          Generate Report
        </Button>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : reports.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
              No reports yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Click "Generate Report" to create your first compliance report.
            </Typography>
            <Button variant="contained" startIcon={<Add />} onClick={() => setGenerateOpen(true)}>
              Generate Report
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {reports.map((report: any) => (
            <Grid item xs={12} sm={6} md={4} key={report.report_id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    {getStatusIcon(report.status)}
                    <Chip
                      label={report.status}
                      size="small"
                      color={report.status === 'completed' ? 'success' : 'default'}
                    />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    {report.type} Report
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Period: {report.period}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Generated: {new Date(report.generated_at).toLocaleString()}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Download />}
                    disabled={report.status !== 'completed'}
                    fullWidth
                  >
                    Download
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={generateOpen} onClose={() => setGenerateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Report</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1, mb: 2 }}>
            <InputLabel>Report Type</InputLabel>
            <Select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              label="Report Type"
            >
              <MenuItem value="executive">Executive Summary</MenuItem>
              <MenuItem value="compliance">Compliance Assessment</MenuItem>
              <MenuItem value="risk">Risk Assessment</MenuItem>
              <MenuItem value="audit">Audit Report</MenuItem>
              <MenuItem value="technical">Technical Report</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Period</InputLabel>
            <Select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              label="Period"
            >
              <MenuItem value="Q1">Q1 2024</MenuItem>
              <MenuItem value="Q2">Q2 2024</MenuItem>
              <MenuItem value="Q3">Q3 2024</MenuItem>
              <MenuItem value="Q4">Q4 2024</MenuItem>
              <MenuItem value="Annual">Annual 2024</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => generateMutation.mutate({ report_type: reportType, period })}
            disabled={generateMutation.isPending}
          >
            {generateMutation.isPending ? 'Generating...' : 'Generate'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Reports;
