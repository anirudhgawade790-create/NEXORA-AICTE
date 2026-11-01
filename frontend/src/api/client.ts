const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem('nexora_token');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 401 && !path.endsWith('/auth/login')) {
    localStorage.removeItem('nexora_token');
    localStorage.removeItem('nexora_user');
    window.location.assign('/login');
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json() as { detail?: unknown };
      if (typeof body.detail === 'string') {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail
          .map((item) => typeof item === 'object' && item !== null && 'msg' in item ? String(item.msg) : '')
          .filter(Boolean)
          .join('; ') || message;
      }
    } catch {
      // The response may not contain JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  const suffix = query.toString();
  return request<T>(`${path}${suffix ? `?${suffix}` : ''}`);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'PUT', body: JSON.stringify(body) });
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

export function apiDownload(path: string, params?: Record<string, string | number | undefined>): Promise<void> {
  const token = localStorage.getItem('nexora_token');
  const headers = new Headers();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  const suffix = query.toString();
  return fetch(`${API_BASE}${path}${suffix ? `?${suffix}` : ''}`, { headers }).then(async (response) => {
    if (response.status === 401) {
      localStorage.removeItem('nexora_token');
      localStorage.removeItem('nexora_user');
      window.location.assign('/login');
    }
    if (!response.ok) throw new ApiError(`Download failed (${response.status})`, response.status);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = response.headers.get('content-disposition')?.match(/filename="?([^";]+)"?/i)?.[1] || 'download.csv';
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
