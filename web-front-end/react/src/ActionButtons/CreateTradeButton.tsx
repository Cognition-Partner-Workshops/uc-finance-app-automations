import React, { MouseEvent, useCallback, useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import CircularProgress from '@mui/material/CircularProgress';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import Grid from '@mui/material/Grid';
import { ActionButtonsProps, RefData, Side } from './types';
import { Environment } from '../env';
import { apiFetch } from '../apiFetch';

export const CreateTradeButton = ({ accountId }: ActionButtonsProps) => {
	const [refData, setRefData] = useState<RefData[]>([]);
	const [open, setOpen] = useState(false);
	const [loading, setLoading] = useState(false);
	const [submitting, setSubmitting] = useState(false);
	const [side, setSide] = useState<Side>(undefined);
	const [security, setSecurity] = useState<string>('');
	const [quantity, setQuantity] = useState<string>('');
	const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
		open: false,
		message: '',
		severity: 'success',
	});

	const handleOpen = async () => {
		setOpen(true);
		setSide(undefined);
		setSecurity('');
		setQuantity('');
		setLoading(true);
		try {
			const response = await apiFetch(`${Environment.reference_data_url}/stocks`);
			const data = await response.json();
			setRefData(data);
		} catch (error) {
			console.error('Failed to load stocks:', error);
		} finally {
			setLoading(false);
		}
	};

	const handleClose = () => {
		setOpen(false);
	};

	const handleSubmit = async () => {
		if (!security || !quantity || !side) return;
		const tradeId = Math.floor(Math.random() * 1000000);
		setSubmitting(true);
		try {
			const response = await apiFetch(`${Environment.trade_service_url}/trade/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					id: `TRADE-${tradeId}`,
					security,
					quantity: parseInt(quantity),
					accountId,
					side,
				}),
			});
			if (response.ok) {
				setSnackbar({ open: true, message: 'Trade created successfully', severity: 'success' });
				setOpen(false);
			} else {
				setSnackbar({ open: true, message: 'Failed to create trade', severity: 'error' });
			}
		} catch (error) {
			setSnackbar({ open: true, message: 'Error creating trade', severity: 'error' });
		} finally {
			setSubmitting(false);
		}
	};

	const handleToggleChange = useCallback(
		(_event: MouseEvent<HTMLElement>, newSide: Side) => {
			setSide(newSide);
		},
		[]
	);

	const isFormValid = security && quantity && parseInt(quantity) > 0 && side;

	return (
		<>
			<Button
				onClick={handleOpen}
				variant="contained"
				disabled={!accountId}
				startIcon={<AddIcon />}
				size="small"
				sx={{
					bgcolor: '#3b82f6',
					'&:hover': { bgcolor: '#2563eb' },
				}}
			>
				New Trade
			</Button>

			<Dialog
				open={open}
				onClose={handleClose}
				maxWidth="sm"
				fullWidth
				PaperProps={{
					sx: {
						bgcolor: '#111827',
						border: '1px solid rgba(255,255,255,0.1)',
						borderRadius: 2,
					},
				}}
			>
				<DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1 }}>
					<Typography variant="h6" sx={{ fontWeight: 600 }}>
						Create Trade
					</Typography>
					<IconButton onClick={handleClose} size="small" sx={{ color: '#6b7280' }}>
						<CloseIcon />
					</IconButton>
				</DialogTitle>

				<DialogContent sx={{ pt: 2 }}>
					{loading ? (
						<Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
							<CircularProgress />
						</Box>
					) : (
						<Grid container spacing={2.5} sx={{ mt: 0 }}>
							<Grid item xs={12}>
								<Autocomplete
									options={refData}
									getOptionLabel={(option: RefData) => `${option.ticker} - ${option.companyName}`}
									onChange={(_e, value) => setSecurity(value ? value.ticker : '')}
									renderInput={(params) => (
										<TextField
											{...params}
											label="Security"
											placeholder="Search ticker or company..."
											fullWidth
										/>
									)}
									renderOption={(props, option: RefData) => (
										<Box component="li" {...props}>
											<Box>
												<Typography variant="body2" sx={{ fontWeight: 600 }}>
													{option.ticker}
												</Typography>
												<Typography variant="caption" sx={{ color: '#6b7280' }}>
													{option.companyName}
												</Typography>
											</Box>
										</Box>
									)}
								/>
							</Grid>
							<Grid item xs={12} sm={6}>
								<TextField
									type="number"
									label="Quantity"
									value={quantity}
									onChange={(e) => setQuantity(e.target.value)}
									fullWidth
									inputProps={{ min: 1 }}
								/>
							</Grid>
							<Grid item xs={12} sm={6}>
								<Box>
									<Typography variant="caption" sx={{ color: '#9ca3af', mb: 1, display: 'block' }}>
										Side
									</Typography>
									<ToggleButtonGroup
										value={side}
										exclusive
										onChange={handleToggleChange}
										fullWidth
										size="medium"
									>
										<ToggleButton
											value="Buy"
											sx={{
												color: '#10b981',
												borderColor: 'rgba(255,255,255,0.15)',
												'&.Mui-selected': {
													bgcolor: 'rgba(16, 185, 129, 0.15)',
													color: '#10b981',
													borderColor: '#10b981',
													'&:hover': { bgcolor: 'rgba(16, 185, 129, 0.25)' },
												},
											}}
										>
											Buy
										</ToggleButton>
										<ToggleButton
											value="Sell"
											sx={{
												color: '#ef4444',
												borderColor: 'rgba(255,255,255,0.15)',
												'&.Mui-selected': {
													bgcolor: 'rgba(239, 68, 68, 0.15)',
													color: '#ef4444',
													borderColor: '#ef4444',
													'&:hover': { bgcolor: 'rgba(239, 68, 68, 0.25)' },
												},
											}}
										>
											Sell
										</ToggleButton>
									</ToggleButtonGroup>
								</Box>
							</Grid>
						</Grid>
					)}
				</DialogContent>

				<DialogActions sx={{ px: 3, pb: 2.5, pt: 1 }}>
					<Button onClick={handleClose} sx={{ color: '#9ca3af' }}>
						Cancel
					</Button>
					<Button
						onClick={handleSubmit}
						variant="contained"
						disabled={!isFormValid || submitting}
						sx={{
							bgcolor: side === 'Buy' ? '#10b981' : side === 'Sell' ? '#ef4444' : '#3b82f6',
							'&:hover': {
								bgcolor: side === 'Buy' ? '#059669' : side === 'Sell' ? '#dc2626' : '#2563eb',
							},
							minWidth: 120,
						}}
					>
						{submitting ? <CircularProgress size={20} color="inherit" /> : `Submit ${side || ''} Order`}
					</Button>
				</DialogActions>
			</Dialog>

			<Snackbar
				open={snackbar.open}
				autoHideDuration={4000}
				onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
				anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
			>
				<Alert
					onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
					severity={snackbar.severity}
					variant="filled"
					sx={{ width: '100%' }}
				>
					{snackbar.message}
				</Alert>
			</Snackbar>
		</>
	);
};
