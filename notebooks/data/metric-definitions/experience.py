import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Experience

    Developer experience measures how long a developer has been contributing to open source crypto, used to distinguish newcomers from veterans.

    Preview:
    ```sql
    SELECT
      e.name AS ecosystem,
      m.day,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established
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

    Open Dev Data classifies developers into three tenure tiers based on how long they have been contributing to crypto overall (not just one ecosystem):

    | Tier | Column | Threshold | Interpretation |
    |:-----|:-------|:----------|:---------------|
    | **Newcomer** | `devs_0_1y` | <1 year of crypto contributions | Recently arrived in the ecosystem |
    | **Emerging** | `devs_1_2y` | 1-2 years of contributions | Past the initial exploration phase |
    | **Established** | `devs_2y_plus` | 2+ years of contributions | Long-term participants in crypto development |

    These tiers are pre-calculated daily in `stg_opendevdata__eco_mads` alongside the activity metrics (MAD, full-time, etc.). Tenure is measured from a developer's first commit to any crypto repo, not their first commit to a specific ecosystem.

    A developer can be a "Newcomer" to crypto while being an experienced software engineer — tenure only tracks crypto-specific contribution history.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## DDP Variants

    The DDP insights adapt the standard tenure concept for different analytical contexts:

    | Variant | Insight | Definition | How It Differs |
    |:--------|:--------|:-----------|:---------------|
    | **Pre-program experience** | Speedrun Ethereum | Experienced (>12mo), Learning (3-12mo), Newb (<3mo) of GitHub activity before SRE enrollment | Uses months of any GitHub activity, not crypto-specific tenure. Threshold at 3 and 12 months rather than 1 and 2 years |
    | **Pipeline categories** | DeFi Builder Journeys | Newcomer (<6mo pre-onboarding), Crypto-experienced, Non-crypto experienced | Based on pre-onboarding activity channels: crypto vs personal/OSS. Distinguishes *where* experience was gained, not just *how long* |
    | **Contribution cluster** | DeFi Builder Journeys | Frequent (>10d/mo), Regular (5-10d/mo), Occasional (<5d/mo) | Measures intensity of engagement during tenure, not tenure length itself |

    The standard ODD tiers answer "how long has this developer been in crypto?" The DDP variants ask more specific questions: "what kind of experience did they bring?" (Speedrun) and "where did that experience come from?" (DeFi Builder Journeys).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Current Tenure Breakdown by Ecosystem (ODD Standard)

    The pre-calculated tenure tiers from `eco_mads`, showing how each ecosystem's developer base breaks down by experience level.

    ```sql
    SELECT
      e.name AS ecosystem,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established,
      m.all_devs AS total_active,
      ROUND(100.0 * m.devs_0_1y / m.all_devs, 1) AS newcomer_pct,
      ROUND(100.0 * m.devs_2y_plus / m.all_devs, 1) AS established_pct
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE m.day = (SELECT MAX(day) FROM oso.stg_opendevdata__eco_mads)
      AND e.is_crypto = 1
      AND e.is_category = 0
    ORDER BY m.all_devs DESC
    LIMIT 15
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    mo.sql(
        """
        SELECT
          e.name AS ecosystem,
          m.devs_0_1y AS newcomers,
          m.devs_1_2y AS emerging,
          m.devs_2y_plus AS established,
          m.all_devs AS total_active,
          ROUND(100.0 * m.devs_0_1y / m.all_devs, 1) AS newcomer_pct,
          ROUND(100.0 * m.devs_2y_plus / m.all_devs, 1) AS established_pct
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day = (SELECT MAX(day) FROM oso.stg_opendevdata__eco_mads)
          AND e.is_crypto = 1
          AND e.is_category = 0
        ORDER BY m.all_devs DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Tenure Composition Over Time (ODD Standard)

    Track how the newcomer/emerging/established mix changes for an ecosystem. A declining newcomer share may indicate an aging developer base.

    ```sql
    SELECT
      m.day,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established,
      ROUND(100.0 * m.devs_0_1y / m.all_devs, 1) AS newcomer_pct
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
      AND m.day >= CURRENT_DATE - INTERVAL '365' DAY
    ORDER BY m.day
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    mo.sql(
        """
        SELECT
          m.day,
          m.devs_0_1y AS newcomers,
          m.devs_1_2y AS emerging,
          m.devs_2y_plus AS established,
          ROUND(100.0 * m.devs_0_1y / m.all_devs, 1) AS newcomer_pct
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
          AND m.day >= CURRENT_DATE - INTERVAL '365' DAY
        ORDER BY m.day
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Developer Tenure from Raw Activity Data (DDP Variant)

    Compute per-developer tenure directly from raw activity data. This is the approach used by the DeFi Builder Journeys and Speedrun Ethereum insights to classify developers by pre-existing experience.

    ```sql
    WITH developer_tenure AS (
      SELECT
        rda.canonical_developer_id,
        MIN(rda.day) AS first_active,
        MAX(rda.day) AS last_active,
        DATE_DIFF('month', MIN(rda.day), MAX(rda.day)) AS months_active
      FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
      GROUP BY 1
    )
    SELECT
      CASE
        WHEN months_active >= 24 THEN 'Established (2+ years)'
        WHEN months_active >= 12 THEN 'Emerging (1-2 years)'
        WHEN months_active >= 3 THEN 'Learning (3-12 months)'
        ELSE 'Newcomer (<3 months)'
      END AS experience_tier,
      COUNT(*) AS developer_count
    FROM developer_tenure
    WHERE last_active >= CURRENT_DATE - INTERVAL '90' DAY
    GROUP BY 1
    ORDER BY developer_count DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    mo.sql(
        """
        WITH developer_tenure AS (
          SELECT
            rda.canonical_developer_id,
            MIN(rda.day) AS first_active,
            MAX(rda.day) AS last_active,
            DATE_DIFF('month', MIN(rda.day), MAX(rda.day)) AS months_active
          FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
          GROUP BY 1
        )
        SELECT
          CASE
            WHEN months_active >= 24 THEN 'Established (2+ years)'
            WHEN months_active >= 12 THEN 'Emerging (1-2 years)'
            WHEN months_active >= 3 THEN 'Learning (3-12 months)'
            ELSE 'Newcomer (<3 months)'
          END AS experience_tier,
          COUNT(*) AS developer_count
        FROM developer_tenure
        WHERE last_active >= CURRENT_DATE - INTERVAL '90' DAY
        GROUP BY 1
        ORDER BY developer_count DESC
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
