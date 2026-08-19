import { useEffect, useState } from "react";
import { AccountSummary } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const GetAccountSummary = (accountId: number, refreshKey: number = 0) => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary | null>(null);

	// Drop the previous account's figures before the new ones arrive
	useEffect(() => { setSummary(null); }, [accountId, tenant]);

	useEffect(() => {
		if (accountId === 0) {
			return;
		}
		const abortController = new AbortController();
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.account_service_url}/account/${accountId}/summary`,
					{ signal: abortController.signal }
				);
				if (abortController.signal.aborted) {
					return;
				}
				setSummary(response.ok ? await response.json() : null);
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return; // Expected when effect is superseded
				}
				setSummary(null);
				return error;
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, tenant, refreshKey]);
	return summary;
}
