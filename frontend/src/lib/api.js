const API_URL = (import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000')).replace(/\/$/, '');
export async function api(path, options = {}) {
  let response;
  const token = localStorage.getItem('practicas.token');
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } });
  } catch { throw new Error(`No se pudo conectar con la API en ${API_URL}. Verifica que el backend esté iniciado.`); }
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || body?.mensaje || `Error de API (${response.status})`);
  return body;
}
export const apiBase = API_URL;
export function rows(data) { return Array.isArray(data) ? data : []; }
