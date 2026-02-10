import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Unauthorized – please log in again.');
    } else if (error.response?.status === 500) {
      console.error('Server error – please try again later.');
    }
    return Promise.reject(error);
  },
);

export default api;
