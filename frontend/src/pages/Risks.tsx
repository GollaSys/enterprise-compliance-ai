import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip, LinearProgress } from '@mui/material';
import { Warning, Error, Info } from '@mui/icons-material';

const Risks: React.FC = () => {
  const risks = [
    { id: 1, title: 'GDPR Data Breach Risk', level: 'high', score: 7.5, mitigation: 60 },
    { id: 2, title: 'SOX Control Weakness', level: 'critical', score: 8.9, mitigation: 30 },
    { id: 3, title: 'Third-party Vendor Risk', level: 'medium', score: 5.2, mitigation: 75 },
    { id: 4, title: 'Access Control Gap', level: 'high', score: 7.1, mitigation: 45 },
  ];

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#ffc107';
      default: return '#4caf50';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'critical': return <Error sx={{ color: '#f44336' }} />;
      case 'high': return <Warning sx={{ color: '#ff9800' }} />;
      default: return <Info sx={{ color: '#2196f3' }} />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
        Risk Management
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Monitor and manage compliance risks
      </Typography>

      <Grid container spacing={3}>
        {risks.map((risk) => (
          <Grid item xs={12} md={6} key={risk.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    {getRiskIcon(risk.level)}
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {risk.title}
                      </Typography>
                      <Chip
                        label={risk.level.toUpperCase()}
                        size="small"
                        sx={{
                          mt: 1,
                          backgroundColor: getRiskColor(risk.level),
                          color: 'white',
                        }}
                      />
                    </Box>
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: getRiskColor(risk.level) }}>
                    {risk.score}
                  </Typography>
                </Box>
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Mitigation Progress: {risk.mitigation}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={risk.mitigation}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: '#e0e0e0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: risk.mitigation >= 70 ? '#4caf50' : '#ff9800',
                        borderRadius: 4,
                      },
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Risks;