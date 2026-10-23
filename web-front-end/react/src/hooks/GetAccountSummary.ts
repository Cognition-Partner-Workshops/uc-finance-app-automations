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
	const [accountSummary, setAccountSummary] = useState<AccountSummary | null>(null);
	useEffect(() => {
		setAccountSummary(null);
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
				if (response.ok) {
					const json = await response.json();
					if (!abortController.signal.aborted) {
						setAccountSummary(json);
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
	return accountSummary;
};
