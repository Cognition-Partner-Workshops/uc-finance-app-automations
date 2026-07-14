/**
 * Wrapper around fetch that injects the X-Tenant-ID header.
 * All API calls should use this instead of raw fetch().
 */
let currentTenant = 'acme_corp';

export function setCurrentTenant(tenant: string) {
  currentTenant = tenant;
}

export function getCurrentTenant(): string {
  return currentTenant;
}

export interface ApiErrorDetail {
  status: number;
  method: string;
  endpoint: string;
  body: string;
}

export const API_ERROR_EVENT = 'traderx:api-error';

function emitApiError(detail: ApiErrorDetail) {
  window.dispatchEvent(new CustomEvent<ApiErrorDetail>(API_ERROR_EVENT, { detail }));
}

function toEndpoint(input: RequestInfo | URL): string {
  const raw = typeof input === 'string' ? input : input.toString();
  try {
    return new URL(raw).pathname;
  } catch {
    return raw;
  }
}

export function fetchWithTenant(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set('X-Tenant-ID', currentTenant);
  const method = (init?.method || 'GET').toUpperCase();

  return fetch(input, { ...init, headers }).then((response) => {
    if (response.status >= 500) {
      response
        .clone()
        .text()
        .then((body) => {
          emitApiError({ status: response.status, method, endpoint: toEndpoint(input), body });
        })
        .catch(() => {
          emitApiError({ status: response.status, method, endpoint: toEndpoint(input), body: '' });
        });
    }
    return response;
  });
}
