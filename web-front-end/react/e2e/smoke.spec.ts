import { test, expect } from '@playwright/test';
import { DEFAULT_TENANT } from './fixtures/golden-data';
import {
  accountsCountChip,
  connectionChip,
  emptyState,
  errorDialog,
  openApp,
  tenantSelect,
} from './helpers/traderx';

test.describe('smoke', () => {
  test('app loads with header, tenant selector and connection chip', async ({ page }) => {
    await openApp(page);

    await expect(page.getByRole('heading', { name: 'TraderX' })).toBeVisible();
    await expect(page.getByText('TENANT', { exact: true })).toBeVisible();
    await expect(tenantSelect(page)).toBeVisible();
    await expect(tenantSelect(page)).toHaveText(DEFAULT_TENANT.label);

    await expect(connectionChip(page)).toBeVisible();
    await expect(connectionChip(page)).toHaveText('Connected');
  });

  test('boots into the default tenant with no account selected', async ({ page }) => {
    await openApp(page);

    await expect(accountsCountChip(page, DEFAULT_TENANT.counts.accounts)).toBeVisible();
    await expect(emptyState(page)).toBeVisible();
    await expect(
      page.getByText('Select an account from the dropdown above to view trades and positions')
    ).toBeVisible();
    await expect(errorDialog(page)).toHaveCount(0);
  });

  test('action buttons render', async ({ page }) => {
    await openApp(page);

    await expect(page.getByRole('button', { name: 'New Account' })).toBeVisible();
  });
});
