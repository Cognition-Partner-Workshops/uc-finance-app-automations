import { act, renderHook, waitFor } from '@testing-library/react';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';
import { AccountSummary, GetAccountSummary } from './GetAccountSummary';

jest.mock('../fetchWithTenant', () => ({ fetchWithTenant: jest.fn() }));
jest.mock('../TenantContext', () => ({ useTenant: jest.fn() }));

const mockFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;
const mockTenant = useTenant as jest.MockedFunction<typeof useTenant>;
const summary: AccountSummary = {
	totalTrades: 3, settledTrades: 2, pendingTrades: 1,
	totalBuyQuantity: 100, totalSellQuantity: 25, netQuantity: 75,
};
const response = (data = summary, ok = true) => ({
	ok, json: async () => data,
} as Response);

beforeEach(() => {
	jest.resetAllMocks();
	mockTenant.mockReturnValue({ tenant: 'acme_corp', setTenant: jest.fn() });
});

test('does not request a summary without an account', () => {
	const { result } = renderHook(() => GetAccountSummary(0));
	expect(mockFetch).not.toHaveBeenCalled();
	expect(result.current).toEqual({ summary: null, error: false });
});

test('fetches summary and refreshes on live trade updates', async () => {
	mockFetch.mockResolvedValue(response());
	const { result, rerender } = renderHook(
		({ version }) => GetAccountSummary(1, version), { initialProps: { version: 0 } }
	);
	await waitFor(() => expect(result.current.summary).toEqual(summary));
	expect(mockFetch).toHaveBeenCalledWith(
		expect.stringContaining('/account/1/summary'), { signal: expect.any(AbortSignal) }
	);
	const updatedSummary = { ...summary, totalTrades: 4 };
	mockFetch.mockResolvedValue(response(updatedSummary));
	rerender({ version: 1 });
	await waitFor(() => expect(result.current.summary).toEqual(updatedSummary));
	expect(mockFetch).toHaveBeenCalledTimes(2);
});

test('clears stale data and ignores late responses when switching accounts', async () => {
	let resolveOld: (value: Response) => void = () => {};
	mockFetch.mockReturnValueOnce(new Promise((resolve) => { resolveOld = resolve; }));
	mockFetch.mockResolvedValueOnce(response({ ...summary, netQuantity: -20 }));
	const { result, rerender } = renderHook(
		({ accountId }) => GetAccountSummary(accountId), { initialProps: { accountId: 1 } }
	);
	const oldSignal = mockFetch.mock.calls[0][1]?.signal;
	rerender({ accountId: 2 });
	expect(oldSignal?.aborted).toBe(true);
	expect(result.current.summary).toBeNull();
	await waitFor(() => expect(result.current.summary?.netQuantity).toBe(-20));
	await act(async () => { resolveOld(response()); });
	expect(result.current.summary?.netQuantity).toBe(-20);
});

test('refetches for tenant changes and clears data on deselection', async () => {
	mockFetch.mockResolvedValue(response());
	const { result, rerender } = renderHook(
		({ accountId }) => GetAccountSummary(accountId), { initialProps: { accountId: 1 } }
	);
	await waitFor(() => expect(result.current.summary).toEqual(summary));
	mockTenant.mockReturnValue({ tenant: 'globex_inc', setTenant: jest.fn() });
	rerender({ accountId: 1 });
	expect(result.current.summary).toBeNull();
	await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));
	await waitFor(() => expect(result.current.summary).toEqual(summary));
	rerender({ accountId: 0 });
	expect(result.current.summary).toBeNull();
	expect(mockFetch).toHaveBeenCalledTimes(2);
});

test('clears a previously loaded summary while the next account loads', async () => {
	mockFetch.mockResolvedValueOnce(response());
	mockFetch.mockReturnValueOnce(new Promise(() => {}));
	const { result, rerender } = renderHook(
		({ accountId }) => GetAccountSummary(accountId), { initialProps: { accountId: 1 } }
	);
	await waitFor(() => expect(result.current.summary).toEqual(summary));
	rerender({ accountId: 2 });
	expect(result.current).toEqual({ summary: null, error: false });
});

test.each(['http', 'network'])('reports %s failures instead of displaying zero', async (failure) => {
	if (failure === 'http') mockFetch.mockResolvedValue(response(summary, false));
	else mockFetch.mockRejectedValue(new Error('Offline'));
	const { result } = renderHook(() => GetAccountSummary(1));
	await waitFor(() => expect(result.current).toEqual({ summary: null, error: true }));
});

test('aborts the request on unmount', () => {
	mockFetch.mockReturnValue(new Promise(() => {}));
	const { unmount } = renderHook(() => GetAccountSummary(1));
	const signal = mockFetch.mock.calls[0][1]?.signal;
	unmount();
	expect(signal?.aborted).toBe(true);
});

test('retries a failed request for the same account when the refresh version changes', async () => {
	mockFetch.mockResolvedValueOnce(response(summary, false));
	mockFetch.mockResolvedValueOnce(response());
	const { result, rerender } = renderHook(
		({ version }) => GetAccountSummary(1, version), { initialProps: { version: 0 } }
	);
	await waitFor(() => expect(result.current.error).toBe(true));
	rerender({ version: 1 });
	expect(result.current).toEqual({ summary: null, error: false });
	await waitFor(() => expect(result.current.summary).toEqual(summary));
	expect(mockFetch).toHaveBeenCalledTimes(2);
	expect(result.current.error).toBe(false);
});
