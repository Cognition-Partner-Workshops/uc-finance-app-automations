import React, { useCallback, useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import CloseIcon from '@mui/icons-material/Close';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { ActionButtonsProps } from './types';
import { Environment } from '../env';
import { apiFetch } from '../apiFetch';

interface PersonOption {
	logonId: string;
	fullName: string;
}

export const CreateAccountUser = ({ accountId }: ActionButtonsProps) => {
	const [open, setOpen] = useState(false);
	const [username, setUsername] = useState('');
	const [searchText, setSearchText] = useState('');
	const [peopleOptions, setPeopleOptions] = useState<PersonOption[]>([]);
	const [searching, setSearching] = useState(false);
	const [submitting, setSubmitting] = useState(false);
	const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
		open: false,
		message: '',
		severity: 'success',
	});

	const handleOpen = () => {
		setOpen(true);
		setUsername('');
		setSearchText('');
		setPeopleOptions([]);
	};

	const handleClose = () => setOpen(false);

	const searchPeople = useCallback(async (text: string) => {
		if (!text || text.length < 2) {
			setPeopleOptions([]);
			return;
		}
		setSearching(true);
		try {
			const response = await apiFetch(
				`${Environment.people_service_url}/people/GetMatchingPeople?SearchText=${encodeURIComponent(text)}`
			);
			const result = await response.json();
				const people = (result.People || result) as Array<Record<string, string>>;
				setPeopleOptions(
					people.map((p) => ({
						logonId: p.logonId || p.LogonId || '',
						fullName: p.fullName || p.FullName || '',
					}))
				);
		} catch (error) {
			console.error('Failed to search people:', error);
		} finally {
			setSearching(false);
		}
	}, []);

	const handleSubmit = async () => {
		if (!username) return;
		setSubmitting(true);
		try {
			const response = await apiFetch(`${Environment.account_service_url}/accountuser/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					accountId,
					username,
				}),
			});
			if (response.ok) {
				setSnackbar({ open: true, message: 'Account user created successfully', severity: 'success' });
				setOpen(false);
			} else {
				setSnackbar({ open: true, message: 'Failed to create account user', severity: 'error' });
			}
		} catch (error) {
			setSnackbar({ open: true, message: 'Error creating account user', severity: 'error' });
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<>
			<Button
				onClick={handleOpen}
				variant="outlined"
				startIcon={<PersonAddIcon />}
				size="small"
				sx={{
					borderColor: 'rgba(255,255,255,0.15)',
					color: '#e5e7eb',
					'&:hover': { borderColor: 'rgba(255,255,255,0.3)', bgcolor: 'rgba(255,255,255,0.04)' },
				}}
			>
				Add User
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
						Add Account User
					</Typography>
					<IconButton onClick={handleClose} size="small" sx={{ color: '#6b7280' }}>
						<CloseIcon />
					</IconButton>
				</DialogTitle>

				<DialogContent sx={{ pt: 2 }}>
					<Autocomplete
						freeSolo
						options={peopleOptions}
						getOptionLabel={(option) =>
							typeof option === 'string' ? option : `${option.fullName} (${option.logonId})`
						}
						loading={searching}
						inputValue={searchText}
						onInputChange={(_e, value) => {
							setSearchText(value);
							searchPeople(value);
						}}
						onChange={(_e, value) => {
							if (value && typeof value !== 'string') {
								setUsername(value.logonId);
							} else if (typeof value === 'string') {
								setUsername(value);
							} else {
								setUsername('');
							}
						}}
						renderInput={(params) => (
							<TextField
								{...params}
								label="Search People"
								placeholder="Type to search by name..."
								fullWidth
								sx={{ mt: 1 }}
								InputProps={{
									...params.InputProps,
									endAdornment: (
										<>
											{searching ? <CircularProgress color="inherit" size={20} /> : null}
											{params.InputProps.endAdornment}
										</>
									),
								}}
							/>
						)}
						renderOption={(props, option) => (
							<Box component="li" {...props}>
								<Box>
									<Typography variant="body2" sx={{ fontWeight: 600 }}>
										{option.fullName}
									</Typography>
									<Typography variant="caption" sx={{ color: '#6b7280' }}>
										{option.logonId}
									</Typography>
								</Box>
							</Box>
						)}
					/>
					{username && (
						<Typography variant="caption" sx={{ color: '#10b981', mt: 1, display: 'block' }}>
							Selected: {username}
						</Typography>
					)}
				</DialogContent>

				<DialogActions sx={{ px: 3, pb: 2.5, pt: 1 }}>
					<Button onClick={handleClose} sx={{ color: '#9ca3af' }}>
						Cancel
					</Button>
					<Button
						onClick={handleSubmit}
						variant="contained"
						disabled={!username || submitting}
						sx={{ bgcolor: '#3b82f6', '&:hover': { bgcolor: '#2563eb' }, minWidth: 100 }}
					>
						{submitting ? <CircularProgress size={20} color="inherit" /> : 'Add User'}
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
