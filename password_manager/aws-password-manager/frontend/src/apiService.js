import axios from 'axios';
import config from './config';
import authService from './authService';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: config.api.baseUrl,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to include authentication token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await authService.getIdToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Unauthorized - redirect to login
      authService.signOut();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

class ApiService {
  /**
   * Get all passwords for the current user
   */
  async getPasswords() {
    try {
      const response = await apiClient.get(config.api.endpoints.passwords);
      return response.data.passwords || [];
    } catch (error) {
      console.error('Error fetching passwords:', error);
      throw error;
    }
  }

  /**
   * Get a specific password by ID (without decrypted value)
   */
  async getPassword(id) {
    try {
      const response = await apiClient.get(`${config.api.endpoints.passwords}/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching password:', error);
      throw error;
    }
  }

  /**
   * Decrypt and get the password value
   */
  async decryptPassword(id) {
    try {
      const response = await apiClient.get(`${config.api.endpoints.decrypt}/${id}`);
      return response.data.decrypted_password;
    } catch (error) {
      console.error('Error decrypting password:', error);
      throw error;
    }
  }

  /**
   * Create a new password
   */
  async createPassword(passwordData) {
    try {
      const response = await apiClient.post(config.api.endpoints.passwords, passwordData);
      return response.data;
    } catch (error) {
      console.error('Error creating password:', error);
      throw error;
    }
  }

  /**
   * Update an existing password
   */
  async updatePassword(id, passwordData) {
    try {
      const response = await apiClient.put(`${config.api.endpoints.passwords}/${id}`, passwordData);
      return response.data;
    } catch (error) {
      console.error('Error updating password:', error);
      throw error;
    }
  }

  /**
   * Delete a password
   */
  async deletePassword(id) {
    try {
      const response = await apiClient.delete(`${config.api.endpoints.passwords}/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting password:', error);
      throw error;
    }
  }
}

export default new ApiService();
