import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Warning,
  Error as ErrorIcon,
  Info,
  CheckCircleOutline,
  Category,
  Gavel,
  TrendingUp,
  Shield,
  Close,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { risksAPI } from '../services/api';

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
    case 'critical': return <ErrorIcon sx={{ color: '#f44336' }} />;
    case 'high': return <Warning sx={{ color: '#ff9800' }} />;
    default: return <Info sx={{ color: '#2196f3' }} />;
  }
};

const Risks: React.FC = () => {
  const [selectedRisk, setSelectedRisk] = useState<any>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['risks'],
    queryFn: () => risksAPI.list().then(res => res.data),
  });

  const risks = data?.risks || [];

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
      ) : risks.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
              No risks identified yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Run a compliance analysis to identify and score risks automatically.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {risks.map((risk: any) => {
            const mitigation = risk.mitigation_progress ?? (risk.score >= 8 ? 20 : risk.score >= 6 ? 45 : 65);
            return (
              <Grid item xs={12} md={6} key={risk.id}>
                <Card sx={{ '&:hover': { boxShadow: 6 }, transition: 'box-shadow 0.2s' }}>
                  <CardActionArea onClick={() => setSelectedRisk(risk)}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                          {getRiskIcon(risk.level)}
                          <Box>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {risk.title || risk.description}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                              <Chip
                                label={risk.level.toUpperCase()}
                                size="small"
                                sx={{
                                  backgroundColor: getRiskColor(risk.level),
                                  color: 'white',
                                }}
                              />
                              {risk.category && (
                                <Chip label={risk.category} size="small" variant="outlined" />
                              )}
                              {risk.regulation && (
                                <Chip label={risk.regulation} size="small" variant="outlined" color="primary" />
                              )}
                            </Box>
                          </Box>
                        </Box>
                        <Typography variant="h5" sx={{ fontWeight: 700, color: getRiskColor(risk.level), flexShrink: 0, ml: 1 }}>
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
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
                        Click to view details
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Risk Detail Dialog */}
      <Dialog
        open={!!selectedRisk}
        onClose={() => setSelectedRisk(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedRisk && (
          <>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                {getRiskIcon(selectedRisk.level)}
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {selectedRisk.title || selectedRisk.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                    <Chip
                      label={selectedRisk.level.toUpperCase()}
                      size="small"
                      sx={{ backgroundColor: getRiskColor(selectedRisk.level), color: 'white' }}
                    />
                    {selectedRisk.category && <Chip label={selectedRisk.category} size="small" variant="outlined" />}
                    {selectedRisk.regulation && <Chip label={selectedRisk.regulation} size="small" variant="outlined" color="primary" />}
                    <Chip label={`Score: ${selectedRisk.score}`} size="small" variant="outlined" sx={{ fontWeight: 600 }} />
                  </Box>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              {/* Description */}
              {selectedRisk.description && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body1">
                    {selectedRisk.description}
                  </Typography>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Risk Assessment Details */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <TrendingUp sx={{ color: '#ff9800', fontSize: 32, mb: 0.5 }} />
                    <Typography variant="subtitle2" color="text.secondary">Impact</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {selectedRisk.impact || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Category sx={{ color: '#2196f3', fontSize: 32, mb: 0.5 }} />
                    <Typography variant="subtitle2" color="text.secondary">Likelihood</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {selectedRisk.likelihood || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Gavel sx={{ color: '#9c27b0', fontSize: 32, mb: 0.5 }} />
                    <Typography variant="subtitle2" color="text.secondary">Regulation</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {selectedRisk.regulation || 'N/A'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Shield sx={{ color: '#4caf50', fontSize: 32, mb: 0.5 }} />
                    <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {selectedRisk.status}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* Affected Areas */}
              {selectedRisk.affected_areas && selectedRisk.affected_areas.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Affected Areas
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedRisk.affected_areas.map((area: string, idx: number) => (
                      <Chip key={idx} label={area} variant="outlined" size="small" />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Mitigation Progress */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Mitigation Progress
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ flex: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={selectedRisk.mitigation_progress ?? (selectedRisk.score >= 8 ? 20 : selectedRisk.score >= 6 ? 45 : 65)}
                      sx={{
                        height: 12,
                        borderRadius: 6,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: (selectedRisk.mitigation_progress ?? 0) >= 70 ? '#4caf50' : '#ff9800',
                          borderRadius: 6,
                        },
                      }}
                    />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, minWidth: 50, textAlign: 'right' }}>
                    {selectedRisk.mitigation_progress ?? (selectedRisk.score >= 8 ? 20 : selectedRisk.score >= 6 ? 45 : 65)}%
                  </Typography>
                </Box>
              </Box>

              {/* Mitigation Steps */}
              {selectedRisk.mitigation_steps && selectedRisk.mitigation_steps.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Mitigation Steps
                  </Typography>
                  <List dense>
                    {selectedRisk.mitigation_steps.map((step: string, idx: number) => (
                      <ListItem key={idx}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <CheckCircleOutline sx={{ color: '#bdbdbd', fontSize: 20 }} />
                        </ListItemIcon>
                        <ListItemText primary={step} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* Metadata */}
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                <Typography variant="caption" color="text.secondary">
                  Risk ID: {selectedRisk.id}
                </Typography>
                {selectedRisk.gap_ref && (
                  <Typography variant="caption" color="text.secondary">
                    Related Gap: {selectedRisk.gap_ref}
                  </Typography>
                )}
                {selectedRisk.compliance_id && (
                  <Typography variant="caption" color="text.secondary">
                    Analysis: {selectedRisk.compliance_id}
                  </Typography>
                )}
                {selectedRisk.created_at && (
                  <Typography variant="caption" color="text.secondary">
                    Identified: {new Date(selectedRisk.created_at).toLocaleDateString()}
                  </Typography>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button startIcon={<Close />} onClick={() => setSelectedRisk(null)}>
                Close
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default Risks;
