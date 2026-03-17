import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Activity

    The **Monthly Active Developer (MAD)** metric measures unique developers contributing code within a rolling 28-day window — the standard metric from the [Electric Capital Developer Report](https://www.developerreport.com). The 2025 Developer Trends insight uses this metric to track ecosystem growth, activity level composition, and tenure shifts over time.

    **Preview:**
    ```sql
    SELECT
      e.name AS ecosystem,
      m.day,
      m.all_devs,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established,
      m.num_commits
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
    ORDER BY m.day DESC
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Definition & Formula

    | Metric | Definition | Window |
    |:-------|:-----------|:-------|
    | **Monthly Active Developers** | Unique developers with ≥1 commit | Rolling 28 days |
    | **Full-time** | ≥10 active days in window | 84-day rolling |
    | **Part-time** | <10 active days, regular contributions | 84-day rolling |
    | **One-time** | Minimal or sporadic activity | 84-day rolling |
    | **Newcomers** | <1 year contributing to crypto | Lifetime |
    | **Emerging** | 1-2 years contributing to crypto | Lifetime |
    | **Established** | 2+ years contributing to crypto | Lifetime |
    | **Exclusive** | Active only in this ecosystem | Rolling 28 days |
    | **Multichain** | Active across multiple ecosystems | Rolling 28 days |

    > Developers are original code authors — merge/PR integrators are not counted unless they authored commits. Identity resolution deduplicates developers across multiple accounts and emails.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Monthly Active Developers for an Ecosystem

    Query the pre-calculated MAD metric with full breakdowns for any ecosystem.

    ```sql
    SELECT
      m.day,
      m.all_devs,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established,
      m.num_commits
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
        f"""
        SELECT
          m.day,
          m.all_devs,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs,
          m.devs_0_1y AS newcomers,
          m.devs_1_2y AS emerging,
          m.devs_2y_plus AS established,
          m.num_commits
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
      m.multichain_devs,
      m.num_commits
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE m.day = (
      SELECT MAX(day)
      FROM oso.stg_opendevdata__eco_mads
    )
    ORDER BY m.all_devs DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          e.name AS ecosystem,
          m.all_devs AS monthly_active_devs,
          m.full_time_devs,
          m.exclusive_devs,
          m.multichain_devs,
          m.num_commits
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day = (
          SELECT MAX(day)
          FROM oso.stg_opendevdata__eco_mads
        )
        ORDER BY m.all_devs DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "Methodology": mo.md("""
        **Data Source**: Electric Capital's Open Dev Data via `stg_opendevdata__eco_mads` — pre-calculated daily snapshots per ecosystem with rolling 28-day windows.

        **Definitions**:
        - **MAD** (Monthly Active Developer): Unique developers with ≥1 commit in a rolling 28-day window
        - **Full-Time**: ≥10 active days per 28-day window
        - **Part-Time**: <10 active days, regular activity pattern
        - **One-Time**: Sporadic activity over 84-day rolling window
        - **Newcomer/Emerging/Established**: Based on lifetime tenure (<1yr / 1-2yr / 2+yr)
        - **Exclusive/Multichain**: Whether developer commits to repos in only one ecosystem or multiple
        """),
        "Assumptions & Limitations": mo.md("""
        - Tracks commits only (excludes PRs, issues, reviews)
        - Curated repository set — coverage depends on Electric Capital's ecosystem classification
        - Identity resolution uses heuristics — some developers may be over/under-counted
        - GitHub Archive PushEvent API truncates at 20 commits per push (inflates commit counts for large pushes)
        - Data lags a few days behind real-time
        """),
        "Data Sources": mo.md("""
        - **Open Dev Data** (Electric Capital): `oso.stg_opendevdata__eco_mads` — pre-calculated MAD snapshots
        - **GitHub Archive**: `oso.int_gharchive__developer_activities` — raw daily activity for validation
        - Full catalog: [docs.oso.xyz](https://docs.oso.xyz)
        """),
    })
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
