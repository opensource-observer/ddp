import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Alignment

    **Ecosystem alignment** measures how concentrated a developer's commit activity is within a single ecosystem versus spread across many. A developer who commits exclusively to Ethereum repos has 100% Ethereum alignment; one splitting time between Ethereum and Solana has proportional alignment to each.

    This metric underpins several DDP analyses: the **DeFi Builder Journeys** insight extends it into a richer multi-channel model tracking activity across home projects, other crypto, personal repos, and OSS contributions. The **Speedrun Ethereum** insight uses a related concept — repo ecosystem classification — to categorize where SRE alumni contribute.

    **Preview:**
    ```sql
    SELECT
      rda.canonical_developer_id,
      e.name AS ecosystem_name,
      rda.num_commits
    FROM oso.stg_opendevdata__repo_developer_28d_activities rda
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
      ON rda.repo_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems e
      ON err.ecosystem_id = e.id
    WHERE rda.day >= CURRENT_DATE - INTERVAL '28' DAY
    LIMIT 10
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
    ### Base Calculation

    For a developer `d` in a 28-day window `t`, alignment to ecosystem `e` is:

    ```
    Alignment(d, e, t) = Commits_to_e(d, t) / Total_commits(d, t) × 100%
    ```

    Repositories are mapped to ecosystems via Electric Capital's recursive classification (`stg_opendevdata__ecosystems_repos_recursive`). A repo can belong to multiple ecosystems (eg, a repo in both "Ethereum" and "DeFi"), so a single commit may contribute to multiple ecosystem alignments.

    ### Alignment Buckets

    | Bucket | Range | Interpretation |
    |:-------|:------|:---------------|
    | Exclusive | 100% | All commits to one ecosystem |
    | Highly aligned | 75–99% | Strong primary ecosystem |
    | Majority aligned | 50–74% | Primary ecosystem with significant cross-pollination |
    | Split | 25–49% | Multi-ecosystem developer |
    | Peripheral | 1–24% | Minor contributor to this ecosystem |

    ### Extended Models

    The DDP insights build on this base metric in two ways:

    **Multi-channel alignment** (DeFi Builder Journeys): Instead of ecosystem-level commit distribution, tracks activity across 5 strategic channels — home project, other crypto, personal repos, OSS, and interest (watch/fork) activity. Each channel measures `repo_event_days` rather than raw commits. This captures a richer picture of how builders split their attention.

    **Repo classification** (Speedrun Ethereum): Categorizes each repository into one of 6 labels (Ethereum, Other EVM, Non-EVM Chain, Other Crypto, Personal, Unknown) using a hierarchical CASE statement over ecosystem flags. This is used to understand where SRE alumni contribute, not to compute per-developer percentages.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 1: Calculate Alignment for Top Developers""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    sql_top_developer_alignment = """
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.num_commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = (SELECT MAX(day) FROM oso.stg_opendevdata__repo_developer_28d_activities)
            AND e.name IN ('Ethereum', 'Solana', 'Optimism', 'Arbitrum', 'Base', 'AI')
        GROUP BY 1, 2, 3
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            day,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_name,
            dea.ecosystem_commits,
            dt.total_commits,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity dea
        JOIN developer_totals dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
            AND dea.day = dt.day
        WHERE dt.total_commits >= 10
    )

    SELECT
        canonical_developer_id,
        ecosystem_name,
        ecosystem_commits,
        total_commits,
        alignment_pct
    FROM alignment
    ORDER BY total_commits DESC, alignment_pct DESC
    LIMIT 100
    """

    with mo.persistent_cache("top_developer_alignment"):
        df_alignment = mo.sql(sql_top_developer_alignment, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Query**: Calculate ecosystem alignment for active developers (≥10 commits) on most recent day

        **Results**: {len(df_alignment):,} developer-ecosystem pairs
        """),
        mo.ui.table(df_alignment, selection=None, pagination=True)
    ])
    return (df_alignment,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 2: Top Developers by Ecosystem Alignment""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _ecosystem = 'Ethereum'
    sql_top_aligned = f"""
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.num_commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = (SELECT MAX(day) FROM oso.stg_opendevdata__repo_developer_28d_activities)
        GROUP BY 1, 2, 3
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            day,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_name,
            dea.ecosystem_commits,
            dt.total_commits,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity dea
        JOIN developer_totals dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
            AND dea.day = dt.day
        WHERE dt.total_commits >= 5
    )

    SELECT
        canonical_developer_id,
        ecosystem_commits,
        total_commits,
        alignment_pct
    FROM alignment
    WHERE ecosystem_name = '{_ecosystem}'
    ORDER BY alignment_pct DESC, total_commits DESC
    LIMIT 50
    """

    with mo.persistent_cache("top_aligned"):
        df_top_aligned = mo.sql(sql_top_aligned, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Top developers most aligned with {_ecosystem}**

        Showing developers with ≥5 commits, ranked by alignment percentage.
        """),
        mo.ui.table(df_top_aligned, selection=None, pagination=True)
    ])
    return (df_top_aligned,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 3: Alignment Distribution for an Ecosystem""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, px):
    _ecosystem = 'Ethereum'
    sql_alignment_distribution = f"""
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.num_commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = (SELECT MAX(day) FROM oso.stg_opendevdata__repo_developer_28d_activities)
        GROUP BY 1, 2, 3
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            day,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_name,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity dea
        JOIN developer_totals dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
            AND dea.day = dt.day
        WHERE dt.total_commits >= 5
            AND dea.ecosystem_name = '{_ecosystem}'
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
    """

    with mo.persistent_cache("alignment_distribution"):
        df_distribution = mo.sql(sql_alignment_distribution, engine=pyoso_db_conn, output=False)

    _fig = px.bar(
        df_distribution,
        x='alignment_bucket',
        y='developer_count',
        title=f'Developer Alignment Distribution: {_ecosystem}',
        labels={'alignment_bucket': 'Alignment Level', 'developer_count': 'Number of Developers'}
    )
    _fig.update_layout(
        template='plotly_white',
        showlegend=False
    )

    mo.vstack([
        mo.md(f"""
        **Alignment distribution for {_ecosystem}**

        Shows how many developers fall into each alignment bucket.
        - **100% (exclusive)**: Developers who only contribute to {_ecosystem}
        - **75-99%**: Primarily {_ecosystem} with some cross-ecosystem work
        - Lower percentages indicate more distributed activity
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.ui.table(df_distribution, selection=None)
    ])
    return (df_distribution,)



@app.cell(hide_code=True)
def _():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True):
        """Apply Electric Capital chart styling to a plotly figure."""
        title_text = ""
        if title:
            title_text = f"<b>{title}</b>"
            if subtitle:
                title_text += f"<br><span style='font-size:14px;color:#666666'>{subtitle}</span>"
        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=20, color="#1B4F72", family="Arial, sans-serif"),
                x=0, xanchor="left", y=0.95, yanchor="top"
            ) if title else None,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12, color="#333"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100 if title else 40, l=70, r=40, b=60),
            hovermode='x unified',
            showlegend=show_legend,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, bgcolor="rgba(255,255,255,0.8)"
            )
        )
        fig.update_xaxes(
            showgrid=False, showline=True,
            linecolor="#CCCCCC", linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=""
        )
        fig.update_yaxes(
            showgrid=True, gridcolor="#E8E8E8", gridwidth=1,
            showline=True, linecolor="#CCCCCC", linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=y_title or "",
            title_font=dict(size=12, color="#666"),
            tickformat=",d"
        )
        return fig
    return (apply_ec_style,)


@app.cell(hide_code=True)
def _():
    EC_COLORS = {
        'light_blue': '#7EB8DA',
        'light_blue_fill': 'rgba(126, 184, 218, 0.4)',
        'dark_blue': '#1B4F72',
        'medium_blue': '#5499C7',
        'orange': '#F5B041',
    }
    return (EC_COLORS,)


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    return pd, go


@app.cell(hide_code=True)
def _():
    import pandas as _pd
    import plotly.express as px
    return (_pd, px)


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
