import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  alpha,
  useTheme,
} from '@mui/material';
import { Save, Check } from '@mui/icons-material';
import { useThemeContext } from '../contexts/ThemeContext';

const Settings: React.FC = () => {
  const theme = useTheme();
  const { mode, toggleMode, accentColor, setAccentColor, accentColors } = useThemeContext();

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Configure system preferences, appearance, and integrations
      </Typography>

      <Grid container spacing={3}>
        {/* Appearance Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Appearance
              </Typography>

              {/* Theme Mode */}
              <Box sx={{ mb: 4 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.secondary' }}>
                  Theme Mode
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  {(['light', 'dark'] as const).map((themeMode) => (
                    <Box
                      key={themeMode}
                      onClick={() => { if (mode !== themeMode) toggleMode(); }}
                      sx={{
                        flex: 1,
                        maxWidth: 240,
                        p: 2,
                        borderRadius: 3,
                        border: `2px solid ${mode === themeMode ? accentColor.main : theme.palette.divider}`,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        bgcolor: mode === themeMode ? alpha(accentColor.main, 0.04) : 'transparent',
                        '&:hover': {
                          borderColor: mode === themeMode ? accentColor.main : theme.palette.text.secondary,
                        },
                      }}
                    >
                      {/* Mini preview */}
                      <Box
                        sx={{
                          width: '100%',
                          height: 80,
                          borderRadius: 2,
                          mb: 1.5,
                          overflow: 'hidden',
                          display: 'flex',
                          border: `1px solid ${themeMode === 'light' ? '#e2e8f0' : '#334155'}`,
                        }}
                      >
                        <Box sx={{
                          width: '30%',
                          bgcolor: themeMode === 'light' ? '#ffffff' : '#0f172a',
                          borderRight: `1px solid ${themeMode === 'light' ? '#e2e8f0' : '#334155'}`,
                          p: 0.5,
                        }}>
                          {[1, 2, 3].map(i => (
                            <Box key={i} sx={{
                              height: 6,
                              borderRadius: 1,
                              bgcolor: themeMode === 'light' ? '#e2e8f0' : '#334155',
                              mb: 0.5,
                            }} />
                          ))}
                        </Box>
                        <Box sx={{
                          flex: 1,
                          bgcolor: themeMode === 'light' ? '#f8fafc' : '#1e293b',
                          p: 0.5,
                        }}>
                          <Box sx={{ display: 'flex', gap: 0.5, mb: 0.5 }}>
                            {[1, 2].map(i => (
                              <Box key={i} sx={{
                                flex: 1,
                                height: 20,
                                borderRadius: 1,
                                bgcolor: themeMode === 'light' ? '#ffffff' : '#0f172a',
                                border: `1px solid ${themeMode === 'light' ? '#e2e8f0' : '#334155'}`,
                              }} />
                            ))}
                          </Box>
                          <Box sx={{
                            height: 30,
                            borderRadius: 1,
                            bgcolor: themeMode === 'light' ? '#ffffff' : '#0f172a',
                            border: `1px solid ${themeMode === 'light' ? '#e2e8f0' : '#334155'}`,
                          }} />
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                          {themeMode}
                        </Typography>
                        {mode === themeMode && (
                          <Box sx={{
                            width: 22,
                            height: 22,
                            borderRadius: '50%',
                            bgcolor: accentColor.main,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}>
                            <Check sx={{ fontSize: 14, color: 'white' }} />
                          </Box>
                        )}
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Box>

              {/* Accent Color */}
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.secondary' }}>
                  Accent Color
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  {accentColors.map((color) => (
                    <Box
                      key={color.name}
                      onClick={() => setAccentColor(color)}
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 0.75,
                        cursor: 'pointer',
                      }}
                    >
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: '50%',
                          background: `linear-gradient(135deg, ${color.main} 0%, ${color.dark} 100%)`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: accentColor.name === color.name
                            ? `3px solid ${color.main}`
                            : '3px solid transparent',
                          outline: accentColor.name === color.name
                            ? `2px solid ${alpha(color.main, 0.3)}`
                            : 'none',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            transform: 'scale(1.1)',
                            boxShadow: `0 4px 12px ${alpha(color.main, 0.4)}`,
                          },
                        }}
                      >
                        {accentColor.name === color.name && (
                          <Check sx={{ color: 'white', fontSize: 20 }} />
                        )}
                      </Box>
                      <Typography
                        variant="caption"
                        sx={{
                          fontSize: '0.7rem',
                          fontWeight: accentColor.name === color.name ? 600 : 400,
                          color: accentColor.name === color.name ? color.main : 'text.secondary',
                        }}
                      >
                        {color.name}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* API Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                API Configuration
              </Typography>
              <TextField
                fullWidth
                label="OpenAI API Key"
                type="password"
                placeholder="sk-..."
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Anthropic API Key"
                type="password"
                placeholder="sk-ant-..."
                sx={{ mb: 2 }}
              />
              <Button variant="contained" startIcon={<Save />}>
                Save Configuration
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Notification Settings
              </Typography>
              <FormControlLabel
                control={<Switch defaultChecked color="primary" />}
                label="Email notifications"
                sx={{ mb: 2, display: 'block' }}
              />
              <FormControlLabel
                control={<Switch defaultChecked color="primary" />}
                label="Critical alerts"
                sx={{ mb: 2, display: 'block' }}
              />
              <FormControlLabel
                control={<Switch color="primary" />}
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
