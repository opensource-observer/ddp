import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Lifecycle

    The **lifecycle metric** classifies developers into stages based on their activity patterns, enabling analysis of developer journeys, churn prediction, and ecosystem health monitoring.

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
      m.devs_2y_plus AS established
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

    The lifecycle model assigns each developer a state each month based on their activity level and prior state. The 16 granular states roll up into 4 summary categories:

    | Category | Label | Description |
    |:---------|:------|:------------|
    | **First Time** | `first time` | First-ever contribution to the ecosystem |
    | **Full Time** | `full time` | 10+ active days, continuing from prior month |
    | | `new full time` | First month reaching 10+ active days |
    | | `part time to full time` | Transitioned from part-time level |
    | | `dormant to full time` | Returned from dormancy at full-time level |
    | **Part Time** | `part time` | 1-9 active days, continuing from prior month |
    | | `new part time` | First month at part-time level |
    | | `full time to part time` | Stepped down from full-time level |
    | | `dormant to part time` | Returned from dormancy at part-time level |
    | **Churned / Dormant** | `dormant` | No activity this month (previously active) |
    | | `first time to dormant` | Dormant after first contribution |
    | | `part time to dormant` | Dormant after part-time activity |
    | | `full time to dormant` | Dormant after full-time activity |
    | | `churned (after first time)` | Extended inactivity after first contribution |
    | | `churned (after reaching part time)` | Extended inactivity after reaching part time |
    | | `churned (after reaching full time)` | Extended inactivity after reaching full time |

    **Active** = First Time + Full Time + Part Time (all 9 labels above the Churned/Dormant group)

    Activity levels (full-time, part-time) are assessed over a 28-day rolling window per Electric Capital's methodology. Dormancy transitions to churn after approximately 6 months of continuous inactivity.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## State Transitions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph LR
        NEW["🆕 New<br/><small>First contribution</small>"] --> FT["💼 Full-Time<br/><small>≥10 days / 28d</small>"]
        NEW --> PT["🔧 Part-Time<br/><small>1-9 days / 28d</small>"]
        FT <-->|"activity changes"| PT
        FT -->|"stops contributing"| DORMANT["💤 Dormant<br/><small>1-6 months inactive</small>"]
        PT -->|"stops contributing"| DORMANT
        DORMANT -->|"resumes activity"| FT
        DORMANT -->|"resumes activity"| PT
        DORMANT -->|">6 months"| CHURNED["🚪 Churned<br/><small>>6 months inactive</small>"]
        CHURNED -.->|"rare return"| FT
        CHURNED -.->|"rare return"| PT
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Transition Rules

    | From | To | Trigger |
    |:-----|:---|:--------|
    | New | Full-Time / Part-Time | Continues contributing after first period |
    | New | Dormant | No activity after initial contribution |
    | Full-Time | Part-Time | Activity drops below 10 days / 28d |
    | Part-Time | Full-Time | Activity rises to ≥10 days / 28d |
    | Full-Time / Part-Time | Dormant | 0 active days |
    | Dormant | Full-Time / Part-Time | Any activity resumes |
    | Dormant | Churned | >6 months of continuous inactivity |
    | Churned | Full-Time / Part-Time | Activity resumes (rare) |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Current Lifecycle Stage Distribution

    Get the latest stage breakdown for an ecosystem from the pre-calculated model.

    ```sql
    SELECT
      m.day,
      m.all_devs AS total_active,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs,
      ROUND(100.0 * m.full_time_devs / m.all_devs, 1) AS full_time_pct,
      ROUND(100.0 * m.part_time_devs / m.all_devs, 1) AS part_time_pct,
      ROUND(100.0 * m.one_time_devs / m.all_devs, 1) AS one_time_pct
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
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          m.day,
          m.all_devs AS total_active,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs,
          ROUND(100.0 * m.full_time_devs / m.all_devs, 1) AS full_time_pct,
          ROUND(100.0 * m.part_time_devs / m.all_devs, 1) AS part_time_pct,
          ROUND(100.0 * m.one_time_devs / m.all_devs, 1) AS one_time_pct
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
        ORDER BY m.day DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Developer-Level Stage Transitions

    Compute actual per-developer transitions between activity levels using raw activity data.
    This query uses a tight 2-month window for performance.

    ```sql
    WITH monthly_activity AS (
        SELECT
          rda.canonical_developer_id,
          DATE_TRUNC('month', rda.day) AS month,
          COUNT(DISTINCT rda.day) AS active_days
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
          ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
          AND rda.day BETWEEN DATE '2025-01-01' AND DATE '2025-02-28'
        GROUP BY 1, 2
    ),
    with_stages AS (
        SELECT
          canonical_developer_id,
          month,
          CASE WHEN active_days >= 10 THEN 'Full-Time'
               ELSE 'Part-Time'
          END AS stage,
          LAG(CASE WHEN active_days >= 10 THEN 'Full-Time'
                   ELSE 'Part-Time'
              END) OVER (
            PARTITION BY canonical_developer_id ORDER BY month
          ) AS prev_stage
        FROM monthly_activity
    )
    SELECT
      prev_stage AS from_stage,
      stage AS to_stage,
      COUNT(*) AS transition_count
    FROM with_stages
    WHERE prev_stage IS NOT NULL
      AND prev_stage != stage
    GROUP BY 1, 2
    ORDER BY transition_count DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        WITH monthly_activity AS (
            SELECT
              rda.canonical_developer_id,
              DATE_TRUNC('month', rda.day) AS month,
              COUNT(DISTINCT rda.day) AS active_days
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
              ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
              ON err.ecosystem_id = e.id
            WHERE e.name = 'Ethereum'
              AND rda.day BETWEEN DATE '2025-01-01' AND DATE '2025-02-28'
            GROUP BY 1, 2
        ),
        with_stages AS (
            SELECT
              canonical_developer_id,
              month,
              CASE WHEN active_days >= 10 THEN 'Full-Time'
                   ELSE 'Part-Time'
              END AS stage,
              LAG(CASE WHEN active_days >= 10 THEN 'Full-Time'
                       ELSE 'Part-Time'
                  END) OVER (
                PARTITION BY canonical_developer_id ORDER BY month
              ) AS prev_stage
            FROM monthly_activity
        )
        SELECT
          prev_stage AS from_stage,
          stage AS to_stage,
          COUNT(*) AS transition_count
        FROM with_stages
        WHERE prev_stage IS NOT NULL
          AND prev_stage != stage
        GROUP BY 1, 2
        ORDER BY transition_count DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "Methodology": mo.md("""
        **Lifecycle States**: Developers are classified into 4 high-level categories based on 28-day rolling activity windows:
        - **Full-Time**: ≥10 active days per 28-day window
        - **Part-Time**: 1-9 active days per 28-day window
        - **One-Time/Dormant**: Sporadic activity over 84-day window or 1-6 months inactive
        - **Churned**: >6 months with no activity

        **Thresholds**: Aligned with Electric Capital's methodology. Full-time threshold (10 days/28 days) represents ~36% of working days.

        **State Transitions**: Developers move between states monthly. A churned developer who returns is reclassified based on current activity level, not history.
        """),
        "Assumptions & Limitations": mo.md("""
        - Commits only — excludes PRs, issues, code reviews
        - Multi-ecosystem developers have independent lifecycle states per ecosystem
        - Seasonal patterns (holidays, conference seasons) can cause temporary state changes
        - Dormant and churned states are not pre-calculated in `eco_mads` — require custom CTE on raw activity data
        - Identity resolution may affect transition accuracy
        """),
        "Data Sources": mo.md("""
        - `oso.stg_opendevdata__eco_mads` — Pre-calculated daily MAD snapshots with activity level breakdowns
        - `oso.stg_opendevdata__repo_developer_28d_activities` — Raw 28-day rolling activity for custom state calculations
        - `oso.stg_opendevdata__ecosystems_repos_recursive` — Ecosystem-to-repo mapping
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
