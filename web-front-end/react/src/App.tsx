import './App.css';
import { Datatable } from './Datatable/Datatable';
import React, { useEffect, useState } from 'react';
import { TenantProvider, useTenant, TENANTS, TenantId } from './TenantContext';
import { setCurrentTenant } from './fetchWithTenant';
import { reconnectSocket } from './socket';
import * as socketModule from './socket';
import { ErrorDialog } from './ErrorDialog';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import MenuItem from '@mui/material/MenuItem';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import FormControl from '@mui/material/FormControl';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';

const TenantSelector = () => {
  const { tenant, setTenant } = useTenant();

  const handleTenantChange = (event: SelectChangeEvent<string>) => {
    const newTenant = event.target.value as TenantId;
    setCurrentTenant(newTenant);
    reconnectSocket(newTenant);
    setTenant(newTenant);
  };

  return (
    <FormControl size="small" sx={{ minWidth: 160 }}>
      <Select
        value={tenant}
        onChange={handleTenantChange}
        sx={{
          color: '#e5e7eb',
          '.MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255,255,255,0.15)',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255,255,255,0.3)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#3b82f6',
          },
          '.MuiSvgIcon-root': { color: '#9ca3af' },
          fontSize: '0.875rem',
        }}
      >
        {TENANTS.map((t) => (
          <MenuItem key={t} value={t}>
            {t.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

const ConnectionStatus = () => {
  const { tenant } = useTenant();
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const checkConnection = () => {
      setConnected(socketModule.socket.connected);
    };

    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    checkConnection();
    const interval = setInterval(checkConnection, 2000);

    const currentSocket = socketModule.socket;
    currentSocket.on('connect', onConnect);
    currentSocket.on('disconnect', onDisconnect);

    return () => {
      clearInterval(interval);
      currentSocket.off('connect', onConnect);
      currentSocket.off('disconnect', onDisconnect);
    };
  }, [tenant]);

  return (
    <Chip
      icon={
        <FiberManualRecordIcon
          sx={{ fontSize: 10, color: connected ? '#10b981' : '#ef4444' }}
        />
      }
      label={connected ? 'Connected' : 'Disconnected'}
      size="small"
      variant="outlined"
      sx={{
        borderColor: 'rgba(255,255,255,0.15)',
        color: '#9ca3af',
        fontSize: '0.75rem',
        height: 28,
        '& .MuiChip-icon': { marginLeft: '8px' },
      }}
    />
  );
};

function App() {
  return (
    <TenantProvider>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppBar
          position="static"
          elevation={0}
          sx={{
            bgcolor: '#0d1321',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <Toolbar sx={{ justifyContent: 'space-between', minHeight: '56px !important' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <ShowChartIcon sx={{ color: '#3b82f6', fontSize: 28 }} />
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                TraderX
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <ConnectionStatus />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" sx={{ color: '#6b7280', fontWeight: 500 }}>
                  TENANT
                </Typography>
                <TenantSelector />
              </Box>
            </Box>
          </Toolbar>
        </AppBar>
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Datatable />
        </Box>
      </Box>
      <ErrorDialog />
    </TenantProvider>
  );
}

export default App;
