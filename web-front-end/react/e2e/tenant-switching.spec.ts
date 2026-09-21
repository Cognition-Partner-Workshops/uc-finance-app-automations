import { test, expect } from '@playwright/test';
import { ACME_CORP, GLOBEX_INC, GOLDEN_TENANTS, INITECH } from './fixtures/golden-data';
import {
  accountOptionName,
  connectionChip,
  emptyState,
  errorDialog,
  listAccountOptions,
  openApp,
  readBlotter,
  selectAccount,
  selectTenant,
  tenantSelect,
} from './helpers/traderx';

test.describe('tenant switching', () => {
  test('tenant dropdown offers exactly the three golden tenants', async ({ page }) => {
    await openApp(page);

    await tenantSelect(page).click();
    const options = page.getByRole('listbox').getByRole('option');
    await expect(options).toHaveText(GOLDEN_TENANTS.map((t) => t.label));
    await page.keyboard.press('Escape');
  });

  for (const tenant of GOLDEN_TENANTS) {
    test(`switching to ${tenant.id} lists its ${tenant.counts.accounts} golden accounts`, async ({
      page,
    }) => {
      await openApp(page);
      await selectTenant(page, tenant);

      const options = await listAccountOptions(page);
      expect(options).toHaveLength(tenant.counts.accounts);
      for (const account of tenant.accounts) {
        expect(options.some((o) => accountOptionName(account).test(o))).toBe(true);
      }
      await expect(errorDialog(page)).toHaveCount(0);
    });

    test(`${tenant.id}: every account's blotters match the golden positions`, async ({ page }) => {
      await openApp(page);
      await selectTenant(page, tenant);

      let totalTrades = 0;
      let totalPositions = 0;
      for (const account of tenant.accounts) {
        await selectAccount(page, account);

        const positions = await readBlotter(page, 'Position Blotter');
        expect(positions.map((p) => p.security).sort()).toEqual(
          account.positions.map((p) => p.security).sort()
        );

        totalTrades += account.trades.length;
        totalPositions += account.positions.length;
      }
      expect(totalTrades).toBe(tenant.counts.trades);
      expect(totalPositions).toBe(tenant.counts.positions);
    });
  }

  test('switching tenant resets the account selection and blotters', async ({ page }) => {
    await openApp(page);
    await selectAccount(page, ACME_CORP.accounts[0]);
    await expect(page.getByText('Trade Blotter', { exact: true })).toBeVisible();

    await selectTenant(page, GLOBEX_INC);

    await expect(emptyState(page)).toBeVisible();
    await expect(page.getByText('Trade Blotter', { exact: true })).toHaveCount(0);
    await expect(
      page.getByRole('heading', { name: `#${ACME_CORP.accounts[0].id}`, exact: true })
    ).toHaveCount(0);
  });

  test('round-tripping tenants restores the original data', async ({ page }) => {
    await openApp(page);
    await selectTenant(page, INITECH);
    await selectTenant(page, GLOBEX_INC);
    await selectTenant(page, ACME_CORP);

    const [account] = ACME_CORP.accounts;
    await selectAccount(page, account);
    const positions = await readBlotter(page, 'Position Blotter');
    expect(positions).toHaveLength(account.positions.length);
  });

  test('socket reconnects for the new tenant', async ({ page }) => {
    await openApp(page);
    await expect(connectionChip(page)).toHaveText('Connected');

    await selectTenant(page, INITECH);

    await expect(connectionChip(page)).toHaveText('Connected');
  });
});
