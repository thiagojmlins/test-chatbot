import axios from 'axios';
import { API_BASE_URL } from './config';

// Create an instance of axios with the base URL
const httpClient = axios.create({
  baseURL: API_BASE_URL,
});

// Optionally, add interceptors to attach tokens automatically
httpClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default httpClient;
