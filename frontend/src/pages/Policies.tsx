import React from 'react';
import { Box, Typography, Grid, Card, CardContent, Chip, Button } from '@mui/material';
import { Add, Edit } from '@mui/icons-material';

const Policies: React.FC = () => {
  const policies = [
    { id: 1, name: 'Data Protection Policy', version: '2.0', status: 'Active', lastUpdated: '2024-01-10' },
    { id: 2, name: 'Access Control Policy', version: '1.5', status: 'Active', lastUpdated: '2024-01-08' },
    { id: 3, name: 'Incident Response Policy', version: '3.1', status: 'Review', lastUpdated: '2023-12-20' },
    { id: 4, name: 'Business Continuity Policy', version: '2.2', status: 'Active', lastUpdated: '2024-01-05' },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Policy Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage and track organizational policies
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />}>
          New Policy
        </Button>
      </Box>

      <Grid container spacing={3}>
        {policies.map((policy) => (
          <Grid item xs={12} sm={6} md={4} key={policy.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  {policy.name}
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Chip label={`v${policy.version}`} size="small" sx={{ mr: 1 }} />
                  <Chip
                    label={policy.status}
                    size="small"
                    color={policy.status === 'Active' ? 'success' : 'warning'}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Last updated: {policy.lastUpdated}
                </Typography>
                <Button size="small" startIcon={<Edit />}>
                  Edit Policy
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Policies;