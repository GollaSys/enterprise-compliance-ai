import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardAPI = {
  getMetrics: () => api.get('/api/v1/dashboard/metrics'),
  getActivities: () => api.get('/api/v1/dashboard/activities'),
};

export const complianceAPI = {
  analyze: (data: any) => api.post('/api/v1/compliance/analyze', data),
  getRegulations: () => api.get('/api/v1/compliance/regulations'),
};

export const documentsAPI = {
  upload: (file: FormData) =>
    api.post('/api/v1/documents/upload', file, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: () => api.get('/api/v1/documents'),
};

export const agentsAPI = {
  getStatus: () => api.get('/api/v1/agents/status'),
};

export const reportsAPI = {
  generate: (data: any) => api.post('/api/v1/reports/generate', data),
  list: () => api.get('/api/v1/reports'),
};

export default api;