import React from 'react';
import { Box, Typography, Card, CardContent, Grid, TextField, Button, Switch, FormControlLabel } from '@mui/material';
import { Save } from '@mui/icons-material';

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Configure system preferences and integrations
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                API Configuration
              </Typography>
              <TextField
                fullWidth
                label="OpenAI API Key"
                type="password"
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Anthropic API Key"
                type="password"
                sx={{ mb: 2 }}
              />
              <Button variant="contained" startIcon={<Save />}>
                Save Configuration
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Notification Settings
              </Typography>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Email notifications"
                sx={{ mb: 2, display: 'block' }}
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Critical alerts"
                sx={{ mb: 2, display: 'block' }}
              />
              <FormControlLabel
                control={<Switch />}
                label="Daily digest"
                sx={{ display: 'block' }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;