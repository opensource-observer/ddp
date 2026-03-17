import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Retention

    The **retention metric** measures what percentage of developers who joined an ecosystem in a given
    cohort remain active over time. It answers: "Of developers who first contributed in Month X, how many
    are still active N months later?"

    The Retention Analysis insight uses this metric to compare cohort retention across ecosystems and time periods.

    **Preview** (computed via CTE from raw activity data):
    ```sql
    -- Retention is derived, not stored. See Sample Queries below.
    SELECT cohort_month, months_since_cohort, retention_rate
    FROM <cohort_retention_cte>
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Definition & Formula""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Retention Calculation

    For each (developer, ecosystem) pair:

    1. **Month 0** = The month of first observed contribution to the ecosystem
    2. **Month N** = N months after Month 0
    3. **Active in Month N** = Developer had at least one qualifying activity in that month

    **Retention Rate Formula:**

    ```
    Retention(cohort, month_N) = Active_in_month_N(cohort) / Cohort_size × 100%
    ```

    **Where:**
    - `cohort` = All developers whose Month 0 was a specific month (e.g., "January 2023 cohort")
    - `Active_in_month_N(cohort)` = Count of cohort developers with activity in Month N
    - `Cohort_size` = Total developers in the cohort

    ### Example

    If 100 developers first contributed to Ethereum in January 2023:
    - Month 0 (Jan 2023): 100 active (100% by definition)
    - Month 1 (Feb 2023): 75 active → 75% retention
    - Month 3 (Apr 2023): 50 active → 50% retention
    - Month 6 (Jul 2023): 35 active → 35% retention
    - Month 12 (Jan 2024): 25 active → 25% retention

    This creates a **retention curve** showing drop-off over time.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 1: Build Cohort Retention Table""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _ecosystem = 'Ethereum'
    sql_cohort_retention = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{_ecosystem}'
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
        WHERE e.name = '{_ecosystem}'
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
        df_retention = mo.sql(sql_cohort_retention, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Cohort retention table for {_ecosystem}**

        Shows retention rates for each monthly cohort over time.
        - **cohort_month**: When developers first contributed (Month 0)
        - **months_since_cohort**: Months elapsed since Month 0
        - **retention_rate**: Percentage of cohort still active
        """),
        mo.ui.table(df_retention, selection=None, pagination=True)
    ])
    return (df_retention,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 2: Retention Curves Visualization""")
    return


@app.cell(hide_code=True)
def _(df_retention, mo, px):
    _ecosystem = 'Ethereum'
    # Filter to a few cohorts for cleaner visualization
    selected_cohorts = ['2023-01-01', '2023-04-01', '2023-07-01', '2023-10-01', '2024-01-01']
    df_curves = df_retention[df_retention['cohort_month'].astype(str).str[:10].isin(selected_cohorts)]
    df_curves = df_curves.copy()
    df_curves['cohort_label'] = df_curves['cohort_month'].astype(str).str[:7]

    _fig = px.line(
        df_curves,
        x='months_since_cohort',
        y='retention_rate',
        color='cohort_label',
        title=f'Developer Retention Curves: {_ecosystem}',
        labels={
            'months_since_cohort': 'Months Since First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'cohort_label': 'Cohort'
        },
        markers=True
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(dtick=1)
    )
    _fig.update_yaxes(range=[0, 105])

    mo.vstack([
        mo.md(f"""
        **Retention curves by cohort for {_ecosystem}**

        Each line represents a different cohort (grouped by first contribution month).
        - Month 0 is always 100% by definition
        - Steeper drop-off indicates lower retention
        - Compare cohorts to see if retention is improving over time
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_curves, selected_cohorts


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 3: Cross-Ecosystem Retention Comparison""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, px):
    sql_cross_ecosystem = """
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
        df_cross = mo.sql(sql_cross_ecosystem, engine=pyoso_db_conn, output=False)

    _fig = px.line(
        df_cross,
        x='months_since_cohort',
        y='retention_rate',
        color='ecosystem',
        title='Retention Comparison: Ethereum vs Solana (Jan 2023 Cohort)',
        labels={
            'months_since_cohort': 'Months Since First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'ecosystem': 'Ecosystem'
        },
        markers=True,
        color_discrete_map={'Ethereum': '#627EEA', 'Solana': '#9945FF'}
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(dtick=2)
    )
    _fig.update_yaxes(range=[0, 105])

    mo.vstack([
        mo.md("""
        **Cross-ecosystem retention comparison**

        Comparing the January 2023 cohort across Ethereum and Solana shows how different
        ecosystems retain developers over time.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (df_cross,)


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "Methodology": mo.md("""
        **Cohort Definition**: Month 0 = the first month a developer is observed contributing to an ecosystem's repos.

        **Retention Rate**: `Retention(cohort, N) = Active_in_month_N / Cohort_size × 100%`

        A developer is "active" if they have ≥1 commit in the 28-day window around month N. Cohort size is fixed at Month 0 count — it never shrinks.

        **Calculation Steps**:
        1. Identify each developer's first activity month per ecosystem (cohort assignment)
        2. Track monthly activity in subsequent months
        3. Divide active count by cohort size for each month offset
        """),
        "Assumptions & Limitations": mo.md("""
        - Cohort assignment is per-ecosystem — a developer joining Ethereum in Jan and Solana in Mar has two separate cohorts
        - Commits only — excludes PRs, issues, code reviews
        - Newer cohorts have shorter observation windows (survivorship bias for recent cohorts)
        - Identity resolution may cause developers to appear in wrong cohorts
        - 28-day activity windows can miss developers who contribute sporadically
        """),
        "Data Sources": mo.md("""
        - `oso.stg_opendevdata__repo_developer_28d_activities` — 28-day rolling activity per developer per repo
        - `oso.stg_opendevdata__ecosystems_repos_recursive` — Recursive repo-to-ecosystem mapping
        - `oso.stg_opendevdata__ecosystems` — Ecosystem definitions
        - Full catalog: [docs.oso.xyz](https://docs.oso.xyz)
        """),
    })
    return


@app.cell(hide_code=True)
def _():
    import plotly.express as px
    return (px,)


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
