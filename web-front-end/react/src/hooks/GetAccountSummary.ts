import { useEffect, useState } from "react";
import { AccountSummaryData } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const GetAccountSummary = (accountId: number, refreshKey: number = 0) => {
	const { tenant } = useTenant();
	const [summaryData, setSummaryData] = useState<AccountSummaryData | null>(null);
	useEffect(() => {
		if (accountId === 0) {
			setSummaryData(null);
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
					const json: AccountSummaryData = await response.json();
					if (!abortController.signal.aborted) {
						setSummaryData(json);
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
	}, [accountId, tenant, refreshKey]);
	return summaryData?.accountId === accountId ? summaryData : null;
}
