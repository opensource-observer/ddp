# OSO Agent Guide

You are a data analyst with access to the OSO (Open Source Observer) data warehouse.

## Connection

Install pyoso and set your API key:

```bash
uv add pyoso  # or: pip install pyoso
export OSO_API_KEY=<your_key>
```

Query the warehouse:

```python
from pyoso import Client
client = Client()  # reads OSO_API_KEY from environment
df = client.to_pandas("SELECT * FROM oso.projects_v1 LIMIT 10")
```

Sign up at [oso.xyz/start](https://www.oso.xyz/start) for a free API key.

## SQL Dialect

Use **Trino SQL**:
- `CAST(x AS VARCHAR)` not `SAFE_CAST`
- `DATE_TRUNC('month', dt)` not `DATE_TRUNC(dt, MONTH)`
- `COALESCE` not `IFNULL`
- `CURRENT_DATE - INTERVAL '30' DAY` for date math

## Key Tables

### Ecosystem & Repository Data (Open Dev Data)
- `oso.stg_opendevdata__ecosystems` -- Ecosystem definitions (name, is_crypto, is_chain)
- `oso.stg_opendevdata__ecosystems_repos_recursive` -- Repos in each ecosystem (with distance)
- `oso.int_opendevdata__repositories_with_repo_id` -- Repository bridge (maps GraphQL IDs to REST IDs)

### Developer & Activity Data
- `oso.int_ddp__developers` -- Unified developer identities (Open Dev Data + GitHub Archive)
- `oso.int_gharchive__developer_activities` -- Daily developer activity rollup (for MAD metrics)
- `oso.int_gharchive__github_events` -- Standardized GitHub events (pushes, PRs, issues, stars, forks)

### Pre-Calculated Metrics
- `oso.stg_opendevdata__eco_mads` -- Monthly active developers per ecosystem
- `oso.stg_opendevdata__repo_developer_28d_activities` -- 28-day rolling activity per repo per developer

### Projects
- `oso.projects_v1` -- Curated project registry with metadata

## Starter Queries

**Largest ecosystems by repo count:**
```sql
SELECT e.name, COUNT(DISTINCT er.repo_id) AS repo_count
FROM oso.stg_opendevdata__ecosystems e
JOIN oso.stg_opendevdata__ecosystems_repos_recursive er ON e.id = er.ecosystem_id
GROUP BY e.name ORDER BY repo_count DESC LIMIT 15
```

**Monthly active developers for an ecosystem:**
```sql
SELECT m.day, m.all_devs AS monthly_active_developers, m.full_time_devs
FROM oso.stg_opendevdata__eco_mads m
JOIN oso.stg_opendevdata__ecosystems e ON m.ecosystem_id = e.id
WHERE e.name = 'Ethereum' AND m.day >= DATE('2024-01-01')
ORDER BY m.day
```

**Cross-source join -- active developers per ecosystem (last 30 days):**
```sql
SELECT e.name, COUNT(DISTINCT da.actor_id) AS active_devs
FROM oso.int_gharchive__developer_activities da
JOIN oso.int_opendevdata__repositories_with_repo_id r ON da.repo_id = r.repo_id
JOIN oso.stg_opendevdata__ecosystems_repos_recursive err ON r.opendevdata_id = err.repo_id
JOIN oso.stg_opendevdata__ecosystems e ON err.ecosystem_id = e.id
WHERE da.bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY e.name ORDER BY active_devs DESC LIMIT 10
```

## Important Notes
- **Only `oso.*` tables are publicly accessible.** Tables with other namespaces (e.g., `ethereum.*`) require customer-scoped API keys and will return an error with a standard key.
- GitHub Archive data can be ~3 days behind real-time
- Only public GitHub events (no private repos)
- When listing/ranking ecosystems, add `WHERE e.is_crypto = 1 AND e.is_category = 0` to filter out internal ODD categories
- Use narrow date ranges (7-30 days) for fast queries
- Full data catalog: https://docs.oso.xyz
