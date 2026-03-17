import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Alignment

    Ecosystem alignment measures how a developer distributes their commit activity across ecosystems, distinguishing exclusive contributors from multi-ecosystem developers.

    **Preview:**
    ```sql
    SELECT
      rda.canonical_developer_id,
      e.name AS ecosystem_name,
      SUM(rda.num_commits) AS commits
    FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
      ON rda.repo_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON err.ecosystem_id = e.id
    WHERE rda.day >= CURRENT_DATE - INTERVAL '28' DAY
    GROUP BY 1, 2
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Standard Definition

    ODD provides two alignment-related columns in `eco_mads`:

    | Metric | Column | Definition |
    |:-------|:-------|:-----------|
    | Exclusive | `exclusive_devs` | Developers active in only this ecosystem during the 28-day window |
    | Multichain | `multichain_devs` | Developers active across multiple ecosystems |

    For finer-grained analysis, alignment percentages can be computed from `stg_opendevdata__repo_developer_28d_activities` by joining to ecosystem mappings:

    ```
    Alignment(developer, ecosystem) = Commits_to_ecosystem / Total_commits x 100%
    ```

    Repos are mapped to ecosystems via `stg_opendevdata__ecosystems_repos_recursive`. A repo can belong to multiple ecosystems, so a single commit may count toward multiple alignments.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## DDP Variants

    | Variant | Insight | Definition | How It Differs |
    |:--------|:--------|:-----------|:---------------|
    | 5-channel activity model | DeFi Builder Journeys | Tracks `repo_event_days` across 5 channels: home project, other crypto, personal, OSS, interest (watch/fork) | Measures attention distribution by activity days, not commit counts. Includes non-crypto activity. Uses customer-scoped `mart_developer_alignment_monthly` |
    | Repo ecosystem classification | Speedrun Ethereum | Categorizes each repo as Ethereum, Other EVM, Non-EVM Chain, Other Crypto, Personal, or Unknown via hierarchical CASE statement | Categorical assignment per repo (not per developer). Used to classify where SRE alumni contribute |
    | Ecosystem category | DeFi Builder Journeys | Classifies projects as Ethereum (>80% ETH TVL), Solana (top chain = SOLANA), or Other | Project-level classification by TVL share, not developer commit distribution |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Alignment Distribution for Ethereum (ODD Standard)

    Computes commit distribution per developer for Ethereum, bucketed into alignment ranges, counting developers per bucket.

    ```sql
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            SUM(rda.num_commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = (
            SELECT MAX(day)
            FROM oso.stg_opendevdata__repo_developer_28d_activities
        )
        GROUP BY 1, 2
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity AS dea
        JOIN developer_totals AS dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
        WHERE dt.total_commits >= 5
            AND dea.ecosystem_name = 'Ethereum'
    )

    SELECT
        CASE
            WHEN alignment_pct = 100 THEN '100% (exclusive)'
            WHEN alignment_pct >= 75 THEN '75-99%'
            WHEN alignment_pct >= 50 THEN '50-74%'
            WHEN alignment_pct >= 25 THEN '25-49%'
            ELSE '1-24%'
        END AS alignment_bucket,
        COUNT(*) AS developer_count
    FROM alignment
    GROUP BY 1
    ORDER BY
        CASE alignment_bucket
            WHEN '100% (exclusive)' THEN 1
            WHEN '75-99%' THEN 2
            WHEN '50-74%' THEN 3
            WHEN '25-49%' THEN 4
            ELSE 5
        END
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        """
        WITH developer_ecosystem_activity AS (
            SELECT
                rda.canonical_developer_id,
                e.name AS ecosystem_name,
                SUM(rda.num_commits) AS ecosystem_commits
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE rda.day = (
                SELECT MAX(day)
                FROM oso.stg_opendevdata__repo_developer_28d_activities
            )
            GROUP BY 1, 2
        ),

        developer_totals AS (
            SELECT
                canonical_developer_id,
                SUM(ecosystem_commits) AS total_commits
            FROM developer_ecosystem_activity
            GROUP BY 1
        ),

        alignment AS (
            SELECT
                dea.canonical_developer_id,
                ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
            FROM developer_ecosystem_activity AS dea
            JOIN developer_totals AS dt
                ON dea.canonical_developer_id = dt.canonical_developer_id
            WHERE dt.total_commits >= 5
                AND dea.ecosystem_name = 'Ethereum'
        )

        SELECT
            CASE
                WHEN alignment_pct = 100 THEN '100% (exclusive)'
                WHEN alignment_pct >= 75 THEN '75-99%'
                WHEN alignment_pct >= 50 THEN '50-74%'
                WHEN alignment_pct >= 25 THEN '25-49%'
                ELSE '1-24%'
            END AS alignment_bucket,
            COUNT(*) AS developer_count
        FROM alignment
        GROUP BY 1
        ORDER BY
            CASE alignment_bucket
                WHEN '100% (exclusive)' THEN 1
                WHEN '75-99%' THEN 2
                WHEN '50-74%' THEN 3
                WHEN '25-49%' THEN 4
                ELSE 5
            END
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Top Developers by Ecosystem Alignment

    Top 20 developers most aligned with Ethereum (>=10 commits, highest alignment percentage).

    ```sql
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            SUM(rda.num_commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = (
            SELECT MAX(day)
            FROM oso.stg_opendevdata__repo_developer_28d_activities
        )
        GROUP BY 1, 2
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_commits AS commits,
            dt.total_commits,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity AS dea
        JOIN developer_totals AS dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
        WHERE dt.total_commits >= 10
            AND dea.ecosystem_name = 'Ethereum'
    )

    SELECT
        canonical_developer_id,
        commits,
        alignment_pct
    FROM alignment
    ORDER BY alignment_pct DESC, commits DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        """
        WITH developer_ecosystem_activity AS (
            SELECT
                rda.canonical_developer_id,
                e.name AS ecosystem_name,
                SUM(rda.num_commits) AS ecosystem_commits
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE rda.day = (
                SELECT MAX(day)
                FROM oso.stg_opendevdata__repo_developer_28d_activities
            )
            GROUP BY 1, 2
        ),

        developer_totals AS (
            SELECT
                canonical_developer_id,
                SUM(ecosystem_commits) AS total_commits
            FROM developer_ecosystem_activity
            GROUP BY 1
        ),

        alignment AS (
            SELECT
                dea.canonical_developer_id,
                dea.ecosystem_commits AS commits,
                dt.total_commits,
                ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
            FROM developer_ecosystem_activity AS dea
            JOIN developer_totals AS dt
                ON dea.canonical_developer_id = dt.canonical_developer_id
            WHERE dt.total_commits >= 10
                AND dea.ecosystem_name = 'Ethereum'
        )

        SELECT
            canonical_developer_id,
            commits,
            alignment_pct
        FROM alignment
        ORDER BY alignment_pct DESC, commits DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Exclusive vs Multichain by Ecosystem

    From `eco_mads` on the latest day, shows exclusive developers, multichain developers, and the exclusive percentage for top ecosystems.

    ```sql
    SELECT
      e.name AS ecosystem,
      m.exclusive_devs,
      m.multichain_devs,
      ROUND(
        100.0 * m.exclusive_devs / (m.exclusive_devs + m.multichain_devs), 1
      ) AS exclusive_pct
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE m.day = (
      SELECT MAX(day)
      FROM oso.stg_opendevdata__eco_mads
    )
      AND (m.exclusive_devs + m.multichain_devs) > 0
      AND e.is_crypto = 1
      AND e.is_category = 0
    ORDER BY m.exclusive_devs + m.multichain_devs DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        """
        SELECT
          e.name AS ecosystem,
          m.exclusive_devs,
          m.multichain_devs,
          ROUND(
            100.0 * m.exclusive_devs / (m.exclusive_devs + m.multichain_devs), 1
          ) AS exclusive_pct
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day = (
          SELECT MAX(day)
          FROM oso.stg_opendevdata__eco_mads
        )
          AND (m.exclusive_devs + m.multichain_devs) > 0
          AND e.is_crypto = 1
          AND e.is_category = 0
        ORDER BY m.exclusive_devs + m.multichain_devs DESC
        LIMIT 20
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
