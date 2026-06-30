import { UploadResponse, TransformResponse, ProjectionConfig } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Helper to handle fetch responses and handle JSON or HTTP errors.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'Network response was not ok';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return response.json() as Promise<T>;
}

/**
 * Uploads a file to the backend.
 */
async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<UploadResponse>(response);
}

export const apiService = {
  /**
   * Upload recruiter CSV.
   */
  async uploadCSV(file: File): Promise<UploadResponse> {
    return uploadFile(file);
  },

  /**
   * Upload resume PDF.
   */
  async uploadResume(file: File): Promise<UploadResponse> {
    return uploadFile(file);
  },

  /**
   * Upload configuration JSON.
   */
  async uploadConfig(file: File): Promise<UploadResponse> {
    return uploadFile(file);
  },

  /**
   * Validate configuration JSON directly.
   */
  async validateConfig(config: ProjectionConfig): Promise<{ valid: boolean; errors?: any[]; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/validate-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    
    if (response.status === 422) {
      return handleResponse(response);
    }
    
    return handleResponse<{ valid: boolean; message: string }>(response);
  },

  /**
   * Run transformation pipeline.
   */
  async transformCandidate(
    csvPath?: string,
    resumePath?: string,
    config?: ProjectionConfig
  ): Promise<TransformResponse> {
    const response = await fetch(`${API_BASE_URL}/api/transform`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        csv_path: csvPath || null,
        resume_path: resumePath || null,
        config: config || null,
      }),
    });

    return handleResponse<TransformResponse>(response);
  },

  /**
   * Returns the direct URL to download the output.
   */
  getDownloadUrl(): string {
    return `${API_BASE_URL}/api/download`;
  },

  /**
   * Downloads output JSON content directly.
   */
  async downloadOutput(): Promise<Blob> {
    const response = await fetch(this.getDownloadUrl(), {
      method: 'GET',
    });

    if (!response.ok) {
      let errorMsg = 'Failed to download file';
      try {
        const errJson = await response.json();
        errorMsg = errJson.detail || errorMsg;
      } catch {}
      throw new Error(errorMsg);
    }

    return response.blob();
  },
};
