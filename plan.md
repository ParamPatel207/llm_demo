# AI Hedge Fund — Oscillation Bot (Robinhood MCP)

## Project Overview

Build a permissioned AI trading agent that:

1. Scans an **AI-stock universe** for **oscillating** (mean-reverting / range-bound) tickers
2. Scores **bottom-of-curve** buy opportunities
3. Runs a full **fundamentals + market research** review before any trade suggestion
4. Surfaces candidates for **explicit human approval**
5. Executes only after permission via **Robinhood Trading MCP** into a dedicated Agentic account

This is **not** fully autonomous trading by default. The bot proposes; the user approves; Robinhood MCP places the order.

> Not financial advice. Trading involves risk of loss. Robinhood Agentic Trading executes real orders in a funded Agentic account (no official paper mode).

---

## Product Goals

| Goal | Behavior |
|------|----------|
| Find oscillating AI names | Detect range-bound / mean-reverting price action |
| Buy near curve bottom | Signal when price is near support / lower band / local trough |
| Review fundamentals | Gate candidates on valuation, growth, balance sheet, earnings quality |
| Market research | News, sentiment, catalysts, bull/bear thesis before approval |
| Permissioned execution | No live order without user approve (or explicit auto-mode later) |
| Robinhood MCP | Quotes, portfolio, watchlists, `review_equity_order` → `place_equity_order` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard / Agent UI                                       │
│  - Oscillators board  - Candidate cards  - Approve / Reject │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
┌───────────────▼───────────────┐   ┌─────────▼──────────────┐
│  Strategy Engine (local)      │   │  Research Agent (LLM)  │
│  - Universe filter (AI)       │   │  - Fundamentals digest │
│  - Oscillation detector       │   │  - News / thesis       │
│  - Bottom-of-curve scorer     │   │  - Risk flags          │
│  - Position / risk rules      │   └─────────┬──────────────┘
└───────────────┬───────────────┘             │
                │                             │
┌───────────────▼─────────────────────────────▼──────────────┐
│  Data + Execution Layer                                     │
│  A) Market data & fundamentals (FMP / Alpha Vantage / etc.) │
│  B) Robinhood Trading MCP (quotes, portfolio, orders)       │
│  C) Mock RH MCP adapter for local dry-run (paper)           │
└────────────────────────────────────────────────────────────┘
```

### Core services

| Service | Must run? | Role |
|---------|-----------|------|
| Strategy API (FastAPI) | MUST | Scan, score, approval queue, risk checks |
| Research worker | MUST | Fundamentals + news synthesis for candidates |
| Robinhood Trading MCP | MUST (live) | Official execution + portfolio + quotes |
| Mock Robinhood MCP | OPTIONAL (dev) | Paper mirror for safe local testing |
| Frontend dashboard | MUST | Select tickers, approve buys, view research |
| Price/fundamentals data provider | MUST | Oscillation math + fundamental gates |

---

## 1. Robinhood MCP Integration

### Official endpoint

- **URL:** `https://agent.robinhood.com/mcp/trading`
- **Auth:** OAuth via Robinhood (desktop onboarding)
- **Trade sandbox:** Dedicated **Agentic account** only (other accounts read-only)
- **Cursor:** Settings → Tools & MCPs → Connect with the MCP URL above

### Tool surface (use in trade loop)

| Class | Tools | Use in this product |
|-------|-------|---------------------|
| Account / portfolio | `get_accounts`, `get_portfolio`, `get_equity_positions`, `get_equity_orders` | Buying power, exposure, open positions |
| Market data | `get_equity_quotes`, `get_equity_tradability`, `search`, `get_popular_lists` | Live quote at signal / order time |
| Watchlists | get/create/update, add/remove items | Track oscillating AI watchlist |
| Equity orders | `review_equity_order`, `place_equity_order`, `cancel_equity_order` | **Always review before place** |

### Permissioned execution flow (required)

```
signal → fundamentals gate → research brief → user APPROVE
  → review_equity_order (Robinhood MCP)
  → show preview (cost, alerts)
  → user CONFIRM
  → place_equity_order (idempotent ref_id)
  → poll get_equity_orders / get_portfolio
```

Hard rules:

- Default mode: **manual approve** for every order
- Never place without a prior successful `review_equity_order`
- Cap size by % of Agentic buying power and per-ticker max
- Kill switch: disconnect MCP / pause bot in UI

### Dev vs live

| Mode | Adapter | Money |
|------|---------|-------|
| `DRY_RUN` | Mock RH MCP (yfinance + paper ledger) | Fake |
| `LIVE` | Official Robinhood Trading MCP | Real Agentic account |

Robinhood has **no official paper trading** for Agentic MCP. Develop against mock; go live only after dry-run confidence.

### User setup checklist (live)

1. Primary Robinhood individual account in good standing
2. Connect agent to `https://agent.robinhood.com/mcp/trading`
3. Complete desktop Agentic account onboarding
4. Fund Agentic account separately
5. Keep main portfolio read-only for the agent

---

## 2. Market Research Integration

Research runs **after** technical oscillation/bottom signals and **before** approval UI.

### Research inputs

| Source | Purpose |
|--------|---------|
| Robinhood MCP quotes / tradability | Confirm liquid & tradable now |
| News + sentiment API (e.g. Alpha Vantage `NEWS_SENTIMENT`, Tiingo, or FMP news) | Catalysts, tone, recent headlines |
| Earnings calendar / surprises | Avoid buying into binary events blindly |
| Optional web search (Tavily) | Fresh narrative for AI supply-chain names |
| LLM synthesis | Structured bull / bear / “why now” brief |

### Research output (stored per candidate)

```json
{
  "symbol": "NVDA",
  "as_of": "ISO-8601",
  "headline_summary": "...",
  "sentiment": {"score": 0.0, "label": "neutral|bullish|bearish"},
  "catalysts": ["..."],
  "risks": ["earnings in 3d", "guidance cut"],
  "bull_thesis": "...",
  "bear_thesis": "...",
  "trade_bias": "buy_dip|wait|avoid",
  "confidence": 0.0
}
```

Research can **block** or **downgrade** a candidate (e.g. imminent earnings, fraud rumor, halt risk) even if technicals look like a bottom.

---

## 3. Fundamentals Review (full checklist)

Every oscillating candidate must pass a fundamentals pack before it reaches the approval queue.

### Data provider (default)

- **Primary:** Financial Modeling Prep (statements, ratios TTM, key metrics, earnings)
- **Fallback / tech overlays:** Alpha Vantage (`OVERVIEW`, indicators, news sentiment)

### Fundamental dimensions to review

#### A. Valuation

- [ ] P/E (TTM) vs sector / own history
- [ ] Forward P/E / PEG if available
- [ ] P/S, P/B, EV/EBITDA
- [ ] Flag extreme premium without growth support

#### B. Growth & quality

- [ ] Revenue growth (YoY, QoQ)
- [ ] EPS growth / earnings surprise history
- [ ] Gross margin & operating margin trend
- [ ] Free cash flow (positive / improving?)

#### C. Balance sheet & leverage

- [ ] Current ratio / quick ratio
- [ ] Debt-to-equity, interest coverage
- [ ] Cash vs short-term debt
- [ ] Dilution / share count trend

#### D. Profitability & efficiency

- [ ] ROE, ROA, ROIC
- [ ] Asset turnover where relevant
- [ ] Rule-of-40 style view for growth software (rev growth + FCF margin)

#### E. AI-thesis fit (universe filter)

- [ ] Business is AI-related (chips, cloud, models, infra, apps, data)
- [ ] Revenue exposure narrative from filings / research brief
- [ ] Not purely meme / zero-fundamentals unless user opts into speculative mode

#### F. Event & governance risks

- [ ] Next earnings date distance
- [ ] Recent guidance changes
- [ ] Outstanding litigation / audit flags (best-effort from news)
- [ ] Tradability on Robinhood (`get_equity_tradability`)

### Fundamentals scorecard

| Grade | Meaning | Default action |
|-------|---------|----------------|
| A / B | Healthy or acceptable for dip-buy | Eligible for approval queue |
| C | Mixed; research must justify | Eligible only with explicit user override |
| D / F | Weak BS, deteriorating FCF, or broken thesis | Auto-reject (unless speculative mode) |

Store raw ratios + scorecard on each candidate so the UI can show “why this passed.”

---

## 4. Oscillation + Bottom-of-Curve Logic

### Universe

Curated AI watchlist (editable), e.g.:

`NVDA, AMD, AVGO, TSM, ASML, MSFT, GOOGL, AMZN, META, PLTR, SNOW, CRM, NOW, PATH, AI, SMCI, ARM, MU, INTC, QCOM`

Plus optional discovery via Robinhood popular lists / search filtered by AI tags.

### Oscillation detection (mean-reversion bias)

Prefer names that **range** rather than strong one-way trends:

- Bollinger Band width (relatively tight / mean-reverting)
- Multiple touches of rolling support & resistance
- RSI cycling (not stuck overbought/oversold for long stretches)
- Optional: Hurst exponent &lt; 0.5 (mean-reverting)
- Reject strong ADX trend breakouts unless user enables trend mode

### Bottom-of-curve entry

Buy candidates when several confirm:

- Price near lower Bollinger / rolling support
- RSI recovering from oversold (e.g. cross up from &lt; 30–35)
- Local trough vs N-day low with volume confirmation
- Not breaking down on high volume (trap filter)

Output: `oscillation_score`, `bottom_score`, `suggested_size`, `invalidation_level` (stop / thesis fail).

---

## 5. End-to-End User Flow

1. Bot scans AI universe on schedule (or on demand)
2. Rank oscillating tickers; highlight bottoms
3. User selects which names to consider (or auto-queue top N)
4. System pulls **full fundamentals** + **market research**
5. Candidate card: chart context, scores, fundamentals grade, research brief
6. User taps **Approve buy** (amount / shares)
7. Bot calls Robinhood `review_equity_order` → shows preview
8. User confirms → `place_equity_order`
9. UI shows fill / order status from `get_equity_orders`
10. Optional: watch for exit / rebalance rules (phase 2)

---

## Implementation Checklist

### Phase 0: Product & safety baseline

- [ ] Replace legacy LangChain/MCP demo scope with this plan (this file)
- [ ] Define risk defaults: max % buying power, max per ticker, approve-only mode
- [ ] Document Robinhood Agentic risks & disconnect kill switch

### Phase 1: Project skeleton

- [ ] New app layout under `src/` (api, strategy, research, brokers, ui)
- [ ] `requirements.txt` for FastAPI, pandas, numpy, httpx, pydantic, MCP client libs
- [ ] `.env.example`: data API keys, `TRADE_MODE=DRY_RUN|LIVE`, risk limits
- [ ] Remove or archive unused calculator/weather demo servers when cutover is ready

### Phase 2: Data + fundamentals

- [ ] Market data client (OHLCV for oscillation)
- [ ] FMP (or equivalent) fundamentals client
- [ ] Fundamentals scorecard module (sections A–F above)
- [ ] Unit tests on scorecard edge cases (missing data, negative equity, etc.)

### Phase 3: Oscillation engine

- [ ] AI universe config
- [ ] Oscillation detector
- [ ] Bottom-of-curve scorer
- [ ] Candidate model + persistence

### Phase 4: Market research agent

- [ ] News/sentiment ingestion
- [ ] Earnings calendar check
- [ ] LLM brief generator (bull/bear/bias)
- [ ] Research gate that can block approval queue

### Phase 5: Robinhood MCP broker adapter

- [ ] MCP client wrapper (quotes, portfolio, positions, orders)
- [ ] `review` → `place` → status pipeline with `ref_id`
- [ ] Mock adapter for `DRY_RUN`
- [ ] Approval queue API (list / approve / reject / confirm)

### Phase 6: Dashboard

- [ ] Oscillators board
- [ ] Candidate detail (fundamentals + research)
- [ ] Approve / reject / size controls
- [ ] Portfolio & order history views (via MCP)

### Phase 7: Hardening

- [ ] Idempotent orders, retry policy, audit log
- [ ] Rate limits & market-hours checks
- [ ] Paper dry-run soak test before any LIVE mode
- [ ] README: setup Robinhood MCP + data keys + runbook

---

## 6. HFT Market-Making Lessons → Best-in-Class Async System

This section translates real HFT MM architecture into what we can (and cannot) build on Robinhood MCP + Polymarket CLOB. The goal is **best-in-class design for our latency/venue regime**, not fake nanosecond HFT.

### Honest latency regimes

| Regime | Typical latency | Our venues |
|--------|-----------------|------------|
| Colocated HFT | ns–µs, binary MD, FPGA/kernel bypass | **Out of scope** |
| Pro algo / low-latency retail API | ms–tens of ms | Polymarket CLOB WS + signed orders |
| Agentic / MCP brokerage | hundreds of ms–seconds | Robinhood Trading MCP |
| Research / offline ML | minutes–hours | Fair-value + order-policy training |

**Design rule:** compete on **fair value quality, inventory control, adverse-selection avoidance, and async reliability** — not on matching-engine race.

### Map of the five HFT components

| HFT component | Role of AI/ML (realistically) | Our implementation |
|---------------|-------------------------------|--------------------|
| **Market data** | Little online ML; purity + sync matter | Separate ingest processes: equities MD (quotes/bars), Polymarket WS books + Gamma discovery, related instruments for FV |
| **Fair value** | Offline ML sets params; rare online inference | Guarded IP module: equities micro-FV + Polymarket P(event) models; related-instrument baskets |
| **Order placement** | Offline policy search; online rules | Two-sided quotes on Poly; permissioned one-shot buys on RH; queue/rate/cancel logic |
| **Exchange connectivity** | None | Venue adapters: `RobinhoodMCPGateway`, `PolymarketClobGateway` (V2 SDK) |
| **Offline training** | **Primary ML spend** | Feature store → model discovery → param optimization → promote to live config |

### Process topology (async, HFT-inspired)

```
[ MD Ingest ] ──ticks/books──► [ Fair Value ] ──theo/edge──► [ Order Policy ]
     │                              │                              │
     │                              ▼                              ▼
     │                        [ Risk / Inventory ] ◄────── [ Gateway(s) ]
     │                              │                              │
     └──────── audit/features ──────┴────► [ Offline Trainer ]     │
                                                                   ▼
                                                         [ Fill / PnL bus ]
                                                                   │
                                                         [ Approval UI ] (equities default)
```

Hard separation (from HFT practice):

1. **MD ingest never shares a thread with decisioning** — asyncio tasks or separate processes; drop/backpressure instead of blocking the trading loop.
2. **Gateway is a thin protocol adapter** — no strategy logic inside signing/send.
3. **Fair value is pure function of state + params** — params only change via offline promote, not ad-hoc in the hot path.
4. **Order policy owns quoting/cancels/sizing** — consumes theo, inventory, fees, rate limits.
5. **Offline training is the real edge** — walk-forward backtests, adverse-selection labels, quote-quality metrics.

### Where AI/ML actually belongs

| Layer | Use ML? | How |
|-------|---------|-----|
| Tick→book normalize | No | Deterministic parsers, checksums, resync |
| Fair value | **Yes (mostly offline)** | Calibrate mean-reversion / relative-value / P(event); optional light online inference later |
| Order placement | **Yes (offline policy)** | Learn spread offset, size, cancel thresholds; live = parameterized rules |
| Research briefs (equities) | Yes (LLM) | Human-readable thesis; **not** in the Poly MM hot path |
| Connectivity | No | SDK + retries + idempotent `ref_id` / order ids |

Do **not** put a large LLM in the quote loop. Use LLMs for research, market selection, and post-trade explanation — same lesson as HFTs: predictive power only enters the loop when it beats latency cost.

### Async trade conductor (permission modes)

| Mode | Equities (Robinhood) | Polymarket |
|------|----------------------|------------|
| `MANUAL` | Signal → research → approve → review → place | Signal/quote plan → approve → place/cancel |
| `SEMI_AUTO` | Auto-cancel / alerts; buys still approved | Auto two-sided quotes within inventory caps; widen/pull on risk |
| `ASYNC_ARMED` | Pre-approved playbook (size, symbols, max loss/day); bot executes when edge≥threshold | Continuous MM / sniper within playbook; kill switch mandatory |

“Asynchronously conduct trade” = event-driven workers (MD, FV, policy, gateway, fills) + a **playbook** you arm, not a chatty agent blocking on every tick.

---

## 7. Polymarket Implications (first-class venue)

Polymarket is closer to classic MM than Robinhood equities: **true CLOB**, two-sided books, WS deltas, maker/taker dynamics, explicit resolution risk.

### Venue stack (2026 V2)

| API | URL | Role |
|-----|-----|------|
| Gamma | `https://gamma-api.polymarket.com` | Market discovery, metadata, volume, expiry, tags |
| CLOB V2 | `https://clob.polymarket.com` | Books, place/cancel (use `py-clob-client-v2`) |
| Data | `https://data-api.polymarket.com` | Positions, history, leaderboard |
| Market WS | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | Book snapshots/deltas, last trade |
| User WS | `.../ws/user` | Own fills/cancels (auth) |
| RTDS (optional) | `wss://ws-live-data.polymarket.com` | Related crypto prices for FV baskets |

### Fair value on prediction markets (core IP)

For a binary YES/NO token, theo ≈ **model probability of resolution**, adjusted for fees, time-to-expiry, and inventory.

```
theo_yes = P_model(event)
edge = theo_yes - mid_yes   # after fee/half-spread costs
quote_bid = theo_yes - skew(inventory) - reserve
quote_ask = theo_yes + skew(inventory) + reserve
```

**Related-instrument basket** (HFT lesson): FV is rarely one book.

| Market type | Related inputs |
|-------------|----------------|
| Crypto price thresholds | Binance/RTDS spot, vol surface proxy, time decay |
| Election / politics | Poll aggregates, prediction-market cross-venue (Kalshi if available), news shocks |
| Sports | Live score WS, win-prob models |
| Macro / Fed | Futures rates, calendars, speech sentiment (offline-heavy) |
| Corp / AI event markets | Equity tape + news (ties to Robinhood research stack) |

Offline ML trains `P_model` and skew/reserve schedules; online loop applies frozen params to live books.

### Order placement on Polymarket (MM + selective take)

- Maintain **balanced two-sided** post-only quotes when edge is thin but inventory OK
- **Take** (cross) only when `|edge|` exceeds take threshold after fees
- Cancel/widen on: stale book, WS gap > N seconds, inventory breach, resolution proximity, news shock
- Respect rate limits (~order/min caps); batch cancel+replace carefully
- Size by depth, remaining open interest, and max loss at resolution (binary payoff is brutal)

### Adverse selection & resolution risk (Poly-specific)

- Binary payoff → inventory at expiry is **full notional risk**, not soft delta
- Prefer markets with clear resolution rules + liquidity rewards
- Pull quotes into known information windows (speech, print, tip-off)
- Label historical fills as toxic vs benign for offline cancel-policy training

### Cross-venue system (equities + Poly)

```
Shared: feature store, risk ledger, approval/playbook UI, offline trainer, audit log
Equities path: oscillation/FV → research/fundamentals → Robinhood MCP gateway
Poly path:     book MD → P(event) FV → quote policy → CLOB V2 gateway
```

Shared risk: **USD (or USDC) capital allocation** across Agentic RH cash and Polymarket collateral; one kill switch freezes both gateways.

### Best-in-class model roadmap (offline → promote)

1. **Data**: tick/book/trade store for Poly; OHLCV + fundamentals for equities; resolution outcomes labels
2. **Features**: microprice, imbalance, related-basket residuals, time-to-expiry, inventory, fee-adjusted mid
3. **Models**: calibrated classifiers/regressors for `P_model`; mean-reversion params for equities; **not** end-to-end LLM traders
4. **Policy search**: simulate quote offsets, sizes, cancel rules vs historical books (fill models + toxicity)
5. **Promote**: versioned param sets → live config; shadow mode before capital
6. **Monitor**: realized edge, toxicity rate, inventory path, missed edge, gateway errors

---

## Implementation Checklist (additions)

### Phase 8: Async runtime core

- [ ] Event bus + separate MD / FV / policy / gateway workers
- [ ] Playbook + kill switch + capital allocator
- [ ] Feature logging for offline training

### Phase 9: Polymarket venue

- [ ] Gamma discovery client + condition_id ↔ token_id map
- [ ] Local book from REST snapshot + WS deltas (resync on gap)
- [ ] `py-clob-client-v2` gateway (place/cancel, user WS fills)
- [ ] Binary FV module + inventory skew
- [ ] Dry-run paper book before live keys

### Phase 10: Offline training pipeline

- [ ] Historical store + labels (fills, resolutions, adverse selection)
- [ ] Walk-forward training jobs for FV + order policy params
- [ ] Param registry + shadow → live promotion

---

## Proposed File Structure (updated)

```
ai-hedgefund/
├── plan.md
├── README.md
├── requirements.txt
├── env.example
├── docker-compose.yml
├── src/
│   ├── api/
│   ├── runtime/                 # async bus, workers, playbooks
│   ├── strategy/
│   │   ├── equities/            # oscillation, bottoms
│   │   └── polymarket/          # P(event) FV, quote policy
│   ├── research/                # fundamentals + news (equities-heavy)
│   ├── marketdata/
│   │   ├── equities_md.py
│   │   └── polymarket_md.py     # WS book + resync
│   ├── brokers/
│   │   ├── robinhood_mcp.py
│   │   ├── mock_robinhood.py
│   │   └── polymarket_clob.py   # CLOB V2 gateway
│   ├── training/                # offline jobs, param registry
│   ├── risk/
│   ├── models/
│   └── config/
├── web/
└── tests/
```

---

## Dependencies (target, extended)

- Prior stack + `py-clob-client-v2`, `websockets`, `numpy`, `scipy` / `scikit-learn` (offline)
- Optional: `polars` for training frames; GPU only for offline discovery later

## Environment Variables (target, extended)

```
TRADE_MODE=DRY_RUN
VENUES=robinhood,polymarket
REQUIRE_USER_APPROVAL=true
PLAYBOOK_ARMED=false
FMP_API_KEY=
ALPHA_VANTAGE_API_KEY=
TAVILY_API_KEY=
ROBINHOOD_MCP_URL=https://agent.robinhood.com/mcp/trading
POLYMARKET_HOST=https://clob.polymarket.com
POLYMARKET_PRIVATE_KEY=
POLYMARKET_FUNDER=
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_API_PASSPHRASE=
POLYMARKET_CHAIN_ID=137
MAX_POSITION_PCT=5
MAX_PORTFOLIO_RISK_PCT=25
MAX_POLY_INVENTORY_USD=500
KILL_SWITCH=false
```

---

## Progress Log

- 2026-07-23: Pivoted from legacy Claude/Tavily notebook demo to AI hedge-fund oscillation bot plan.
- 2026-07-23: Added official Robinhood Trading MCP execution path, market research integration, and full fundamentals review checklist.
- 2026-07-23: Absorbed HFT MM component model (MD, FV, order placement, connectivity, offline training); defined async runtime + Polymarket CLOB V2 venue implications and model roadmap.
