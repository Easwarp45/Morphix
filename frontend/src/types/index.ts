/* =============================================================================
   TypeScript Types for Cloud File Converter
   ============================================================================= */

// ── User Types ──────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  avatar_url: string;
  auth_provider: 'email' | 'google';
  storage_used: number;
  storage_limit: number;
  storage_remaining: number;
  storage_usage_percent: number;
  is_staff: boolean;
  is_guest?: boolean;
  created_at: string;
  last_login: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password1: string;
  password2: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// ── File Types ──────────────────────────────────────────────────────────────

export interface FileRecord {
  id: string;
  original_name: string;
  mime_type: string;
  file_extension: string;
  file_size: number;
  file_size_mb: number;
  status: FileStatus;
  is_image: boolean;
  is_document: boolean;
  metadata: Record<string, unknown>;
  download_url: string | null;
  created_at: string;
  updated_at: string;
}

export type FileStatus = 'uploading' | 'uploaded' | 'processing' | 'completed' | 'failed' | 'deleted';

export interface UploadResponse {
  uploaded: FileRecord[];
  errors: { file: string; error: string }[];
  total_uploaded: number;
  total_errors: number;
}

// ── Conversion Types ────────────────────────────────────────────────────────

export interface Conversion {
  id: string;
  source_file: string;
  source_file_name: string;
  conversion_type: ConversionType;
  source_format: string;
  target_format: string;
  status: ConversionStatus;
  output_filename: string;
  output_file_size: number;
  output_file_size_mb: number;
  processing_time: number | null;
  error_message: string;
  download_url: string | null;
  started_at: string | null;
  completed_at: string | null;
  is_batch?: boolean;
  batch_id?: string | null;
  created_at: string;
}

export type ConversionStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export type ConversionType =
  | 'pdf_to_docx' | 'docx_to_pdf' | 'txt_to_pdf' | 'pdf_to_txt'
  | 'png_to_jpg' | 'jpg_to_png' | 'webp_to_png' | 'png_to_webp'
  | 'image_compress' | 'pdf_compress'
  | 'zip_create' | 'zip_extract';

export interface FormatOption {
  type: ConversionType;
  target: string;
  label: string;
}

export interface SupportedFormat {
  source_extension: string;
  conversions: FormatOption[];
}

// ── Dashboard / Analytics Types ─────────────────────────────────────────────

export interface DashboardStats {
  total_files: number;
  total_conversions: number;
  completed_conversions: number;
  failed_conversions: number;
  total_downloads: number;
  storage: {
    used: number;
    limit: number;
    percent: number;
    used_mb: number;
    limit_mb: number;
  };
  conversions_by_type: { conversion_type: string; count: number }[];
  daily_conversions: { date: string; count: number }[];
}

// ── Notification Types ──────────────────────────────────────────────────────

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  data: Record<string, unknown>;
  created_at: string;
}

// ── API Response Types ──────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: {
    count: number;
    page: number;
    page_size: number;
    total_pages: number;
    next: string | null;
    previous: string | null;
  };
}
