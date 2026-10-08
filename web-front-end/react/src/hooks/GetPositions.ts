import { useEffect, useState } from "react";
import { PositionData } from "../Datatable/types";
import { Environment } from '../env';
import { apiFetch } from '../apiFetch';

export const GetPositions = (accountId:number) => {
	const [positionsData, setPositionsData] = useState<PositionData[]>([]);
	useEffect(() => {
		if (accountId === 0) {
			setPositionsData([]);
			return;
		}
		const abortController = new AbortController();
		const fetchData = async () => {
			try {
				const response = await apiFetch(
					`${Environment.position_service_url}/positions/${accountId}`,
					{ signal: abortController.signal }
				);
				if (response.ok) {
					const json = await response.json();
					if (!abortController.signal.aborted) {
						setPositionsData(json);
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
	}, [accountId]);
	return positionsData;
}
