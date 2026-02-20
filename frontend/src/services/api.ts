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
  getStatus: (id: string) => api.get(`/api/v1/compliance/status/${id}`),
  getResults: (id: string) => api.get(`/api/v1/compliance/results/${id}`),
};

export const documentsAPI = {
  upload: (file: FormData) =>
    api.post('/api/v1/documents/upload', file, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: () => api.get('/api/v1/documents'),
  delete: (docId: string) => api.delete(`/api/v1/documents/${docId}`),
};

export const agentsAPI = {
  getStatus: () => api.get('/api/v1/agents/status'),
  getDetails: () => api.get('/api/v1/agents/details'),
  getOrchestration: () => api.get('/api/v1/agents/orchestration'),
  getMetrics: () => api.get('/api/v1/agents/metrics'),
  startRun: (data: { regulation_type: string; document_id?: string }) => api.post('/api/v1/agents/orchestration/run', data),
  getTimeline: (runId: string) => api.get(`/api/v1/agents/orchestration/${runId}/timeline`),
};

export const reportsAPI = {
  generate: (data: any) => api.post('/api/v1/reports/generate', data),
  list: () => api.get('/api/v1/reports'),
  get: (id: string) => api.get(`/api/v1/reports/${id}`),
};

export const policiesAPI = {
  list: () => api.get('/api/v1/policies'),
  create: (data: any) => api.post('/api/v1/policies', null, { params: data }),
};

export const risksAPI = {
  list: () => api.get('/api/v1/risks'),
  get: (id: string) => api.get(`/api/v1/risks/${id}`),
  assess: (data: any) => api.post('/api/v1/risks/assess', data),
};

export default api;
