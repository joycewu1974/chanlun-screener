import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000
});

export const stockApi = {
  // 掃描相關
  getScanStatus: () => api.get('/api/scan/status'),
  runScan: () => api.post('/api/scan/run'),
  getScanResults: (signalType, confidenceType, limit = 50) =>
    api.get('/api/scan/results', { 
      params: { 
        signal_type: signalType, 
        confidence: confidenceType,
        limit 
      } 
    }),

  // 分析相關
  analyzeStock: (ticker) => api.get(`/api/analyze/${ticker}`),
  getChart: (ticker) => api.get(`/api/chart/${ticker}`),

  // 統計相關
  getStats: () => api.get('/api/stats'),
  getScanCandidates: () => api.get('/api/scan/candidates'),
  getScanSummary: () => api.get('/api/scan/summary'),

  // 健康檢查
  health: () => api.get('/health')
};

export default api;
