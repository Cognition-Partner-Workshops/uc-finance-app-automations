import { useEffect, useState } from 'react';
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export interface AccountSummary {
	totalTrades: number;
	settledTrades: number;
	pendingTrades: number;
	totalBuyQuantity: number;
	totalSellQuantity: number;
	netQuantity: number;
}

interface SummaryState {
	accountId: number;
	tenant: string;
	summary: AccountSummary | null;
	error: boolean;
}

export const GetAccountSummary = (accountId: number, refreshVersion = 0) => {
	const { tenant } = useTenant();
	const [state, setState] = useState<SummaryState | null>(null);

	useEffect(() => {
		setState(null);
		if (accountId === 0) return;
		const controller = new AbortController();
		const fetchSummary = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.account_service_url}/account/${accountId}/summary`,
					{ signal: controller.signal }
				);
				if (!response.ok) throw new Error('Account summary unavailable');
				const summary: AccountSummary = await response.json();
				if (!controller.signal.aborted) {
					setState({ accountId, tenant, summary, error: false });
				}
			} catch {
				if (!controller.signal.aborted) {
					setState({ accountId, tenant, summary: null, error: true });
				}
			}
		};
		fetchSummary();
		return () => controller.abort();
	}, [accountId, tenant, refreshVersion]);

	const isCurrent = accountId !== 0 && state?.accountId === accountId && state?.tenant === tenant;
	return {
		summary: isCurrent ? state.summary : null,
		error: isCurrent ? state.error : false,
	};
};
