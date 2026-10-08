import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AgGridReact } from 'ag-grid-react';

import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { SelectChangeEvent } from '@mui/material';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import BarChartIcon from '@mui/icons-material/BarChart';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import { socket } from '../socket';
import { GetPositions, GetTrades } from '../hooks';
import { CreateAccount, CreateAccountUser, CreateTradeButton } from '../ActionButtons';
import { ColDef, ICellRendererParams } from 'ag-grid-community';
import { PositionData, TradeData } from './types';
import { AccountsDropdown } from '../AccountsDropdown';

const PUBLISH = 'publish';
const SUBSCRIBE = 'subscribe';
const UNSUBSCRIBE = 'unsubscribe';

const SideCellRenderer = (params: ICellRendererParams) => {
	if (!params.value) return null;
	const isBuy = params.value === 'Buy';
	return (
		<Chip
			label={params.value}
			size="small"
			sx={{
				bgcolor: isBuy ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
				color: isBuy ? '#10b981' : '#ef4444',
				fontWeight: 600,
				fontSize: '0.75rem',
				height: 24,
				border: `1px solid ${isBuy ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
			}}
		/>
	);
};

const StateCellRenderer = (params: ICellRendererParams) => {
	if (!params.value) return null;
	const stateColors: Record<string, { bg: string; color: string; border: string }> = {
		New: { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)' },
		Processing: { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' },
		Pending: { bg: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6', border: 'rgba(139, 92, 246, 0.3)' },
		Settled: { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' },
		Cancelled: { bg: 'rgba(107, 114, 128, 0.15)', color: '#6b7280', border: 'rgba(107, 114, 128, 0.3)' },
	};
	const style = stateColors[params.value] || stateColors['New'];
	return (
		<Chip
			label={params.value}
			size="small"
			sx={{
				bgcolor: style.bg,
				color: style.color,
				fontWeight: 600,
				fontSize: '0.75rem',
				height: 24,
				border: `1px solid ${style.border}`,
			}}
		/>
	);
};

const QuantityCellRenderer = (params: ICellRendererParams) => {
	if (params.value == null) return null;
	const val = Number(params.value);
	const color = val > 0 ? '#10b981' : val < 0 ? '#ef4444' : '#e5e7eb';
	return <span style={{ color, fontWeight: 500 }}>{val.toLocaleString()}</span>;
};

interface StatCardProps {
	title: string;
	value: string | number;
	icon: React.ReactNode;
	color: string;
}

const StatCard = ({ title, value, icon, color }: StatCardProps) => (
	<Card sx={{ bgcolor: '#111827', border: '1px solid rgba(255,255,255,0.06)' }}>
		<CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
			<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
				<Box>
					<Typography variant="caption" sx={{ color: '#6b7280', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.65rem' }}>
						{title}
					</Typography>
					<Typography variant="h5" sx={{ fontWeight: 700, color: '#e5e7eb', mt: 0.5 }}>
						{value}
					</Typography>
				</Box>
				<Box sx={{ color, opacity: 0.8 }}>
					{icon}
				</Box>
			</Box>
		</CardContent>
	</Card>
);

export const Datatable = () => {
	const [tradeRowData, setTradeRowData] = useState<TradeData[]>([]);
	const [positionRowData, setPositionRowData] = useState<PositionData[]>([]);
	const [selectedId, setSelectedId] = useState<number>(0);
	const [currentAccount, setCurrentAccount] = useState<string>('');

	const positionData = GetPositions(selectedId);
	const tradeData = GetTrades(selectedId);

	const tradeColumnDefs = useMemo<ColDef<TradeData>[]>(() => [
		{ field: 'security', headerName: 'Security', flex: 1, minWidth: 100 },
		{ field: 'quantity', headerName: 'Quantity', flex: 1, minWidth: 90 },
		{ field: 'side', headerName: 'Side', flex: 1, minWidth: 90, cellRenderer: SideCellRenderer },
		{ field: 'state', headerName: 'State', flex: 1, minWidth: 100, cellRenderer: StateCellRenderer },
		{ field: 'updated', headerName: 'Updated', flex: 1.2, minWidth: 140 },
	], []);

	const positionColumnDefs = useMemo<ColDef<PositionData>[]>(() => [
		{ field: 'security', headerName: 'Security', flex: 1, minWidth: 100 },
		{ field: 'quantity', headerName: 'Quantity', flex: 1, minWidth: 100, cellRenderer: QuantityCellRenderer },
		{ field: 'updated', headerName: 'Updated', flex: 1.2, minWidth: 140 },
	], []);

	const defaultColDef = useMemo<ColDef>(() => ({
		resizable: true,
		sortable: true,
		filter: true,
	}), []);

	const handleChange = useCallback((event: SelectChangeEvent<string>) => {
		socket.off(PUBLISH);
		if (selectedId !== 0) {
			socket.emit(UNSUBSCRIBE, `/accounts/${selectedId}/trades`);
			socket.emit(UNSUBSCRIBE, `/accounts/${selectedId}/positions`);
		}
		const numericId = event.target.value ? Number(event.target.value) : 0;
		setSelectedId(numericId);
		setCurrentAccount(event.target.value);
		if (event.target.value) {
			socket.emit(SUBSCRIBE, `/accounts/${event.target.value}/trades`);
			socket.emit(SUBSCRIBE, `/accounts/${event.target.value}/positions`);
			socket.on(PUBLISH, (data: { topic: string; payload: TradeData | PositionData }) => {
				if (data.topic === `/accounts/${event.target.value}/trades`) {
					setTradeRowData((current: TradeData[]) => [...current, data.payload as TradeData]);
				}
				if (data.topic === `/accounts/${event.target.value}/positions`) {
					setPositionRowData((current: PositionData[]) => [...current, data.payload as PositionData]);
				}
			});
		}
	}, [selectedId]);

	useEffect(() => {
		setPositionRowData(positionData);
		setTradeRowData(tradeData);
	}, [positionData, tradeData]);

	const hasAccount = selectedId !== 0;

	return (
		<Box sx={{ p: 3 }}>
			{/* Account selector and action buttons row */}
			<Card sx={{ mb: 3, bgcolor: '#111827', border: '1px solid rgba(255,255,255,0.06)' }}>
				<CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
					<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
						<Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
							<AccountBalanceIcon sx={{ color: '#6b7280' }} />
							<AccountsDropdown currentAccount={currentAccount} handleChange={handleChange} />
						</Box>
						<Stack direction="row" spacing={1}>
							<CreateTradeButton accountId={selectedId} />
							<CreateAccount />
							<CreateAccountUser accountId={selectedId} />
						</Stack>
					</Box>
				</CardContent>
			</Card>

			{/* Summary stat cards */}
			{hasAccount && (
				<Grid container spacing={2} sx={{ mb: 3 }}>
					<Grid item xs={12} sm={6} md={3}>
						<StatCard
							title="Total Trades"
							value={tradeRowData.length}
							icon={<TrendingUpIcon sx={{ fontSize: 32 }} />}
							color="#3b82f6"
						/>
					</Grid>
					<Grid item xs={12} sm={6} md={3}>
						<StatCard
							title="Total Positions"
							value={positionRowData.length}
							icon={<BarChartIcon sx={{ fontSize: 32 }} />}
							color="#8b5cf6"
						/>
					</Grid>
					<Grid item xs={12} sm={6} md={3}>
						<StatCard
							title="Account"
							value={currentAccount ? `#${currentAccount}` : '--'}
							icon={<AccountBalanceIcon sx={{ fontSize: 32 }} />}
							color="#10b981"
						/>
					</Grid>
					<Grid item xs={12} sm={6} md={3}>
						<StatCard
							title="Live Feed"
							value="Active"
							icon={<ShowChartIcon sx={{ fontSize: 32 }} />}
							color="#f59e0b"
						/>
					</Grid>
				</Grid>
			)}

			{/* Grids or empty state */}
			{!hasAccount ? (
				<Box
					sx={{
						display: 'flex',
						flexDirection: 'column',
						alignItems: 'center',
						justifyContent: 'center',
						minHeight: '50vh',
						color: '#4b5563',
					}}
				>
					<ShowChartIcon sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
					<Typography variant="h6" sx={{ fontWeight: 600, color: '#6b7280' }}>
						No Account Selected
					</Typography>
					<Typography variant="body2" sx={{ color: '#4b5563', mt: 1 }}>
						Select an account from the dropdown above to view trades and positions
					</Typography>
				</Box>
			) : (
				<Grid container spacing={3}>
					{/* Trade Blotter */}
					<Grid item xs={12} lg={7}>
						<Card sx={{ bgcolor: '#111827', border: '1px solid rgba(255,255,255,0.06)', height: '100%' }}>
							<CardContent sx={{ p: 0, '&:last-child': { pb: 0 }, height: '100%', display: 'flex', flexDirection: 'column' }}>
								<Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
									<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
										<TrendingUpIcon sx={{ fontSize: 18, color: '#3b82f6' }} />
										<Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#e5e7eb' }}>
											Trade Blotter
										</Typography>
									</Box>
									<Chip label={`${tradeRowData.length} trades`} size="small" sx={{ bgcolor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', fontSize: '0.7rem', height: 22 }} />
								</Box>
								<Box className="ag-theme-alpine-dark" sx={{ flex: 1, minHeight: 400 }}>
									<AgGridReact
										rowData={tradeRowData}
										columnDefs={tradeColumnDefs}
										defaultColDef={defaultColDef}
										animateRows={true}
										domLayout="autoHeight"
									/>
								</Box>
							</CardContent>
						</Card>
					</Grid>

					{/* Position Blotter */}
					<Grid item xs={12} lg={5}>
						<Card sx={{ bgcolor: '#111827', border: '1px solid rgba(255,255,255,0.06)', height: '100%' }}>
							<CardContent sx={{ p: 0, '&:last-child': { pb: 0 }, height: '100%', display: 'flex', flexDirection: 'column' }}>
								<Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
									<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
										<BarChartIcon sx={{ fontSize: 18, color: '#8b5cf6' }} />
										<Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#e5e7eb' }}>
											Position Blotter
										</Typography>
									</Box>
									<Chip label={`${positionRowData.length} positions`} size="small" sx={{ bgcolor: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6', fontSize: '0.7rem', height: 22 }} />
								</Box>
								<Box className="ag-theme-alpine-dark" sx={{ flex: 1, minHeight: 400 }}>
									<AgGridReact
										rowData={positionRowData}
										columnDefs={positionColumnDefs}
										defaultColDef={defaultColDef}
										animateRows={true}
										domLayout="autoHeight"
									/>
								</Box>
							</CardContent>
						</Card>
					</Grid>
				</Grid>
			)}
		</Box>
	);
};
