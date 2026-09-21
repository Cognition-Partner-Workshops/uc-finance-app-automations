import { expect, Locator, Page } from '@playwright/test';
import { GoldenAccount, GoldenTenant } from '../fixtures/golden-data';

export type BlotterName = 'Trade Blotter' | 'Position Blotter';

/** Text rendered in a grid cell, keyed by ag-grid `col-id` (the `field` in Datatable.tsx). */
export type GridRecord = Record<string, string>;

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export async function openApp(page: Page): Promise<void> {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'TraderX' })).toBeVisible();
}

/** The tenant `Select` lives in the header (MUI AppBar renders a `<header>` / banner). */
export function tenantSelect(page: Page): Locator {
  return page.getByRole('banner').getByRole('combobox');
}

export function connectionChip(page: Page): Locator {
  return page.getByText(/^(Connected|Disconnected)$/);
}

/** The account `Select` is labelled "Select Account" by an adjacent InputLabel. */
export function accountSelect(page: Page): Locator {
  return page.getByText('Select Account', { exact: true }).locator('..').getByRole('combobox');
}

export function accountsCountChip(page: Page, count: number): Locator {
  return page.getByText(`${count} accounts`, { exact: true });
}

export function errorDialog(page: Page): Locator {
  return page.getByRole('dialog').filter({ hasText: 'Application Error' });
}

export function emptyState(page: Page): Locator {
  return page.getByRole('heading', { name: 'No Account Selected' });
}

export async function selectTenant(page: Page, tenant: GoldenTenant): Promise<void> {
  const current = (await tenantSelect(page).textContent())?.trim();
  if (current !== tenant.label) {
    await tenantSelect(page).click();
    const accountsLoaded = page.waitForResponse(
      (r) =>
        r.url().endsWith('/account/') &&
        r.request().method() === 'GET' &&
        r.request().headers()['x-tenant-id'] === tenant.id
    );
    await page.getByRole('option', { name: tenant.label, exact: true }).click();
    await accountsLoaded;
  }
  await expect(tenantSelect(page)).toHaveText(tenant.label);
  await expect(accountsCountChip(page, tenant.counts.accounts)).toBeVisible();
}

export function accountOptionName(account: GoldenAccount): RegExp {
  return new RegExp(`^${escapeRegExp(account.displayName)}\\s*#${account.id}$`);
}

/** Opens the account dropdown and returns the visible option labels (excluding "None"). */
export async function listAccountOptions(page: Page): Promise<string[]> {
  await accountSelect(page).click();
  const listbox = page.getByRole('listbox');
  await expect(listbox).toBeVisible();
  const labels = await listbox.getByRole('option').allInnerTexts();
  await page.keyboard.press('Escape');
  await expect(listbox).toBeHidden();
  return labels.map((l) => l.replace(/\s+/g, ' ').trim()).filter((l) => l !== 'None');
}

export async function selectAccount(page: Page, account: GoldenAccount): Promise<void> {
  await accountSelect(page).click();
  await page.getByRole('option', { name: accountOptionName(account) }).click();
  await expect(page.getByRole('heading', { name: `#${account.id}`, exact: true })).toBeVisible();
  await expect(blotterCountChip(page, 'Trade Blotter', account.trades.length)).toBeVisible();
  await expect(blotterCountChip(page, 'Position Blotter', account.positions.length)).toBeVisible();
}

export function blotterCard(page: Page, name: BlotterName): Locator {
  return page.locator('.MuiCard-root').filter({ has: page.getByText(name, { exact: true }) });
}

export function blotterCountChip(page: Page, name: BlotterName, count: number): Locator {
  const noun = name === 'Trade Blotter' ? 'trades' : 'positions';
  return blotterCard(page, name).getByText(`${count} ${noun}`, { exact: true });
}

/** ag-grid renders its root with role="treegrid"; body rows are the ones that contain gridcells. */
export function blotterGrid(page: Page, name: BlotterName): Locator {
  return blotterCard(page, name).getByRole('treegrid');
}

export function bodyRows(grid: Locator): Locator {
  return grid.getByRole('row').filter({ has: grid.page().getByRole('gridcell') });
}

export async function readGrid(grid: Locator): Promise<GridRecord[]> {
  const rows = bodyRows(grid);
  const records: GridRecord[] = [];
  for (const row of await rows.all()) {
    records.push(
      await row.getByRole('gridcell').evaluateAll((cells) =>
        Object.fromEntries(
          cells.map((c) => [c.getAttribute('col-id') ?? '', (c.textContent ?? '').trim()])
        )
      )
    );
  }
  return records;
}

export async function readBlotter(page: Page, name: BlotterName): Promise<GridRecord[]> {
  return readGrid(blotterGrid(page, name));
}

/** Position quantities go through QuantityCellRenderer (`toLocaleString`), trades render raw. */
export function formatPositionQuantity(quantity: number): string {
  return quantity.toLocaleString('en-US');
}
