import { useEffect, useState } from "react";
import { AccountSummaryData } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const EMPTY_ACCOUNT_SUMMARY: AccountSummaryData = {
	accountId: 0,
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number, refreshToken: number = 0) => {
	const { tenant } = useTenant();
	const [summaryData, setSummaryData] = useState<AccountSummaryData>(EMPTY_ACCOUNT_SUMMARY);
	useEffect(() => {
		if (accountId === 0) {
			setSummaryData(EMPTY_ACCOUNT_SUMMARY);
			return;
		}
		const abortController = new AbortController();
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.account_service_url}/account/${accountId}/summary`,
					{ signal: abortController.signal }
				);
				if (response.ok) {
					const json = await response.json();
					if (!abortController.signal.aborted) {
						setSummaryData(json);
					}
				}
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return; // Expected when effect is superseded
				}
				return error;
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, tenant, refreshToken]);
	return summaryData;
}
