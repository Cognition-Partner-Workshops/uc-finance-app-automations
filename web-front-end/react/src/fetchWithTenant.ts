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

  return fetch(input, { ...init, headers })
    .then((response) => {
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
    })
    .catch((error) => {
      // A rejected fetch means a network-level failure. In this app that most
      // commonly happens when the server throws an unhandled 500: the error
      // response is returned without CORS headers, so the browser surfaces it
      // as a failed request rather than a readable response.
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw error; // expected when an in-flight request is superseded
      }
      emitApiError({
        status: 0,
        method,
        endpoint: toEndpoint(input),
        body:
          'The request failed. This usually means the server returned an ' +
          'unhandled error (HTTP 500) or is unreachable.',
      });
      throw error;
    });
}
