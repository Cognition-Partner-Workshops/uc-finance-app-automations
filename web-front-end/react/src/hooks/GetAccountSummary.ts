import { useEffect, useState } from "react";
import { AccountSummaryData } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const GetAccountSummary = (
	accountId: number,
	refreshKey: number = 0
): AccountSummaryData | null => {
	const { tenant } = useTenant();
	const [summaryState, setSummaryState] = useState<{
		accountId: number;
		tenant: string;
		summary: AccountSummaryData | null;
	}>({ accountId: 0, tenant, summary: null });

	useEffect(() => {
		if (accountId === 0) {
			setSummaryState({ accountId, tenant, summary: null });
			return;
		}
		setSummaryState((current) => (
			current.accountId === accountId && current.tenant === tenant
				? current
				: { accountId, tenant, summary: null }
		));
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
						setSummaryState({ accountId, tenant, summary: json });
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
	}, [accountId, tenant, refreshKey]);

	if (summaryState.accountId !== accountId || summaryState.tenant !== tenant) {
		return null;
	}
	return summaryState.summary;
};
