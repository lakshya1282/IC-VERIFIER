import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Verify IC from text
export const verifyICText = async (markingText) => {
  const response = await api.post('/verify-text', {
    marking_text: markingText
  });
  return response.data;
};

// Verify IC from image
export const verifyICImage = async (imageBase64) => {
  const response = await api.post('/verify-image', {
    image_base64: imageBase64
  });
  return response.data;
};

// Get verification history
export const getVerifications = async (page = 1, limit = 20) => {
  const response = await api.get('/verifications', {
    params: { page, limit }
  });
  return response.data;
};

// Get single verification
export const getVerification = async (id) => {
  const response = await api.get(`/verifications/${id}`);
  return response.data;
};

// Get statistics
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

// Get IC database
export const getICDatabase = async () => {
  const response = await api.get('/ic-database');
  return response.data;
};

// Get IC stats
export const getICStats = async () => {
  const response = await api.get('/ic-stats');
  return response.data;
};

export default api;
