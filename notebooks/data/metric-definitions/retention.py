import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Retention

    Cohort retention measures what percentage of developers who first contributed in a given period remain active over time.

    **Preview:**
    ```sql
    -- Retention is computed via CTE from raw activity data (not pre-calculated)
    -- See Sample Queries below for the full cohort retention query
    SELECT
      rda.canonical_developer_id,
      MIN(rda.day) AS first_active
    FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
    GROUP BY 1
    LIMIT 5
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Standard Definition

    ODD does not pre-calculate retention. The raw data needed is in `stg_opendevdata__repo_developer_28d_activities` — per-developer, per-repo, per-day activity records. Retention must be derived via a multi-step CTE:

    1. **Cohort assignment**: `MIN(day)` per developer per ecosystem = Month/Year 0
    2. **Monthly activity tracking**: `DISTINCT (developer, month)` of subsequent activity
    3. **Retention rate**: `active_in_period_N / cohort_size * 100%`

    Cohort size is fixed at period 0 — it never shrinks.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## DDP Variants

    | Variant | Insight | Definition | How It Differs |
    |:--------|:--------|:-----------|:---------------|
    | Yearly cohort retention | Retention Analysis | Groups developers by year of first contribution; tracks retention at years 1, 2, 3+ | Yearly granularity, 2020-2025 cohorts, per-ecosystem |
    | Cross-ecosystem comparison | Retention Analysis | Same formula applied to Ethereum, Solana, Bitcoin 2023 cohort | Compares ecosystem stickiness |
    | Quarterly project-level retention | DeFi Builder Journeys | Cohort = quarter of first home project activity; tracks % still active on that project each subsequent quarter | Per-project (not ecosystem), quarterly (not yearly), project-specific activity (not any ecosystem activity) |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Build Cohort Retention Table (DDP Variant)

    Full 4-CTE query that computes monthly retention for Ethereum cohorts from 2023-2024. Each row shows what percentage of a cohort remained active N months after their first contribution.

    ```sql
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
        GROUP BY 1
    ),
    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
    ),
    cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month >= DATE('2023-01-01')
            AND cohort_month <= DATE('2024-06-01')
        GROUP BY 1
    ),
    cohort_activity AS (
        SELECT
            fa.cohort_month,
            ma.activity_month,
            DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
            COUNT(DISTINCT fa.canonical_developer_id) AS active_count
        FROM first_activity fa
        JOIN monthly_activity ma
            ON fa.canonical_developer_id = ma.canonical_developer_id
            AND ma.activity_month >= fa.cohort_month
        WHERE fa.cohort_month >= DATE('2023-01-01')
            AND fa.cohort_month <= DATE('2024-06-01')
        GROUP BY 1, 2
    )
    SELECT
        ca.cohort_month,
        ca.months_since_cohort,
        ca.active_count,
        cs.cohort_size,
        ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
    FROM cohort_activity ca
    JOIN cohort_sizes cs
        ON ca.cohort_month = cs.cohort_month
    WHERE ca.months_since_cohort <= 12
    ORDER BY ca.cohort_month, ca.months_since_cohort
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _sql_cohort_retention = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
        GROUP BY 1
    ),
    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
    ),
    cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month >= DATE('2023-01-01')
            AND cohort_month <= DATE('2024-06-01')
        GROUP BY 1
    ),
    cohort_activity AS (
        SELECT
            fa.cohort_month,
            ma.activity_month,
            DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
            COUNT(DISTINCT fa.canonical_developer_id) AS active_count
        FROM first_activity fa
        JOIN monthly_activity ma
            ON fa.canonical_developer_id = ma.canonical_developer_id
            AND ma.activity_month >= fa.cohort_month
        WHERE fa.cohort_month >= DATE('2023-01-01')
            AND fa.cohort_month <= DATE('2024-06-01')
        GROUP BY 1, 2
    )
    SELECT
        ca.cohort_month,
        ca.months_since_cohort,
        ca.active_count,
        cs.cohort_size,
        ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
    FROM cohort_activity ca
    JOIN cohort_sizes cs
        ON ca.cohort_month = cs.cohort_month
    WHERE ca.months_since_cohort <= 12
    ORDER BY ca.cohort_month, ca.months_since_cohort
    """

    with mo.persistent_cache("cohort_retention"):
        _df = mo.sql(_sql_cohort_retention, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Cross-Ecosystem Retention Comparison

    Compares the January 2023 cohort across Ethereum and Solana to see how different ecosystems retain developers over time.

    ```sql
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
        GROUP BY 1, 2
    ),
    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
    ),
    cohort_sizes AS (
        SELECT
            ecosystem,
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month = DATE('2023-01-01')
        GROUP BY 1, 2
    ),
    cohort_activity AS (
        SELECT
            fa.ecosystem,
            fa.cohort_month,
            DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
            COUNT(DISTINCT fa.canonical_developer_id) AS active_count
        FROM first_activity fa
        JOIN monthly_activity ma
            ON fa.canonical_developer_id = ma.canonical_developer_id
            AND fa.ecosystem = ma.ecosystem
            AND ma.activity_month >= fa.cohort_month
        WHERE fa.cohort_month = DATE('2023-01-01')
        GROUP BY 1, 2, ma.activity_month
    )
    SELECT
        ca.ecosystem,
        ca.months_since_cohort,
        ca.active_count,
        cs.cohort_size,
        ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
    FROM cohort_activity ca
    JOIN cohort_sizes cs
        ON ca.ecosystem = cs.ecosystem
        AND ca.cohort_month = cs.cohort_month
    WHERE ca.months_since_cohort <= 18
    ORDER BY ca.ecosystem, ca.months_since_cohort
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _sql_cross_ecosystem = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
        GROUP BY 1, 2
    ),
    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
    ),
    cohort_sizes AS (
        SELECT
            ecosystem,
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month = DATE('2023-01-01')
        GROUP BY 1, 2
    ),
    cohort_activity AS (
        SELECT
            fa.ecosystem,
            fa.cohort_month,
            DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
            COUNT(DISTINCT fa.canonical_developer_id) AS active_count
        FROM first_activity fa
        JOIN monthly_activity ma
            ON fa.canonical_developer_id = ma.canonical_developer_id
            AND fa.ecosystem = ma.ecosystem
            AND ma.activity_month >= fa.cohort_month
        WHERE fa.cohort_month = DATE('2023-01-01')
        GROUP BY 1, 2, ma.activity_month
    )
    SELECT
        ca.ecosystem,
        ca.months_since_cohort,
        ca.active_count,
        cs.cohort_size,
        ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
    FROM cohort_activity ca
    JOIN cohort_sizes cs
        ON ca.ecosystem = cs.ecosystem
        AND ca.cohort_month = cs.cohort_month
    WHERE ca.months_since_cohort <= 18
    ORDER BY ca.ecosystem, ca.months_since_cohort
    """

    with mo.persistent_cache("cross_ecosystem"):
        _df = mo.sql(_sql_cross_ecosystem, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
