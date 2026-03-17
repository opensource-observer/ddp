import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Activity

    Monthly Active Developers (MAD) counts unique developers contributing code within a rolling 28-day window — the standard metric from Electric Capital's Open Dev Data.

    **Preview:**
    ```sql
    SELECT
      e.name AS ecosystem,
      m.day,
      m.all_devs,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
    ORDER BY m.day DESC
    LIMIT 5
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Standard Definition

    ODD classifies active developers by intensity over rolling windows:

    | Metric | Column | Threshold | Window |
    |:-------|:-------|:----------|:-------|
    | Monthly Active Developers | `all_devs` | >=1 commit | Rolling 28 days |
    | Full-time | `full_time_devs` | >=10 active days | 84-day rolling |
    | Part-time | `part_time_devs` | <10 active days, regular contributions | 84-day rolling |
    | One-time | `one_time_devs` | Minimal or sporadic activity | 84-day rolling |
    | Exclusive | `exclusive_devs` | Active in only this ecosystem | Rolling 28 days |
    | Multichain | `multichain_devs` | Active across multiple ecosystems | Rolling 28 days |

    These are pre-calculated daily in `stg_opendevdata__eco_mads`. Developers are original code authors — merge/PR integrators are not counted unless they authored commits. Identity resolution deduplicates developers across multiple accounts and emails.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## DDP Variants

    | Variant | Insight | Definition | How It Differs |
    |:--------|:--------|:-----------|:---------------|
    | Standard MAD | 2025 Developer Trends | Uses `eco_mads` directly — MAD, full-time/part-time/one-time stacked area charts, ecosystem comparisons | Direct use of ODD metrics, no modifications |
    | Engagement-based activity | Ethereum Repo Rank | Counts unique stargazers + forkers (not committers) per repo over 30d/7d windows | Different primitive: stars/forks from GitHub API, not commits from ODD. Measures attention, not contribution |
    | Momentum | Ethereum Repo Rank | `(engagers_7d / 7) / (engagers_30d / 30)` — ratio of recent vs trailing engagement rate | Derived acceleration metric. >1.0 = trending up, <1.0 = cooling |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. MAD with Activity Level Breakdown (ODD Standard)

    Query the pre-calculated MAD metric for Ethereum over the last 90 days, showing the full activity level breakdown.

    ```sql
    SELECT
      m.day,
      m.all_devs,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
      AND m.day >= CURRENT_DATE - INTERVAL '90' DAY
    ORDER BY m.day DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        """
        SELECT
          m.day,
          m.all_devs,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
          AND m.day >= CURRENT_DATE - INTERVAL '90' DAY
        ORDER BY m.day DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Top Ecosystems by Current Developer Count

    Rank ecosystems by their most recent MAD count.

    ```sql
    SELECT
      e.name AS ecosystem,
      m.all_devs AS monthly_active_devs,
      m.full_time_devs,
      m.exclusive_devs,
      m.multichain_devs
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE m.day = (
      SELECT MAX(day)
      FROM oso.stg_opendevdata__eco_mads
    )
      AND e.is_crypto = 1
      AND e.is_category = 0
    ORDER BY m.all_devs DESC
    LIMIT 15
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        """
        SELECT
          e.name AS ecosystem,
          m.all_devs AS monthly_active_devs,
          m.full_time_devs,
          m.exclusive_devs,
          m.multichain_devs
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day = (
          SELECT MAX(day)
          FROM oso.stg_opendevdata__eco_mads
        )
          AND e.is_crypto = 1
          AND e.is_category = 0
        ORDER BY m.all_devs DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
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
