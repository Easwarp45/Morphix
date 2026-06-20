/* =============================================================================
   Auth Service — Authentication API calls
   ============================================================================= */

import type { AuthTokens, LoginCredentials, RegisterCredentials, User } from '@/types';
import api from './api';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await api.post('/auth/login/', credentials);
    const tokens = response.data;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    return tokens;
  },

  async register(data: RegisterCredentials): Promise<AuthTokens> {
    const response = await api.post('/auth/register/', data);
    const tokens = response.data;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    return tokens;
  },

  async logout(): Promise<void> {
    try {
      const refresh = localStorage.getItem('refresh_token');
      await api.post('/auth/logout/', { refresh });
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  async getProfile(): Promise<User> {
    const response = await api.get('/auth/user/');
    return response.data?.data || response.data;
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await api.patch('/auth/user/', data);
    return response.data?.data || response.data;
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  async resetPassword(email: string): Promise<void> {
    await api.post('/auth/password/reset/', { email });
  },

  async googleLogin(code: string): Promise<AuthTokens> {
    const response = await api.post('/auth/google/', { code });
    const tokens = response.data;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    return tokens;
  },

  async guestLogin(): Promise<AuthTokens> {
    const response = await api.post('/auth/guest/');
    const tokens = response.data?.data || response.data;
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    return tokens;
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
