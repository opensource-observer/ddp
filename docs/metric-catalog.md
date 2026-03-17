# DDP Metric Catalog

Bottom-up inventory of every metric used across the 6 DDP insight notebooks, grouped by metric definition category.

---

## Activity (MAD)

Source: `oso.stg_opendevdata__eco_mads` — pre-calculated daily snapshots with rolling 28-day windows.

| Metric | Column | Definition | Used In |
|--------|--------|-----------|---------|
| Monthly Active Developers | `all_devs` | Unique developers with >=1 commit in rolling 28d | developer-report-2025 |
| Full-Time Developers | `full_time_devs` | >=10 active days per 28d window | developer-report-2025, developer-lifecycle |
| Part-Time Developers | `part_time_devs` | <10 active days, regular pattern | developer-report-2025, developer-lifecycle |
| One-Time Developers | `one_time_devs` | Sporadic activity over 84d window | developer-report-2025 |
| Newcomers | `devs_0_1y` | <1 year contributing to crypto | developer-report-2025 |
| Emerging | `devs_1_2y` | 1-2 years contributing | developer-report-2025 |
| Established | `devs_2y_plus` | 2+ years contributing | developer-report-2025 |
| Exclusive | `exclusive_devs` | Active in only one ecosystem (28d) | developer-report-2025 |
| Multichain | `multichain_devs` | Active across multiple ecosystems (28d) | developer-report-2025 |
| Commits | `num_commits` | Total commits in 28d window | developer-report-2025 |

**Status:** Definition matches usage exactly. Primary consumer is 2025 Developer Trends.

---

## Lifecycle

Source: `oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated` — monthly state snapshots.

| Metric | Label(s) | Definition | Used In |
|--------|----------|-----------|---------|
| First Time | `first time` | First-ever contribution to ecosystem | developer-lifecycle |
| Full Time (4 variants) | `full time`, `new full time`, `part time to full time`, `dormant to full time` | >=10 active days, various transitions | developer-lifecycle |
| Part Time (4 variants) | `part time`, `new part time`, `full time to part time`, `dormant to part time` | 1-9 active days, various transitions | developer-lifecycle |
| Churned/Dormant (7 variants) | `dormant`, `first time to dormant`, `part time to dormant`, `full time to dormant`, `churned (after first time)`, `churned (after reaching part time)`, `churned (after reaching full time)` | No activity (1-6mo dormant, >6mo churned) | developer-lifecycle |
| Monthly Churn Rate | Derived | `(churned+dormant) / active * 100` per month | developer-lifecycle |

**Status:** Definition matches usage exactly. 16 granular states roll up to 4 categories.

---

## Retention

Source: `oso.stg_opendevdata__repo_developer_28d_activities` joined to ecosystem mappings — computed via CTE.

| Metric | Computation | Used In |
|--------|------------|---------|
| Cohort assignment | Year of first contribution to ecosystem | developer-retention |
| Cohort size | Count of developers per cohort year per ecosystem | developer-retention |
| Retention rate | `active_in_year_N / cohort_size * 100` | developer-retention |
| 1-Year / 2-Year avg retention | Mean retention across cohorts | developer-retention (stat cards) |
| Cross-ecosystem retention | Same formula, compared across ETH/SOL/BTC | developer-retention |
| Quarterly cohort retention | Quarterly variant applied to project-level activity | defi-builder-journeys |

**Status:** Definition matches developer-retention exactly. DeFi Builder Journeys uses a quarterly project-level variant.

---

## Alignment

Two distinct implementations across insights:

### 5-Channel Activity Model (DeFi Builder Journeys)

Source: `ethereum.devpanels.mart_developer_alignment_monthly` (customer-scoped).

| Channel | Column | Definition |
|---------|--------|-----------|
| Home Project | `home_project_repo_event_days` | Activity days on the builder's primary DeFi project |
| Crypto | `crypto_repo_event_days` | Activity days on other crypto repos |
| Personal | `personal_repo_event_days` | Activity days on personal/non-crypto repos |
| OSS | `oss_repo_event_days` | Activity days on open-source repos |
| Interest | `interest_repo_event_days` | Watch/fork events on repos of interest |

Used for: onboarding features, contribution features, current status classification, alluvial flows, balance of trade, feeder project analysis.

### Repo Ecosystem Classification (Speedrun Ethereum)

Source: `stg_opendevdata__ecosystems_repos_recursive` + `stg_opendevdata__ecosystems`.

| Category | Rule |
|----------|------|
| Ethereum | `ecosystem_name IN ('Ethereum', 'Celo')` |
| Other EVM Chain | `ecosystem_name = 'Ethereum Virtual Machine Stack'` |
| Non-EVM Chain | `is_chain = 1` (not EVM) |
| Other (Crypto-Related) | `is_crypto = 1` (not chain) |
| Personal | `user_name = repo_owner` |
| Unknown | No ecosystem mapping |

Used for: classifying where SRE alumni contribute post-program.

### Base Ecosystem Alignment (Public Tables)

Source: `oso.stg_opendevdata__repo_developer_28d_activities` joined to ecosystem mappings.

Formula: `Commits_to_ecosystem / Total_commits * 100%`

Currently queryable but not directly used by any insight notebook. Serves as the building block for the customer-scoped models above.

**Status:** Definition needs rewrite. Current definition describes the base formula; actual insights use richer models built on top.

---

## Uncategorized

### Engagement / Repo Popularity (Ethereum Repo Rank)

Source: `ethereum.dev_engagement_models.*` (customer-scoped) + GitHub API scrapes.

| Metric | Definition | Time Window |
|--------|-----------|-------------|
| `global_engagers_30d` / `7d` | Unique stargazers + forkers | 30d / 7d rolling |
| `eth_devs_30d` / `7d` | Engagers who are Ethereum panel builders | 30d / 7d rolling |
| `eth_dev_pct` | `eth_devs / global_engagers * 100` (signal strength) | 30d |
| `momentum` | `(global_engagers_7d / 7) / (global_engagers_30d / 30)` | 7d vs 30d |
| Community label | "Crypto" if eth_dev_pct >= 1%, else "Mainstream" | 30d |
| Overlap % | `shared_engagers / min(repo_a_size, repo_b_size) * 100` | All-time |
| `alignment_score` | Sum of eth_dev_pct weights across repos a builder engages with | 30d |
| Cumulative engagers | Running count of unique stargazers/forkers per repo | All-time |

Note: These are based on stars/forks (GitHub API), not commits (Open Dev Data). Entirely different primitive from the Activity metrics.

### TVL / Protocol Metrics (DeFi Builder Journeys)

Source: `ethereum.devpanels.mart_defi_project_summary`, `mart_project_tvl_history` (customer-scoped).

| Metric | Definition |
|--------|-----------|
| `current_tvl` | Total Value Locked (DefiLlama) |
| `ethereum_pct` | % of TVL on Ethereum L1 + L2s |
| `tvl_rank` | Rank by TVL |
| `total_repos` | Repos associated with project |
| `qualifying_developers` | Builders with 12+ months on home project |

### Developer Journey Metrics (DeFi Builder Journeys)

| Metric | Definition |
|--------|-----------|
| Onboarding month | First month with home project activity |
| Offboarding month | Last activity month if 6+ months inactive after |
| Tenure months | `offboard - onboard` (or to latest if still active) |
| Is still active | No offboard date |
| Pipeline category | Newcomer (<6mo pre-activity), Crypto-experienced, Non-crypto experienced |
| Contribution cluster | Frequent (>10d/mo), Regular (5-10d/mo), Occasional (<5d/mo) |
| Consistency % | `contrib_months / tenure_months * 100` |
| Feeder projects | Crypto/OSS projects a builder was active in pre-onboarding |
| Balance of trade | Annual imports/exports between ecosystem categories |

### SRE Program Metrics (Speedrun Ethereum)

| Metric | Definition |
|--------|-----------|
| `challenges_completed` | SRE challenges finished |
| `batch_id` | SRE program batch |
| `cohort_year` | Year of SRE enrollment |
| Experience category | Experienced (>12mo), Learning (3-12mo), Newb (<3mo) pre-SRE |
| `velocity` | `SUM(1 + ln(event_count))` per month per user |
| Incremental Ethereum MAD | Active Ethereum devs attributable to SRE vs baseline |

---

## Observations

1. **Activity, Lifecycle, Retention** — clean 1:1 mapping between definitions and insights.
2. **Alignment** — the definition doesn't match the implementations. Needs rewrite to describe the 5-channel model and repo classification.
3. **Repo Rank** runs on an entirely different primitive (engagement events, not commits). No existing metric definition covers it.
4. **DeFi Builder Journeys** is the most metric-rich notebook (~95 measures). Many are project-level lifecycle concepts (onboarding, tenure, pipeline) that don't have definitions.
5. **Speedrun Ethereum** has program-specific metrics that are unique to SRE.

## Potential New Definitions

- **Engagement** — stars, forks, signal strength, momentum (covers Repo Rank)
- **Developer Journey** — onboarding, offboarding, tenure, pipeline categories (covers DeFi Builder Journeys project-level metrics)
- **Experience** — pre-existing activity classification, velocity, SRE attribution (covers Speedrun Ethereum)
