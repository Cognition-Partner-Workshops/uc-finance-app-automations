import { useEffect, useState } from "react";
import { AccountSummary } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const GetAccountSummary = (
	accountId: number,
	refreshKey: number = 0
): AccountSummary | null => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary | null>(null);

	// Clear stale data only when the account or tenant changes, not on live refreshes
	useEffect(() => {
		setSummary(null);
	}, [accountId, tenant]);

	useEffect(() => {
		if (accountId === 0) {
			setSummary(null);
			return;
		}

		const abortController = new AbortController();
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.position_service_url}/account/${accountId}/summary`,
					{ signal: abortController.signal }
				);
				if (response.ok) {
					const json = await response.json();
					if (!abortController.signal.aborted) {
						setSummary(json);
					}
				}
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return;
				}
				return error;
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, refreshKey, tenant]);

	return summary;
};
