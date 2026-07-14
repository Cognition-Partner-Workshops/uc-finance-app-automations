import React, { useEffect, useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { API_ERROR_EVENT, ApiErrorDetail } from './fetchWithTenant';

function parseMessage(body: string): string {
  if (!body) {
    return 'Internal Server Error';
  }
  try {
    const parsed = JSON.parse(body);
    if (parsed && typeof parsed.detail === 'string') {
      return parsed.detail;
    }
  } catch {
    // body is not JSON; fall through to raw text
  }
  return body;
}

export const ErrorDialog = () => {
  const [error, setError] = useState<ApiErrorDetail | null>(null);

  useEffect(() => {
    const handler = (event: Event) => {
      setError((event as CustomEvent<ApiErrorDetail>).detail);
    };
    window.addEventListener(API_ERROR_EVENT, handler);
    return () => window.removeEventListener(API_ERROR_EVENT, handler);
  }, []);

  const handleClose = () => setError(null);

  return (
    <Dialog
      open={error !== null}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: '#111827',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 2,
        },
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, pb: 1 }}>
        <ErrorOutlineIcon sx={{ color: '#ef4444', fontSize: 28 }} />
        <Typography variant="h6" sx={{ fontWeight: 700, color: '#ef4444' }}>
          Application Error
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Typography variant="body2" sx={{ color: '#e5e7eb', mb: 2 }}>
          The server encountered an unexpected error while handling this request. The
          issue has been reported for investigation.
        </Typography>

        {error && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`HTTP ${error.status}`}
                size="small"
                sx={{ bgcolor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontWeight: 700 }}
              />
              <Typography
                variant="body2"
                sx={{ fontFamily: 'monospace', color: '#9ca3af' }}
              >
                {error.method} {error.endpoint}
              </Typography>
            </Box>

            <Box
              sx={{
                bgcolor: '#0d1321',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 1,
                p: 1.5,
              }}
            >
              <Typography
                variant="body2"
                sx={{ fontFamily: 'monospace', color: '#f87171', whiteSpace: 'pre-wrap' }}
              >
                {parseMessage(error.body)}
              </Typography>
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2.5 }}>
        <Button
          onClick={handleClose}
          variant="contained"
          sx={{ bgcolor: '#ef4444', '&:hover': { bgcolor: '#dc2626' }, minWidth: 100 }}
        >
          Dismiss
        </Button>
      </DialogActions>
    </Dialog>
  );
};
