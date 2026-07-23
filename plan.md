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

## Proposed File Structure

```
ai-hedgefund/
├── plan.md
├── README.md
├── requirements.txt
├── env.example
├── docker-compose.yml          # optional local services
├── src/
│   ├── api/                    # FastAPI routes
│   ├── strategy/               # oscillation, bottoms, risk
│   ├── research/               # fundamentals + news + LLM brief
│   ├── brokers/
│   │   ├── robinhood_mcp.py    # live MCP adapter
│   │   └── mock_robinhood.py   # dry-run
│   ├── data/                   # OHLCV + FMP/AV clients
│   ├── models/                 # pydantic schemas
│   └── config/
├── web/                        # dashboard (Next or simple React)
└── tests/
```

---

## Dependencies (target)

- fastapi, uvicorn, pydantic, python-dotenv, httpx
- pandas, numpy
- mcp (client) for Robinhood Trading MCP / mock
- financial data: `fmp` HTTP or official SDK; optional `yfinance` for dry-run
- LLM provider already available in env (Bedrock / OpenAI / Anthropic) for research briefs

## Environment Variables (target)

```
TRADE_MODE=DRY_RUN
FMP_API_KEY=
ALPHA_VANTAGE_API_KEY=
TAVILY_API_KEY=                 # optional research enrichment
ROBINHOOD_MCP_URL=https://agent.robinhood.com/mcp/trading
MAX_POSITION_PCT=5
MAX_PORTFOLIO_RISK_PCT=25
REQUIRE_USER_APPROVAL=true
```

---

## Progress Log

- 2026-07-23: Pivoted from legacy Claude/Tavily notebook demo to AI hedge-fund oscillation bot plan.
- 2026-07-23: Added official Robinhood Trading MCP execution path, market research integration, and full fundamentals review checklist.
