import axios from 'axios';

// API Base URL - automatically detect environment
const getApiBaseUrl = () => {
  // Check if we're in production
  if (import.meta.env.PROD) {
    // In production, try to get the API URL from environment variable first
    return import.meta.env.VITE_API_BASE_URL || 'https://your-railway-app.railway.app';
  }
  // In development
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

const API_BASE = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // 30 seconds timeout for production
});

function getToken() {
  return localStorage.getItem('token') || '';
}

// Health and legacy endpoints
export const getHealth = () => api.get('/health');
export const getDevToken = (username) => api.post('/dev/token', { username });

// Authentication endpoints
export const registerUser = (userData) => api.post('/auth/register', userData);
export const loginUser = (credentials) => api.post('/auth/login', credentials);
export const getCurrentUser = (token) => api.get('/auth/me', { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const updateUserProfile = (data, token) => api.put('/auth/profile', data, { headers: { Authorization: `Bearer ${token || getToken()}` } });

// Chat endpoints
export const askQuestion = (data, token) => api.post('/ask', data, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const createChatSession = (data, token) => api.post('/chat/sessions', data, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const getChatSessions = (token) => api.get('/chat/sessions', { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const getChatSessionDetail = (sessionId, token) => api.get(`/chat/sessions/${sessionId}`, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const updateChatSession = (sessionId, data, token) => api.put(`/chat/sessions/${sessionId}`, data, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const deleteChatSession = (sessionId, token) => api.delete(`/chat/sessions/${sessionId}`, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const submitMessageFeedback = (data, token) => api.post('/chat/feedback', data, { headers: { Authorization: `Bearer ${token || getToken()}` } });

// User stats endpoint
export const getUserStats = (token) => api.get('/user/stats', { headers: { Authorization: `Bearer ${token || getToken()}` } });

// Admin endpoints
export const uploadFiles = (formData, token) => api.post('/upload', formData, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const reindex = (folder, token) => api.post('/reindex', { folder }, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const sendFeedback = (data, token) => api.post('/feedback', data, { headers: { Authorization: `Bearer ${token || getToken()}` } });
export const getFeedbacks = (token) => api.get('/feedbacks', { headers: { Authorization: `Bearer ${token || getToken()}` } });