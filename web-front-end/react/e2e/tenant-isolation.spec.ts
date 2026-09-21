import { test, expect } from '@playwright/test';
import { ACME_CORP, GLOBEX_INC, GOLDEN_TENANTS, INITECH, foreignAccounts } from './fixtures/golden-data';
import {
  accountOptionName,
  emptyState,
  errorDialog,
  listAccountOptions,
  openApp,
  readBlotter,
  selectAccount,
  selectTenant,
} from './helpers/traderx';

/**
 * Multi-tenant category from .devin/skills/add-integration-test: data created
 * (here: seeded) in tenant A must not be visible when tenant B is selected.
 */
test.describe('tenant isolation', () => {
  for (const tenant of GOLDEN_TENANTS) {
    test(`${tenant.id} never lists accounts owned by other tenants`, async ({ page }) => {
      await openApp(page);
      await selectTenant(page, tenant);

      const options = await listAccountOptions(page);
      for (const foreign of foreignAccounts(tenant)) {
        expect(options.some((o) => accountOptionName(foreign).test(o))).toBe(false);
        expect(options.some((o) => o.includes(`#${foreign.id}`))).toBe(false);
      }
    });
  }

  test('acme_corp positions disappear after switching to globex_inc', async ({ page }) => {
    await openApp(page);
    const acmeAccount = ACME_CORP.accounts[0];
    await selectAccount(page, acmeAccount);
    const acmePositions = await readBlotter(page, 'Position Blotter');
    expect(acmePositions.map((p) => p.security)).toContain('AAPL');

    await selectTenant(page, GLOBEX_INC);

    await expect(emptyState(page)).toBeVisible();
    await expect(page.getByRole('gridcell', { name: 'AAPL' })).toHaveCount(0);

    const [globexAccount] = GLOBEX_INC.accounts;
    await selectAccount(page, globexAccount);
    const globexPositions = await readBlotter(page, 'Position Blotter');
    expect(globexPositions.map((p) => p.security).sort()).toEqual(
      globexAccount.positions.map((p) => p.security).sort()
    );
    expect(globexPositions.map((p) => p.security)).not.toContain('AAPL');
  });

  test('a security held by two tenants shows only the current tenant quantity', async ({ page }) => {
    // AAPL is held by acme_corp/22214 (70) and initech/62654 (300).
    await openApp(page);
    await selectAccount(page, ACME_CORP.accounts[0]);
    const acme = await readBlotter(page, 'Position Blotter');
    expect(acme.find((p) => p.security === 'AAPL')?.quantity).toBe('70');

    await selectTenant(page, INITECH);
    await selectAccount(page, INITECH.accounts[0]);
    const initech = await readBlotter(page, 'Position Blotter');
    expect(initech.find((p) => p.security === 'AAPL')?.quantity).toBe('300');
    await expect(errorDialog(page)).toHaveCount(0);
  });

  test('backend rejects cross-tenant reads of a foreign account', async ({ request }) => {
    const backend = process.env.E2E_BACKEND_URL || 'http://localhost:8000';
    const acmeAccount = ACME_CORP.accounts[0];

    const own = await request.get(`${backend}/positions/${acmeAccount.id}`, {
      headers: { 'X-Tenant-ID': ACME_CORP.id },
    });
    expect(own.ok()).toBe(true);
    expect(await own.json()).toHaveLength(acmeAccount.positions.length);

    for (const other of [GLOBEX_INC, INITECH]) {
      const cross = await request.get(`${backend}/positions/${acmeAccount.id}`, {
        headers: { 'X-Tenant-ID': other.id },
      });
      expect(cross.ok()).toBe(true);
      expect(await cross.json()).toEqual([]);
    }
  });
});
