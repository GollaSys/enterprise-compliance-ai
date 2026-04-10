import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Badge,
  Chip,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Description as DocumentIcon,
  Policy as PolicyIcon,
  Warning as RiskIcon,
  Assessment as ComplianceIcon,
  BarChart as ReportsIcon,
  SmartToy as AgentsIcon,
  AccountTree as DemoIcon,
  Settings as SettingsIcon,
  Notifications as NotificationIcon,
  AccountCircle,
  ChevronLeft,
  DarkMode,
  LightMode,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { dashboardAPI, risksAPI } from '../services/api';
import { useThemeContext } from '../contexts/ThemeContext';

const drawerWidth = 272;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const { mode, toggleMode, accentColor } = useThemeContext();
  const isLight = mode === 'light';

  const { data: metricsData } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => dashboardAPI.getMetrics().then(res => res.data),
    refetchInterval: 30000,
  });
  const { data: risksData } = useQuery({
    queryKey: ['risks'],
    queryFn: () => risksAPI.list().then(res => res.data),
    refetchInterval: 30000,
  });
  const { data: activitiesData } = useQuery({
    queryKey: ['activities'],
    queryFn: () => dashboardAPI.getActivities().then(res => res.data),
    refetchInterval: 30000,
  });

  const openRisksCount = risksData?.total || 0;
  const openGapsCount = metricsData?.open_gaps || 0;
  const activitiesCount = activitiesData?.activities?.length || 0;
  const complianceScore = metricsData?.overall_compliance || 0;

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard', badge: null },
    { text: 'Compliance', icon: <ComplianceIcon />, path: '/compliance', badge: openGapsCount > 0 ? String(openGapsCount) : null },
    { text: 'Documents', icon: <DocumentIcon />, path: '/documents', badge: null },
    { text: 'Policies', icon: <PolicyIcon />, path: '/policies', badge: null },
    { text: 'Risks', icon: <RiskIcon />, path: '/risks', badge: openRisksCount > 0 ? String(openRisksCount) : null },
    { text: 'Reports', icon: <ReportsIcon />, path: '/reports', badge: null },
    { text: 'Agents', icon: <AgentsIcon />, path: '/agents', badge: null },
    { text: 'Live Agent Demo', icon: <DemoIcon />, path: '/demo', badge: null },
  ];

  const sidebarBg = isLight ? '#ffffff' : '#0f172a';

  const drawer = (
    <Box sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: sidebarBg,
    }}>
      {/* Logo area */}
      <Toolbar
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2.5,
          py: 3,
          minHeight: '72px !important',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 38,
              height: 38,
              borderRadius: 2.5,
              background: `linear-gradient(135deg, ${accentColor.main} 0%, ${accentColor.dark} 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 800,
              fontSize: '0.8rem',
              letterSpacing: '0.05em',
              boxShadow: `0 4px 12px ${alpha(accentColor.main, 0.35)}`,
            }}
          >
            CA
          </Box>
          <Box>
            <Typography variant="subtitle1" noWrap sx={{ fontWeight: 700, lineHeight: 1.2, color: 'text.primary' }}>
              Compliance AI
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              Enterprise Platform
            </Typography>
          </Box>
        </Box>
        {drawerOpen && (
          <IconButton onClick={handleDrawerToggle} size="small" sx={{ color: 'text.secondary' }}>
            <ChevronLeft />
          </IconButton>
        )}
      </Toolbar>

      <Divider sx={{ mx: 2.5, borderColor: theme.palette.divider }} />

      {/* Navigation */}
      <List sx={{ flex: 1, px: 2, py: 2 }}>
        {menuItems.map((item) => {
          const isSelected = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                selected={isSelected}
                sx={{
                  borderRadius: 2.5,
                  py: 1,
                  px: 1.5,
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isSelected ? accentColor.main : 'text.secondary',
                    minWidth: 38,
                    transition: 'color 0.2s',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: isSelected ? 600 : 400,
                    fontSize: '0.875rem',
                    color: isSelected ? accentColor.main : 'text.primary',
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    sx={{
                      height: 22,
                      minWidth: 28,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      bgcolor: alpha(theme.palette.error.main, 0.1),
                      color: theme.palette.error.main,
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Settings link */}
      <Box sx={{ px: 2, mb: 1 }}>
        <ListItemButton
          onClick={() => navigate('/settings')}
          selected={location.pathname === '/settings'}
          sx={{
            borderRadius: 2.5,
            py: 1,
            px: 1.5,
          }}
        >
          <ListItemIcon sx={{
            color: location.pathname === '/settings' ? accentColor.main : 'text.secondary',
            minWidth: 38,
          }}>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText
            primary="Settings"
            primaryTypographyProps={{
              fontWeight: location.pathname === '/settings' ? 600 : 400,
              fontSize: '0.875rem',
              color: location.pathname === '/settings' ? accentColor.main : 'text.primary',
            }}
          />
        </ListItemButton>
      </Box>

      <Divider sx={{ mx: 2.5, borderColor: theme.palette.divider }} />

      {/* Compliance Score Card */}
      <Box sx={{ p: 2.5 }}>
        <Box
          sx={{
            p: 2.5,
            borderRadius: 3,
            background: `linear-gradient(135deg, ${accentColor.main} 0%, ${accentColor.dark} 100%)`,
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: -20,
              right: -20,
              width: 80,
              height: 80,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.1)',
            },
            '&::after': {
              content: '""',
              position: 'absolute',
              bottom: -10,
              left: -10,
              width: 50,
              height: 50,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.08)',
            },
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 600, opacity: 0.9, textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '0.65rem' }}>
            Compliance Score
          </Typography>
          <Typography variant="h3" sx={{ fontWeight: 800, my: 0.5, position: 'relative' }}>
            {complianceScore > 0 ? `${complianceScore}%` : '--'}
          </Typography>
          <Typography variant="caption" sx={{ opacity: 0.85, fontSize: '0.7rem' }}>
            {complianceScore >= 90 ? 'Excellent' :
             complianceScore >= 75 ? 'Good' :
             complianceScore >= 50 ? 'Needs Improvement' :
             complianceScore > 0 ? 'Requires Attention' :
             'Run analysis to see score'}
          </Typography>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', width: '100%' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${drawerOpen ? drawerWidth : 0}px)` },
          ml: { sm: `${drawerOpen ? drawerWidth : 0}px` },
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          backgroundColor: alpha(theme.palette.background.default, 0.8),
          backdropFilter: 'blur(12px)',
          color: 'text.primary',
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Toolbar sx={{ minHeight: '64px !important' }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: drawerOpen ? 'none' : 'flex' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
            {menuItems.find((item) => item.path === location.pathname)?.text ||
             (location.pathname === '/settings' ? 'Settings' : 'Dashboard')}
          </Typography>

          <Tooltip title={isLight ? 'Switch to dark mode' : 'Switch to light mode'}>
            <IconButton onClick={toggleMode} sx={{ mr: 1, color: 'text.secondary' }}>
              {isLight ? <DarkMode fontSize="small" /> : <LightMode fontSize="small" />}
            </IconButton>
          </Tooltip>

          <IconButton sx={{ mr: 1, color: 'text.secondary' }}>
            <Badge badgeContent={activitiesCount > 0 ? activitiesCount : undefined} color="error">
              <NotificationIcon fontSize="small" />
            </Badge>
          </IconButton>

          <IconButton
            onClick={handleProfileMenuOpen}
            size="small"
            sx={{ ml: 0.5 }}
            aria-controls={Boolean(anchorEl) ? 'account-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={Boolean(anchorEl) ? 'true' : undefined}
          >
            <Avatar sx={{
              width: 34,
              height: 34,
              bgcolor: alpha(accentColor.main, 0.15),
              color: accentColor.main,
              fontSize: '0.875rem',
              fontWeight: 600,
            }}>
              <AccountCircle fontSize="small" />
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            onClick={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            slotProps={{
              paper: {
                sx: {
                  mt: 1,
                  minWidth: 180,
                  borderRadius: 3,
                  border: `1px solid ${theme.palette.divider}`,
                },
              },
            }}
          >
            <MenuItem sx={{ borderRadius: 1.5, mx: 1 }}>Profile</MenuItem>
            <MenuItem sx={{ borderRadius: 1.5, mx: 1 }}>My Account</MenuItem>
            <Divider />
            <MenuItem sx={{ borderRadius: 1.5, mx: 1 }}>Logout</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{
          width: { sm: drawerOpen ? drawerWidth : 0 },
          flexShrink: { sm: 0 },
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 'none',
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="persistent"
          open={drawerOpen}
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: `1px solid ${theme.palette.divider}`,
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              background: sidebarBg,
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { sm: `calc(100% - ${drawerOpen ? drawerWidth : 0}px)` },
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          backgroundColor: 'background.default',
          minHeight: '100vh',
          mt: 8,
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout;
