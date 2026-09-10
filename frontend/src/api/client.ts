const API_BASE = '/api/v1';

/** Errore del backend nel formato concordato: { detail, code }. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(detail: string, code: string, status: number) {
    super(detail);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, params?: Record<string, QueryValue>): string {
  const url = `${API_BASE}${path}`;
  if (!params) return url;

  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `${url}?${query}` : url;
}

export async function apiGet<T>(path: string, params?: Record<string, QueryValue>): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path, params), { headers: { Accept: 'application/json' } });
  } catch {
    // Il caso più comune in hackathon: il backend non è avviato. Meglio dirlo chiaramente.
    throw new ApiError('Backend non raggiungibile. Avvialo sulla porta 8000.', 'network_error', 0);
  }

  if (!response.ok) {
    const fallback = { detail: `Errore ${response.status}`, code: `http_${response.status}` };
    const body = (await response.json().catch(() => fallback)) as {
      detail?: string;
      code?: string;
    };
    throw new ApiError(body.detail ?? fallback.detail, body.code ?? fallback.code, response.status);
  }

  return (await response.json()) as T;
}
