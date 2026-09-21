/**
 * Golden mock data contract for the TraderX e2e suite.
 *
 * Mirrors the deterministic seed in traderx-monolith/app/seed.py. The backend
 * seeds this data into an empty SQLite DB on first startup, so a fresh backend
 * is guaranteed to serve exactly these accounts, trades and positions.
 *
 * If seed.py changes, this file must change with it — the specs treat these
 * values as the source of truth.
 */

export type TenantId = 'acme_corp' | 'globex_inc' | 'initech';

export type TradeSide = 'Buy' | 'Sell';
export type TradeState = 'New' | 'Processing' | 'Pending' | 'Settled' | 'Cancelled';

export interface GoldenTrade {
  security: string;
  side: TradeSide;
  quantity: number;
  state: TradeState;
}

export interface GoldenPosition {
  security: string;
  quantity: number;
}

export interface GoldenAccount {
  id: number;
  displayName: string;
  trades: GoldenTrade[];
  positions: GoldenPosition[];
}

export interface GoldenTenant {
  id: TenantId;
  /** Label rendered by the tenant dropdown: `id.replace('_', ' ')` title-cased. */
  label: string;
  accounts: GoldenAccount[];
  counts: {
    accounts: number;
    trades: number;
    positions: number;
  };
}

export const ACME_CORP: GoldenTenant = {
  id: 'acme_corp',
  label: 'Acme Corp',
  accounts: [
    {
      id: 22214,
      displayName: 'Test Account 20',
      trades: [
        { security: 'AAPL', side: 'Buy', quantity: 100, state: 'Settled' },
        { security: 'MSFT', side: 'Buy', quantity: 250, state: 'Settled' },
        { security: 'GOOGL', side: 'Buy', quantity: 50, state: 'Settled' },
        { security: 'AAPL', side: 'Sell', quantity: 30, state: 'Settled' },
        { security: 'TSLA', side: 'Buy', quantity: 75, state: 'Settled' },
      ],
      positions: [
        { security: 'AAPL', quantity: 70 },
        { security: 'MSFT', quantity: 250 },
        { security: 'GOOGL', quantity: 50 },
        { security: 'TSLA', quantity: 75 },
      ],
    },
    {
      id: 11413,
      displayName: 'Private Clients Fund TTXX',
      trades: [
        { security: 'JPM', side: 'Buy', quantity: 500, state: 'Settled' },
        { security: 'BAC', side: 'Buy', quantity: 300, state: 'Settled' },
        { security: 'GS', side: 'Buy', quantity: 200, state: 'Settled' },
      ],
      positions: [
        { security: 'JPM', quantity: 500 },
        { security: 'BAC', quantity: 300 },
        { security: 'GS', quantity: 200 },
      ],
    },
  ],
  counts: { accounts: 2, trades: 8, positions: 7 },
};

export const GLOBEX_INC: GoldenTenant = {
  id: 'globex_inc',
  label: 'Globex Inc',
  accounts: [
    {
      id: 42422,
      displayName: 'Algo Execution Partners',
      trades: [
        { security: 'BAC', side: 'Buy', quantity: 1000, state: 'Settled' },
        { security: 'AMZN', side: 'Buy', quantity: 150, state: 'Settled' },
        { security: 'META', side: 'Buy', quantity: 300, state: 'Settled' },
      ],
      positions: [
        { security: 'BAC', quantity: 1000 },
        { security: 'AMZN', quantity: 150 },
        { security: 'META', quantity: 300 },
      ],
    },
    {
      id: 52355,
      displayName: 'Big Corporate Fund',
      trades: [
        { security: 'NVDA', side: 'Buy', quantity: 200, state: 'Settled' },
        { security: 'AMD', side: 'Buy', quantity: 400, state: 'Settled' },
      ],
      positions: [
        { security: 'NVDA', quantity: 200 },
        { security: 'AMD', quantity: 400 },
      ],
    },
  ],
  counts: { accounts: 2, trades: 5, positions: 5 },
};

export const INITECH: GoldenTenant = {
  id: 'initech',
  label: 'Initech',
  accounts: [
    {
      id: 62654,
      displayName: 'Hedge Fund TXY1',
      trades: [
        { security: 'AAPL', side: 'Buy', quantity: 500, state: 'Settled' },
        { security: 'MSFT', side: 'Buy', quantity: 300, state: 'Settled' },
        { security: 'AAPL', side: 'Sell', quantity: 200, state: 'Settled' },
      ],
      positions: [
        { security: 'AAPL', quantity: 300 },
        { security: 'MSFT', quantity: 300 },
      ],
    },
    {
      id: 10031,
      displayName: 'Internal Trading Book',
      trades: [
        { security: 'GOOGL', side: 'Buy', quantity: 100, state: 'Processing' },
        { security: 'TSLA', side: 'Buy', quantity: 150, state: 'Settled' },
      ],
      positions: [
        { security: 'GOOGL', quantity: 100 },
        { security: 'TSLA', quantity: 150 },
      ],
    },
    {
      id: 44044,
      displayName: 'Trading Account 1',
      trades: [
        { security: 'NVDA', side: 'Buy', quantity: 250, state: 'Settled' },
        { security: 'AMD', side: 'Buy', quantity: 350, state: 'Settled' },
        { security: 'INTC', side: 'Buy', quantity: 600, state: 'Settled' },
      ],
      positions: [
        { security: 'NVDA', quantity: 250 },
        { security: 'AMD', quantity: 350 },
        { security: 'INTC', quantity: 600 },
      ],
    },
  ],
  counts: { accounts: 3, trades: 8, positions: 7 },
};

export const GOLDEN_TENANTS: readonly GoldenTenant[] = [ACME_CORP, GLOBEX_INC, INITECH];

export const GOLDEN_BY_ID: Record<TenantId, GoldenTenant> = {
  acme_corp: ACME_CORP,
  globex_inc: GLOBEX_INC,
  initech: INITECH,
};

/** Tenant the app boots into (TenantContext default). */
export const DEFAULT_TENANT: GoldenTenant = ACME_CORP;

export const TOTALS = {
  accounts: 7,
  trades: 21,
  positions: 19,
};

/** Accounts belonging to every tenant other than `tenant`. */
export function foreignAccounts(tenant: GoldenTenant): GoldenAccount[] {
  return GOLDEN_TENANTS.filter((t) => t.id !== tenant.id).flatMap((t) => t.accounts);
}
