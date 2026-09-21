import { test, expect } from '@playwright/test';
import { ACME_CORP, GLOBEX_INC, GOLDEN_TENANTS } from './fixtures/golden-data';
import {
  blotterCountChip,
  blotterGrid,
  errorDialog,
  formatPositionQuantity,
  openApp,
  readBlotter,
  selectAccount,
  selectTenant,
} from './helpers/traderx';

test.describe('positions blotter', () => {
  test('acme_corp Test Account 20 holds AAPL 70 (100 bought, 30 sold)', async ({ page }) => {
    await openApp(page);
    const [account] = ACME_CORP.accounts;
    await selectAccount(page, account);

    const grid = blotterGrid(page, 'Position Blotter');
    await expect(grid.getByRole('columnheader', { name: 'Security' })).toBeVisible();
    await expect(grid.getByRole('columnheader', { name: 'Quantity' })).toBeVisible();

    const aaplRow = grid.getByRole('row').filter({ has: page.getByRole('gridcell', { name: 'AAPL', exact: true }) });
    await expect(aaplRow).toHaveCount(1);
    await expect(aaplRow.locator('[col-id="quantity"]')).toHaveText('70');
  });

  test('summary cards reflect the golden trade and position counts', async ({ page }) => {
    await openApp(page);
    const [account] = ACME_CORP.accounts;
    await selectAccount(page, account);

    const totalTrades = page.locator('.MuiCard-root').filter({ hasText: 'Total Trades' });
    const totalPositions = page.locator('.MuiCard-root').filter({ hasText: 'Total Positions' });
    await expect(totalTrades.getByRole('heading')).toHaveText(String(account.trades.length));
    await expect(totalPositions.getByRole('heading')).toHaveText(String(account.positions.length));
    await expect(page.getByRole('heading', { name: `#${account.id}`, exact: true })).toBeVisible();
  });

  test('large quantities are locale-formatted', async ({ page }) => {
    // globex_inc / Algo Execution Partners holds BAC 1000.
    await openApp(page);
    await selectTenant(page, GLOBEX_INC);
    const [account] = GLOBEX_INC.accounts;
    await selectAccount(page, account);

    const positions = await readBlotter(page, 'Position Blotter');
    expect(positions.find((p) => p.security === 'BAC')?.quantity).toBe(formatPositionQuantity(1000));
  });

  for (const tenant of GOLDEN_TENANTS) {
    for (const account of tenant.accounts) {
      test(`${tenant.id} / ${account.displayName}: positions match golden data`, async ({ page }) => {
        await openApp(page);
        await selectTenant(page, tenant);
        await selectAccount(page, account);

        await expect(
          blotterCountChip(page, 'Position Blotter', account.positions.length)
        ).toBeVisible();

        const rows = await readBlotter(page, 'Position Blotter');
        const actual = rows
          .map((r) => ({ security: r.security, quantity: r.quantity }))
          .sort((a, b) => a.security.localeCompare(b.security));
        const expected = account.positions
          .map((p) => ({ security: p.security, quantity: formatPositionQuantity(p.quantity) }))
          .sort((a, b) => a.security.localeCompare(b.security));
        expect(actual).toEqual(expected);
        await expect(errorDialog(page)).toHaveCount(0);
      });
    }
  }
});
