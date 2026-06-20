/* =============================================================================
   File & Conversion Service — API calls
   ============================================================================= */

import type {
  ApiResponse,
  Conversion,
  ConversionType,
  DashboardStats,
  FileRecord,
  Notification,
  SupportedFormat,
  UploadResponse,
} from '@/types';
import api from './api';

export const fileService = {
  async uploadFiles(files: File[], onProgress?: (percent: number) => void): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const response = await api.post('/files/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    });

    return response.data?.data || response.data;
  },

  async getFiles(page = 1, search = ''): Promise<{ data: FileRecord[]; pagination: unknown }> {
    const params = new URLSearchParams({ page: String(page) });
    if (search) params.append('search', search);
    const response = await api.get(`/files/?${params}`);
    return response.data;
  },

  async getFile(id: string): Promise<FileRecord> {
    const response = await api.get(`/files/${id}/`);
    return response.data?.data || response.data;
  },

  async deleteFile(id: string): Promise<void> {
    await api.delete(`/files/${id}/`);
  },
};

export const conversionService = {
  async createConversion(
    sourceFileId: string,
    conversionType: ConversionType,
    options: Record<string, unknown> = {}
  ): Promise<Conversion> {
    const response = await api.post('/conversions/', {
      source_file_id: sourceFileId,
      conversion_type: conversionType,
      options,
    });
    return response.data?.data || response.data;
  },

  async getConversions(page = 1): Promise<{ data: Conversion[]; pagination: unknown }> {
    const response = await api.get(`/conversions/list/?page=${page}`);
    return response.data;
  },

  async getConversion(id: string): Promise<Conversion> {
    const response = await api.get(`/conversions/${id}/`);
    return response.data?.data || response.data;
  },

  async downloadConversion(id: string): Promise<{ download_url: string; filename: string }> {
    const response = await api.get(`/conversions/${id}/download/`);
    return response.data?.data || response.data;
  },

  async getSupportedFormats(): Promise<SupportedFormat[]> {
    const response = await api.get('/conversions/formats/');
    return response.data?.data || response.data;
  },

  async createShare(id: string): Promise<{ share_token: string; share_url: string; expires_at: string }> {
    const response = await api.post(`/conversions/${id}/share/`);
    return response.data?.data || response.data;
  },

  async getPublicShare(token: string): Promise<{ download_url: string; filename: string; file_size: number }> {
    const response = await api.get(`/conversions/share/${token}/`);
    return response.data?.data || response.data;
  },

  async createBatchConversion(conversions: { source_file_id: string; conversion_type: ConversionType; options?: Record<string, unknown> }[]): Promise<{ batch_id: string; conversions: Conversion[] }> {
    const response = await api.post('/conversions/batch/', { conversions });
    return response.data?.data || response.data;
  },

  async getBatchStatus(batchId: string): Promise<{ batch_id: string; total_conversions: number; completed_count: number; failed_count: number; pending_count: number; conversions: Conversion[] }> {
    const response = await api.get(`/conversions/batch/${batchId}/`);
    return response.data?.data || response.data;
  },

  async createBatchZip(batchId: string): Promise<Conversion> {
    const response = await api.post(`/conversions/batch/${batchId}/zip/`);
    return response.data?.data || response.data;
  },
};

export const analyticsService = {
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get('/analytics/dashboard/');
    return response.data?.data || response.data;
  },

  async getHistory(): Promise<unknown[]> {
    const response = await api.get('/analytics/history/');
    return response.data?.data || response.data;
  },

  async getUsage(): Promise<unknown> {
    const response = await api.get('/analytics/usage/');
    return response.data?.data || response.data;
  },
};

export const notificationService = {
  async getNotifications(): Promise<ApiResponse<Notification[]>> {
    const response = await api.get('/notifications/');
    return response.data;
  },

  async getUnreadCount(): Promise<number> {
    const response = await api.get('/notifications/unread-count/');
    return response.data?.data?.unread_count || 0;
  },

  async markAsRead(id: string): Promise<void> {
    await api.patch(`/notifications/${id}/read/`);
  },

  async markAllAsRead(): Promise<void> {
    await api.post('/notifications/read-all/');
  },
};
