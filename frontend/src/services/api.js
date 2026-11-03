import axios from 'axios';

// Determine default base URL:
// In browser development with webpack dev server proxy, '/api/v1' or full URL can be used.
const baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor for consistent error messaging
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let message = 'An unexpected network error occurred.';
    if (error.response) {
      // Backend returned HTTP error status
      const { data, status } = error.response;
      if (data && typeof data === 'object') {
        message = data.detail || data.message || `Request failed with status code ${status}`;
      } else if (typeof data === 'string') {
        message = data;
      } else {
        message = `HTTP error ${status}`;
      }
    } else if (error.request) {
      // Request made but no response received (backend offline / CORS / network error)
      message = 'Unable to reach backend server at ' + baseURL + '. Ensure FastAPI backend is running on localhost:8000.';
    } else {
      message = error.message || message;
    }

    const enhancedError = new Error(message);
    enhancedError.status = error.response ? error.response.status : null;
    enhancedError.originalError = error;
    return Promise.reject(enhancedError);
  }
);

export default apiClient;
