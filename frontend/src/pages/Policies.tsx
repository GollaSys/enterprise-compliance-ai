import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { Add, Edit } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { policiesAPI } from '../services/api';

const Policies: React.FC = () => {
  const [createOpen, setCreateOpen] = useState(false);
  const [newPolicy, setNewPolicy] = useState({ name: '', content: '', version: '1.0' });
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();

  const { data, isLoading, error } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesAPI.list().then(res => res.data),
  });

  const createMutation = useMutation({
    mutationFn: (policy: { name: string; content: string; version: string }) =>
      policiesAPI.create(policy),
    onSuccess: () => {
      enqueueSnackbar('Policy created successfully', { variant: 'success' });
      queryClient.invalidateQueries({ queryKey: ['policies'] });
      setCreateOpen(false);
      setNewPolicy({ name: '', content: '', version: '1.0' });
    },
    onError: () => {
      enqueueSnackbar('Failed to create policy', { variant: 'error' });
    },
  });

  const policies = data?.policies || [];

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load policies. Please ensure the backend server is running.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
            Policy Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage and track organizational policies
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          New Policy
        </Button>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : policies.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
              No policies yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Click "New Policy" to create your first organizational policy.
            </Typography>
            <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
              New Policy
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {policies.map((policy: any) => (
            <Grid item xs={12} sm={6} md={4} key={policy.policy_id || policy.name}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    {policy.name}
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Chip label={`v${policy.version}`} size="small" sx={{ mr: 1 }} />
                    <Chip
                      label={policy.status === 'active' ? 'Active' : 'Review'}
                      size="small"
                      color={policy.status === 'active' ? 'success' : 'warning'}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Created: {new Date(policy.created_at).toLocaleDateString()}
                  </Typography>
                  <Button size="small" startIcon={<Edit />}>
                    Edit Policy
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Policy</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Policy Name"
            value={newPolicy.name}
            onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Version"
            value={newPolicy.version}
            onChange={(e) => setNewPolicy({ ...newPolicy, version: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Content"
            value={newPolicy.content}
            onChange={(e) => setNewPolicy({ ...newPolicy, content: e.target.value })}
            multiline
            rows={4}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createMutation.mutate(newPolicy)}
            disabled={!newPolicy.name || !newPolicy.content || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Policies;
