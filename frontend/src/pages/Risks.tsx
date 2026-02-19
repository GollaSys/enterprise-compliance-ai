import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Warning, Error, Info } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { risksAPI } from '../services/api';

const defaultRisks = [
  { id: 'RISK-001', description: 'Data breach risk', level: 'high', score: 7.5, status: 'open' },
  { id: 'RISK-002', description: 'Access control gap', level: 'medium', score: 5.2, status: 'open' },
  { id: 'RISK-003', description: 'Unencrypted PII storage', level: 'critical', score: 9.1, status: 'open' },
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

const getMitigationFromScore = (score: number) => {
  if (score >= 8) return 20;
  if (score >= 6) return 45;
  if (score >= 4) return 65;
  return 80;
};

const Risks: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['risks'],
    queryFn: () => risksAPI.list().then(res => res.data),
  });

  const apiRisks = data?.risks || [];
  const risks = apiRisks.length > 0 ? apiRisks : defaultRisks;

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load risks. Is the backend running?
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
        Risk Management
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Monitor and manage compliance risks
      </Typography>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {risks.map((risk: any) => {
            const mitigation = getMitigationFromScore(risk.score);
            return (
              <Grid item xs={12} md={6} key={risk.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        {getRiskIcon(risk.level)}
                        <Box>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {risk.description}
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
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Mitigation Progress: {mitigation}%
                        </Typography>
                        <Chip label={risk.status} size="small" variant="outlined" />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={mitigation}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: '#e0e0e0',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: mitigation >= 70 ? '#4caf50' : '#ff9800',
                            borderRadius: 4,
                          },
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
};

export default Risks;
