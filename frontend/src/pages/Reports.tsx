import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Button, Chip } from '@mui/material';
import { Download, Schedule, CheckCircle } from '@mui/icons-material';

const Reports: React.FC = () => {
  const reports = [
    { id: 1, title: 'Q4 2024 Executive Summary', type: 'Executive', status: 'completed', date: '2024-01-15' },
    { id: 2, title: 'GDPR Compliance Assessment', type: 'Compliance', status: 'completed', date: '2024-01-10' },
    { id: 3, title: 'Risk Assessment Report', type: 'Risk', status: 'generating', date: '2024-01-16' },
    { id: 4, title: 'Annual Audit Report', type: 'Audit', status: 'scheduled', date: '2024-01-20' },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle sx={{ color: '#4caf50', fontSize: 20 }} />;
      case 'generating': return <Schedule sx={{ color: '#ff9800', fontSize: 20 }} />;
      default: return <Schedule sx={{ color: '#9e9e9e', fontSize: 20 }} />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
        Reports
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Generate and manage compliance reports
      </Typography>

      <Grid container spacing={3}>
        {reports.map((report) => (
          <Grid item xs={12} sm={6} md={4} key={report.id}>
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
                  {report.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Type: {report.type} • {report.date}
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
    </Box>
  );
};

export default Reports;