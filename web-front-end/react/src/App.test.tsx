import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import theme from './theme';

test('renders TraderX header', () => {
  render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );
  const headerElement = screen.getByText(/TraderX/i);
  expect(headerElement).toBeInTheDocument();
});

test('renders connection status indicator', () => {
  render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );
  const statusChip = screen.getByText(/Connected|Disconnected/);
  expect(statusChip).toBeInTheDocument();
});
