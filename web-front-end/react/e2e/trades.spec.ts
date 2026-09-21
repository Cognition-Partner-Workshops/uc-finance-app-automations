import { test, expect } from '@playwright/test';
import { ACME_CORP, GOLDEN_TENANTS, INITECH } from './fixtures/golden-data';
import {
  blotterCountChip,
  blotterGrid,
  errorDialog,
  openApp,
  readBlotter,
  selectAccount,
  selectTenant,
} from './helpers/traderx';

const sortTrades = <T extends { security: string; side: string; quantity: string }>(rows: T[]) =>
  [...rows].sort(
    (a, b) =>
      a.security.localeCompare(b.security) ||
      a.side.localeCompare(b.side) ||
      a.quantity.localeCompare(b.quantity)
  );

test.describe('trade blotter', () => {
  test('acme_corp Test Account 20 shows both AAPL trades (Buy 100, Sell 30)', async ({ page }) => {
    await openApp(page);
    const [account] = ACME_CORP.accounts;
    await selectAccount(page, account);

    const grid = blotterGrid(page, 'Trade Blotter');
    for (const header of ['Security', 'Quantity', 'Side', 'State', 'Updated']) {
      await expect(grid.getByRole('columnheader', { name: header })).toBeVisible();
    }

    const aaplRows = grid
      .getByRole('row')
      .filter({ has: page.getByRole('gridcell', { name: 'AAPL', exact: true }) });
    await expect(aaplRows).toHaveCount(2);

    const buy = aaplRows.filter({ hasText: 'Buy' });
    const sell = aaplRows.filter({ hasText: 'Sell' });
    await expect(buy.locator('[col-id="quantity"]')).toHaveText('100');
    await expect(sell.locator('[col-id="quantity"]')).toHaveText('30');
  });

  test('initech Internal Trading Book shows the one Processing trade', async ({ page }) => {
    await openApp(page);
    await selectTenant(page, INITECH);
    const account = INITECH.accounts.find((a) => a.id === 10031)!;
    await selectAccount(page, account);

    const trades = await readBlotter(page, 'Trade Blotter');
    const processing = trades.filter((t) => t.state === 'Processing');
    expect(processing).toHaveLength(1);
    expect(processing[0]).toMatchObject({ security: 'GOOGL', side: 'Buy', quantity: '100' });
    expect(trades.filter((t) => t.state === 'Settled')).toHaveLength(1);
  });

  test('all seeded trades outside initech/10031 are Settled', async ({ page }) => {
    await openApp(page);
    const [account] = ACME_CORP.accounts;
    await selectAccount(page, account);

    const trades = await readBlotter(page, 'Trade Blotter');
    expect(trades).toHaveLength(account.trades.length);
    expect(trades.every((t) => t.state === 'Settled')).toBe(true);
  });

  for (const tenant of GOLDEN_TENANTS) {
    for (const account of tenant.accounts) {
      test(`${tenant.id} / ${account.displayName}: trades match golden data`, async ({ page }) => {
        await openApp(page);
        await selectTenant(page, tenant);
        await selectAccount(page, account);

        await expect(blotterCountChip(page, 'Trade Blotter', account.trades.length)).toBeVisible();

        const rows = await readBlotter(page, 'Trade Blotter');
        const actual = sortTrades(
          rows.map((r) => ({ security: r.security, side: r.side, quantity: r.quantity, state: r.state }))
        );
        const expected = sortTrades(
          account.trades.map((t) => ({
            security: t.security,
            side: t.side,
            quantity: String(t.quantity),
            state: t.state,
          }))
        );
        expect(actual).toEqual(expected);
        await expect(errorDialog(page)).toHaveCount(0);
      });
    }
  }
});
