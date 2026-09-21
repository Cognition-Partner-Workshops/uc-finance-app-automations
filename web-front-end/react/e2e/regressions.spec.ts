import { test, expect } from '@playwright/test';
import { ACME_CORP, DEFAULT_TENANT, GoldenAccount } from './fixtures/golden-data';
import {
  blotterCountChip,
  bodyRows,
  blotterGrid,
  errorDialog,
  openApp,
  selectAccount,
} from './helpers/traderx';

/**
 * UI ports of traderx-monolith/tests/test_error_regressions.py — runtime
 * errors that must never reach the client.
 */
test.describe('error regressions', () => {
  test('an account with no trades or positions shows empty blotters, not an error', async ({ page }) => {
    // Mirrors test_list_positions_for_account_without_positions: the backend
    // answers `[]` (not 404/500) for an account that has never traded. The
    // account list is augmented client-side so the seeded golden data stays
    // untouched; /trades and /positions still hit the real backend.
    const emptyAccount: GoldenAccount = {
      id: 99999,
      displayName: 'No Positions',
      trades: [],
      positions: [],
    };
    await page.route('**/account/', async (route) => {
      if (route.request().method() !== 'GET') {
        return route.continue();
      }
      const response = await route.fetch();
      const accounts = await response.json();
      await route.fulfill({
        response,
        json: [
          ...accounts,
          { id: emptyAccount.id, displayName: emptyAccount.displayName, tenant_id: DEFAULT_TENANT.id },
        ],
      });
    });

    await openApp(page);
    await selectAccount(page, emptyAccount);

    await expect(blotterCountChip(page, 'Trade Blotter', 0)).toBeVisible();
    await expect(blotterCountChip(page, 'Position Blotter', 0)).toBeVisible();
    await expect(bodyRows(blotterGrid(page, 'Trade Blotter'))).toHaveCount(0);
    await expect(bodyRows(blotterGrid(page, 'Position Blotter'))).toHaveCount(0);
    await expect(errorDialog(page)).toHaveCount(0);
  });

  test('a 500 from the backend surfaces the Application Error dialog', async ({ page }) => {
    const [account] = ACME_CORP.accounts;
    await page.route(`**/positions/${account.id}`, (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Injected failure' }),
      })
    );

    await openApp(page);
    await page.getByText('Select Account', { exact: true }).locator('..').getByRole('combobox').click();
    await page.getByRole('option', { name: new RegExp(`#${account.id}$`) }).click();

    const dialog = errorDialog(page);
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('HTTP 500')).toBeVisible();
    await expect(dialog.getByText(`GET /positions/${account.id}`)).toBeVisible();
    await expect(dialog.getByText('Injected failure')).toBeVisible();

    await dialog.getByRole('button', { name: 'Dismiss' }).click();
    await expect(dialog).toHaveCount(0);
  });

  test('reloading keeps the default tenant and golden account count', async ({ page }) => {
    await openApp(page);
    await selectAccount(page, ACME_CORP.accounts[1]);

    await page.reload();

    await expect(page.getByRole('heading', { name: 'TraderX' })).toBeVisible();
    await expect(page.getByText(`${ACME_CORP.counts.accounts} accounts`, { exact: true })).toBeVisible();
    await expect(errorDialog(page)).toHaveCount(0);
  });
});
