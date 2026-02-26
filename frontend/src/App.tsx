import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SnackbarProvider } from 'notistack';

import { ThemeContextProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Compliance from './pages/Compliance';
import Documents from './pages/Documents';
import Policies from './pages/Policies';
import Risks from './pages/Risks';
import Reports from './pages/Reports';
import Agents from './pages/Agents';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContextProvider>
        <SnackbarProvider
          maxSnack={3}
          anchorOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <CssBaseline />
          <Router>
            <Box sx={{ display: 'flex', height: '100vh' }}>
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/compliance" element={<Compliance />} />
                  <Route path="/documents" element={<Documents />} />
                  <Route path="/policies" element={<Policies />} />
                  <Route path="/risks" element={<Risks />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/agents" element={<Agents />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </Layout>
            </Box>
          </Router>
        </SnackbarProvider>
      </ThemeContextProvider>
    </QueryClientProvider>
  );
}

export default App;
