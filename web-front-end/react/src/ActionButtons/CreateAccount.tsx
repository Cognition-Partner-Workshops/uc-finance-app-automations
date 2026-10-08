import React, { useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import CircularProgress from '@mui/material/CircularProgress';
import CloseIcon from '@mui/icons-material/Close';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import { Environment } from '../env';
import { apiFetch } from '../apiFetch';

export const CreateAccount = () => {
	const [open, setOpen] = useState(false);
	const [displayName, setDisplayName] = useState('');
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState('');
	const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
		open: false,
		message: '',
		severity: 'success',
	});

	const handleOpen = () => {
		setOpen(true);
		setDisplayName('');
		setError('');
	};

	const handleClose = () => setOpen(false);

	const handleSubmit = async () => {
		if (!displayName.trim()) {
			setError('Display name is required');
			return;
		}
		const accountId = Math.floor(Math.random() * 10000);
		setSubmitting(true);
		setError('');
		try {
			const response = await apiFetch(`${Environment.account_service_url}/account/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					id: accountId,
					displayName: displayName.trim(),
				}),
			});
			if (response.ok) {
				setSnackbar({ open: true, message: 'Account created successfully', severity: 'success' });
				setOpen(false);
			} else {
				setSnackbar({ open: true, message: 'Failed to create account', severity: 'error' });
			}
		} catch (err) {
			setSnackbar({ open: true, message: 'Error creating account', severity: 'error' });
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<>
			<Button
				onClick={handleOpen}
				variant="outlined"
				startIcon={<AccountBalanceIcon />}
				size="small"
				sx={{
					borderColor: 'rgba(255,255,255,0.15)',
					color: '#e5e7eb',
					'&:hover': { borderColor: 'rgba(255,255,255,0.3)', bgcolor: 'rgba(255,255,255,0.04)' },
				}}
			>
				New Account
			</Button>

			<Dialog
				open={open}
				onClose={handleClose}
				maxWidth="xs"
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
						Create Account
					</Typography>
					<IconButton onClick={handleClose} size="small" sx={{ color: '#6b7280' }}>
						<CloseIcon />
					</IconButton>
				</DialogTitle>

				<DialogContent sx={{ pt: 2 }}>
					<TextField
						label="Display Name"
						value={displayName}
						onChange={(e) => setDisplayName(e.target.value)}
						fullWidth
						autoFocus
						error={!!error}
						helperText={error}
						sx={{ mt: 1 }}
						onKeyDown={(e) => {
							if (e.key === 'Enter') handleSubmit();
						}}
					/>
				</DialogContent>

				<DialogActions sx={{ px: 3, pb: 2.5, pt: 1 }}>
					<Button onClick={handleClose} sx={{ color: '#9ca3af' }}>
						Cancel
					</Button>
					<Button
						onClick={handleSubmit}
						variant="contained"
						disabled={!displayName.trim() || submitting}
						sx={{ bgcolor: '#3b82f6', '&:hover': { bgcolor: '#2563eb' }, minWidth: 100 }}
					>
						{submitting ? <CircularProgress size={20} color="inherit" /> : 'Create'}
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
