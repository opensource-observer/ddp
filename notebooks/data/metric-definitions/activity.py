import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../../styles/data.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Activity

    The **Monthly Active Developer (MAD)** metric measures unique developers contributing code within a rolling 28-day window — the standard metric from the [Electric Capital Developer Report](https://www.developerreport.com).

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
def _(mo, pyoso_db_conn):
    _eco_df = mo.sql("""
        SELECT DISTINCT e.name
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day >= CURRENT_DATE - INTERVAL '90' DAY
        ORDER BY e.name
    """, engine=pyoso_db_conn, output=False)
    ecosystem_names = sorted(_eco_df['name'].tolist())
    return (ecosystem_names,)


@app.cell(hide_code=True)
def _(mo, ecosystem_names):
    ecosystem_dropdown = mo.ui.dropdown(
        options=ecosystem_names,
        value="Ethereum",
        label="Ecosystem"
    )
    time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )
    mo.hstack([ecosystem_dropdown, time_range], gap=2)
    return ecosystem_dropdown, time_range


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, pd, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    with mo.persistent_cache("activity_data"):
        df_activity = mo.sql(
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
              m.exclusive_devs,
              m.multichain_devs,
              m.num_commits
            FROM oso.stg_opendevdata__eco_mads AS m
            JOIN oso.stg_opendevdata__ecosystems AS e
              ON m.ecosystem_id = e.id
            WHERE e.name = '{_eco}'
              AND m.day >= DATE '2015-01-01'
            ORDER BY m.day
            """,
            engine=pyoso_db_conn,
            output=False
        )
        df_activity['day'] = pd.to_datetime(df_activity['day'])
    return (df_activity,)


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _repo_df = mo.sql(
        f"""
        SELECT COUNT(DISTINCT err.repo_id) AS repo_count
        FROM oso.stg_opendevdata__ecosystems_repos_recursive AS err
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON err.ecosystem_id = e.id
        WHERE e.name = '{_eco}'
        """,
        engine=pyoso_db_conn,
        output=False
    )
    repo_count = int(_repo_df['repo_count'].iloc[0])
    return (repo_count,)


@app.cell(hide_code=True)
def _(mo, df_activity, repo_count, pd, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _current = df_activity.iloc[-1]
    _current_date = _current['day']
    _mad = int(_current['all_devs'])
    _ft = int(_current['full_time_devs'])
    _commits = int(_current['num_commits'])

    _year_ago = _current_date - pd.DateOffset(years=1)
    _year_ago_df = df_activity[df_activity['day'] <= _year_ago]
    if len(_year_ago_df) > 0:
        _prev_mad = int(_year_ago_df.iloc[-1]['all_devs'])
        _yoy_pct = ((_mad - _prev_mad) / _prev_mad) * 100
        _yoy_caption = f"{_yoy_pct:+.1f}% YoY"
    else:
        _yoy_caption = "N/A"

    _peak_mad = int(df_activity['all_devs'].max())
    _peak_date = df_activity.loc[df_activity['all_devs'].idxmax(), 'day']

    mo.vstack([
        mo.md(f"## {_eco} Developer Activity"),
        mo.hstack([
            mo.stat(label="Monthly Active Devs", value=f"{_mad:,}", bordered=True, caption=_yoy_caption),
            mo.stat(label="Full-time Devs", value=f"{_ft:,}", bordered=True, caption="≥10 active days / 28d"),
            mo.stat(label="Total Repos", value=f"{repo_count:,}", bordered=True, caption="Recursive ecosystem mapping"),
            mo.stat(label="28d Commits", value=f"{_commits:,}", bordered=True, caption=f"Peak MAD: {_peak_mad:,} ({_peak_date.strftime('%b %Y')})"),
        ], widths="equal", gap=1),
    ])
    return


@app.cell(hide_code=True)
def _(mo, df_activity, go, apply_ec_style, time_range, pd, EC_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_activity.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]

    _fig = go.Figure()

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['all_devs'],
        name=f"Monthly Active ({int(_current['all_devs']):,})",
        mode='lines', fill='tozeroy',
        fillcolor=EC_COLORS['light_blue_fill'],
        line=dict(color=EC_COLORS['light_blue'], width=2),
        hovertemplate='<b>MAD</b>: %{y:,.0f}<extra></extra>'
    ))

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['full_time_devs'],
        name=f"Full-time ({int(_current['full_time_devs']):,})",
        mode='lines',
        line=dict(color=EC_COLORS['dark_blue'], width=2),
        hovertemplate='<b>Full-time</b>: %{y:,.0f}<extra></extra>'
    ))

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['newcomers'],
        name=f"New Devs ({int(_current['newcomers']):,})",
        mode='lines',
        line=dict(color=EC_COLORS['orange'], width=2, dash='dot'),
        hovertemplate='<b>New Devs</b>: %{y:,.0f}<extra></extra>'
    ))

    apply_ec_style(_fig,
        title=f"{int(_current['all_devs']):,} monthly active developers in {_eco}",
        subtitle="Total MAD, full-time developers, and new developers (<1yr) over time",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Activity Level Breakdown

    Developers segmented by sustained activity patterns over an 84-day rolling window.
    Full-time developers (≥10 active days per 28-day window) represent the most committed contributors.
    """)
    return


@app.cell(hide_code=True)
def _(mo, df_activity, go, apply_ec_style, time_range, pd, ACTIVITY_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_activity.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]

    _fig = go.Figure()

    for _label, _col in [("Full-time", "full_time_devs"), ("Part-time", "part_time_devs"), ("One-time", "one_time_devs")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'], y=_df[_col],
            name=f"{_label} ({int(_current[_col]):,})",
            mode='lines', stackgroup='one',
            fillcolor=ACTIVITY_COLORS[_label],
            line=dict(width=0.5, color=ACTIVITY_COLORS[_label]),
            hovertemplate=f'<b>{_label}</b>: %{{y:,.0f}}<extra></extra>'
        ))

    apply_ec_style(_fig,
        title=f"{_eco} Developers by Activity Level",
        subtitle="Stacked by full-time, part-time, and one-time contributors",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Active Developers by Tenure

    Developer tenure reflects how long they have been contributing to crypto overall (not just this ecosystem).
    Established developers (2+ years) represent the core of sustained open source engagement.
    """)
    return


@app.cell(hide_code=True)
def _(mo, df_activity, go, apply_ec_style, time_range, pd, TENURE_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_activity.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]

    _fig = go.Figure()

    for _label, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'], y=_df[_col],
            name=f"{_label} ({int(_current[_col]):,})",
            mode='lines', stackgroup='one',
            fillcolor=TENURE_COLORS[_label],
            line=dict(width=0.5, color=TENURE_COLORS[_label]),
            hovertemplate=f'<b>{_label}</b>: %{{y:,.0f}}<extra></extra>'
        ))

    apply_ec_style(_fig,
        title=f"{_eco} Developers by Tenure",
        subtitle="Stacked by newcomers (<1yr), emerging (1-2yr), and established (2+yr)",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
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


# --- Infrastructure cells ---


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
            title="", tickformat="%b %Y"
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

    TENURE_COLORS = {
        "Newcomers": "#B5D5E8",
        "Emerging": "#5DADE2",
        "Established": "#1B4F72",
    }

    ACTIVITY_COLORS = {
        "Full-time": "#5DADE2",
        "Part-time": "#EC7063",
        "One-time": "#F5B041",
    }
    return EC_COLORS, TENURE_COLORS, ACTIVITY_COLORS


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    return pd, go


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
