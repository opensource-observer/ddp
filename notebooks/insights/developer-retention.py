import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../styles/insights.css")


@app.cell(hide_code=True)
def header_title(mo):
    mo.Html('<div class="ddp-header"><h1>Retention Analysis</h1><p>Measuring cohort-based developer retention across crypto ecosystems.</p><div class="ddp-header-meta"><span>Created: <span class="ddp-badge">2026-03-16</span></span></div></div>')
    return




@app.cell(hide_code=True)
def header_accordion(mo):
    mo.accordion({
        "Metrics & Definitions": mo.md("""
**Definitions**

- **Cohort**: Developers grouped by the year of their first contribution to the ecosystem
- **Retention Rate**: Percentage of the original cohort that remains active in subsequent periods
- **Years Since Join**: Time elapsed since first contribution (Year 0 = joined year, always 100%)

**Methodology**

1. **Cohort Assignment**: Each developer is assigned to a cohort based on their first contribution date
2. **Activity Tracking**: We track whether the developer had any activity in subsequent years
3. **Retention Rate**: Percentage of the original cohort that remains active
        """),
        "Assumptions & Limitations": mo.md("""
- **Multi-ecosystem developers**: Developers active in multiple ecosystems are counted separately per ecosystem — a developer who churns from one ecosystem may still be active in another
- **Identity resolution**: Developer identities are resolved by Electric Capital's fingerprinting; the same person using different accounts may be counted multiple times
- **Newer cohorts**: More recent cohorts have shorter observation windows and therefore fewer data points for retention analysis
- **Public commits only**: Only public GitHub activity is tracked; private repos and non-GitHub platforms are excluded
- **Activity windows**: Activity is measured using 28-day rolling windows via Open Dev Data's `repo_developer_28d_activities` model
        """),
        "Data Sources": mo.md("""
- **Open Dev Data (Electric Capital)** — Developer activity data, [github.com/electric-capital/crypto-ecosystems](https://github.com/electric-capital/crypto-ecosystems)
- **Key Models** — `oso.stg_opendevdata__repo_developer_28d_activities`, `oso.stg_opendevdata__ecosystems_repos_recursive`
        """),
    })
    return


@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return


@app.cell(hide_code=True)
def query_all_retention_data(mo, pyoso_db_conn):
    _ECOSYSTEMS = ['Ethereum', 'Bitcoin', 'Solana', 'Arbitrum', 'Base', 'Polygon', 'AI']
    _eco_list = ', '.join(f"'{e}'" for e in _ECOSYSTEMS)

    with mo.persistent_cache("all_retention_data"):
        df_all_retention = mo.sql(f"""
        WITH first_activity AS (
            SELECT
                rda.canonical_developer_id,
                e.name AS ecosystem,
                YEAR(MIN(rda.day)) AS cohort_year,
                MIN(rda.day) AS first_active_date
            FROM stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE e.name IN ({_eco_list})
            GROUP BY 1, 2
        ),
        cohort_sizes AS (
            SELECT
                ecosystem,
                cohort_year,
                COUNT(*) AS cohort_size
            FROM first_activity
            WHERE cohort_year BETWEEN 2020 AND 2025
            GROUP BY 1, 2
        ),
        yearly_activity AS (
            SELECT DISTINCT
                fa.canonical_developer_id,
                fa.ecosystem,
                fa.cohort_year,
                YEAR(rda.day) AS activity_year
            FROM first_activity fa
            JOIN stg_opendevdata__repo_developer_28d_activities rda
                ON fa.canonical_developer_id = rda.canonical_developer_id
            JOIN stg_opendevdata__ecosystems_repos_recursive err
                ON rda.repo_id = err.repo_id
            JOIN stg_opendevdata__ecosystems e
                ON err.ecosystem_id = e.id
            WHERE e.name = fa.ecosystem
                AND fa.cohort_year BETWEEN 2020 AND 2025
        ),
        retention_data AS (
            SELECT
                ya.ecosystem,
                ya.cohort_year,
                ya.activity_year - ya.cohort_year AS years_since_join,
                COUNT(DISTINCT ya.canonical_developer_id) AS active_count
            FROM yearly_activity ya
            GROUP BY 1, 2, 3
        )
        SELECT
            rd.ecosystem,
            rd.cohort_year,
            rd.years_since_join,
            rd.active_count,
            cs.cohort_size,
            ROUND(100.0 * rd.active_count / cs.cohort_size, 1) AS retention_rate
        FROM retention_data rd
        JOIN cohort_sizes cs
            ON rd.ecosystem = cs.ecosystem
            AND rd.cohort_year = cs.cohort_year
        WHERE rd.years_since_join >= 0 AND rd.years_since_join <= 5
        ORDER BY rd.ecosystem, rd.cohort_year, rd.years_since_join
        """, engine=pyoso_db_conn, output=False)
        df_all_retention['retention_rate'] = df_all_retention['retention_rate'].astype(float)
        df_all_retention['years_since_join'] = df_all_retention['years_since_join'].astype(int)
    return (df_all_retention,)


@app.cell(hide_code=True)
def section_cohort_retention(mo):
    mo.md("""
    ## Cohort Retention
    *What percentage of developers who joined in Year X are still active after N years?*
    """)
    return


@app.cell(hide_code=True)
def retention_overview_tabs(df_all_retention, mo, go):
    import json as _json
    import html as _html_mod

    _ECOSYSTEMS = ['Ethereum', 'Bitcoin', 'Solana', 'Arbitrum', 'Base', 'Polygon', 'AI']

    _COHORT_COLORS = ['#1B4F72', '#7EB8DA', '#5DADE2', '#A9CCE3', '#2E86C1', '#85C1E9']

    def _stat(value, label, caption=''):
        return (
            f'<div class="ddp-stat-box">'
            f'<div class="ddp-stat-value">{value}</div>'
            f'<div class="ddp-stat-label">{label}</div>'
            + (f'<div class="ddp-stat-caption">{caption}</div>' if caption else '')
            + '</div>'
        )

    _states = {}
    for _eco in _ECOSYSTEMS:
        _df_eco = df_all_retention[df_all_retention['ecosystem'] == _eco].copy()
        if _df_eco.empty:
            continue

        _df_eco['cohort_label'] = _df_eco['cohort_year'].astype(str) + ' Cohort'

        _metrics_1yr = _df_eco[_df_eco['years_since_join'] == 1].copy()
        _metrics_2yr = _df_eco[_df_eco['years_since_join'] == 2].copy()

        if len(_metrics_1yr) > 0:
            _avg_1yr = _metrics_1yr['retention_rate'].mean()
            _best_1yr = _metrics_1yr.loc[_metrics_1yr['retention_rate'].idxmax()]
            _worst_1yr = _metrics_1yr.loc[_metrics_1yr['retention_rate'].idxmin()]
        else:
            _avg_1yr = 0
            _best_1yr = {'cohort_year': 'N/A', 'retention_rate': 0}
            _worst_1yr = {'cohort_year': 'N/A', 'retention_rate': 0}

        _avg_2yr = _metrics_2yr['retention_rate'].mean() if len(_metrics_2yr) > 0 else 0

        _stats_html = (
            '<div class="ddp-stat-row">'
            + _stat(f'{_avg_1yr:.1f}%', 'Avg 1-Year Retention', f'{_eco} across selected cohorts')
            + _stat(f'{_avg_2yr:.1f}%', 'Avg 2-Year Retention', f'{_eco} across selected cohorts')
            + _stat(str(_best_1yr['cohort_year']), 'Best Cohort', f"{_best_1yr['retention_rate']:.1f}% retention at 1 year")
            + _stat(str(_worst_1yr['cohort_year']), 'Lowest Cohort', f"{_worst_1yr['retention_rate']:.1f}% retention at 1 year")
            + '</div>'
        )

        _title_rate = f'{_avg_1yr:.1f}%' if _avg_1yr > 0 else 'N/A'

        _fig = go.Figure()
        for _i, _cohort in enumerate(sorted(_df_eco['cohort_label'].unique())):
            _cdf = _df_eco[_df_eco['cohort_label'] == _cohort]
            _fig.add_trace(go.Scatter(
                x=_cdf['years_since_join'].tolist(),
                y=_cdf['retention_rate'].tolist(),
                mode='lines+markers',
                name=_cohort,
                line=dict(color=_COHORT_COLORS[_i % len(_COHORT_COLORS)], width=2.5),
                marker=dict(size=7),
                hovertemplate=f'<b>{_cohort}</b><br>Year %{{x}}<br>Retention: %{{y:.1f}}%<extra></extra>',
            ))

        _fig.update_layout(
            title=dict(
                text=f"<b>On average, {_title_rate} of {_eco} developers are still active after 1 year</b><br><span style='font-size:14px;color:#666666'>Annual retention rate by cohort year</span>",
                font=dict(size=22, color='#1B4F72', family='Arial, sans-serif'),
                x=0,
                xanchor='left',
                y=0.95,
                yanchor='top',
            ),
            template='plotly_white',
            font=dict(family='Arial, sans-serif', size=12, color='#333'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100, l=70, r=60, b=60),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                bgcolor='rgba(255,255,255,0.8)',
            ),
            height=450,
        )
        _fig.update_xaxes(
            dtick=1,
            range=[-0.2, 5.2],
            showgrid=False,
            showline=True,
            linecolor='#1F2937',
            linewidth=1,
            tickfont=dict(size=11, color='#666'),
            title='',
        )
        _fig.update_yaxes(
            range=[0, 105],
            tickformat='.0f',
            ticksuffix='%',
            showgrid=True,
            gridcolor='#E5E7EB',
            gridwidth=1,
            showline=True,
            linecolor='#1F2937',
            linewidth=1,
            tickfont=dict(size=11, color='#666'),
            title='Retention Rate (%)',
            title_font=dict(size=12, color='#666'),
        )

        _states[_eco] = {'stats': _stats_html, 'chart': _json.loads(_fig.to_json())}

    _opts = [o for o in _ECOSYSTEMS if o in _states]
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _sel_html = '<div style="margin-bottom:8px"><span class="ddp-select-label">Ecosystem</span><select id="sel" class="ddp-select">' + ''.join(f'<option value="{i}">{o}</option>' for i, o in enumerate(_opts)) + '</select></div>'

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important}'
        'body{font-size:14px;color:#0f172a;padding:4px}'
        '.ddp-select{padding:4px 8px;border:1px solid #e2e8f0;border-radius:4px;font-size:0.8125em;color:#0f172a;background:#fff;cursor:pointer;outline:none}'
        '.ddp-select-label{font-size:0.6875em;color:#64748b;display:block;margin-bottom:2px}'
        '</style></head><body>'
        f'{_sel_html}'
        '<div id="stats" style="margin-bottom:12px"></div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'var sel=document.getElementById("sel");'
        'function show(i){document.getElementById("stats").innerHTML=D[O[i]].stats||"";'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});}'
        'sel.addEventListener("change",function(){show(parseInt(this.value))});'
        'show(0);'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" class="ddp-chart-frame-tall" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def section_cross_ecosystem(mo):
    mo.md("""
    ## Cross-Ecosystem Comparison
    *How do Ethereum, Solana, and Bitcoin retain their 2023 developer cohort?*
    """)
    return


@app.cell(hide_code=True)
def query_cross_ecosystem(mo, pyoso_db_conn):
    sql_cross_ecosystem = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            YEAR(MIN(rda.day)) AS cohort_year,
            MIN(rda.day) AS first_active_date
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana', 'Bitcoin')
        GROUP BY 1, 2
    ),

    cohort_sizes AS (
        SELECT
            ecosystem,
            cohort_year,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_year = 2023
        GROUP BY 1, 2
    ),

    yearly_activity AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.ecosystem,
            fa.cohort_year,
            YEAR(rda.day) AS activity_year
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE fa.ecosystem = e.name
            AND fa.cohort_year = 2023
    ),

    retention_data AS (
        SELECT
            ya.ecosystem,
            ya.cohort_year,
            ya.activity_year - ya.cohort_year AS years_since_join,
            COUNT(DISTINCT ya.canonical_developer_id) AS active_count
        FROM yearly_activity ya
        GROUP BY 1, 2, 3
    )

    SELECT
        rd.ecosystem,
        rd.years_since_join,
        rd.active_count,
        cs.cohort_size,
        ROUND(100.0 * rd.active_count / cs.cohort_size, 1) AS retention_rate
    FROM retention_data rd
    JOIN cohort_sizes cs
        ON rd.ecosystem = cs.ecosystem
        AND rd.cohort_year = cs.cohort_year
    WHERE rd.years_since_join >= 0
        AND rd.years_since_join <= 3
    ORDER BY rd.ecosystem, rd.years_since_join
    """

    with mo.persistent_cache("cross_ecosystem"):
        df_cross = mo.sql(sql_cross_ecosystem, engine=pyoso_db_conn, output=False)
        df_cross['retention_rate'] = df_cross['retention_rate'].astype(float)
        df_cross['years_since_join'] = df_cross['years_since_join'].astype(int)
    return (df_cross,)


@app.cell(hide_code=True)
def cross_ecosystem_chart(apply_ec_style, df_cross, go, mo):
    _eco_colors = {
        'Ethereum': '#1B4F72',
        'Solana': '#5DADE2',
        'Bitcoin': '#E59866',
    }

    _fig = go.Figure()
    for _eco in df_cross['ecosystem'].unique():
        _edf = df_cross[df_cross['ecosystem'] == _eco]
        _fig.add_trace(go.Scatter(
            x=_edf['years_since_join'],
            y=_edf['retention_rate'],
            mode='lines+markers',
            name=_eco,
            line=dict(color=_eco_colors.get(_eco, '#888'), width=2.5),
            marker=dict(size=7),
            hovertemplate=f'<b>{_eco}</b><br>Year %{{x}}<br>Retention: %{{y:.1f}}%<extra></extra>',
        ))

    _eth_1yr = df_cross[(df_cross['ecosystem'] == 'Ethereum') & (df_cross['years_since_join'] == 1)]['retention_rate'].values
    _eth_rate = f"{_eth_1yr[0]:.0f}%" if len(_eth_1yr) > 0 else "N/A"

    apply_ec_style(
        _fig,
        title=f"Ethereum retains {_eth_rate} of 2023 developers after 1 year",
        subtitle="Cross-ecosystem retention comparison — 2023 cohort",
        y_title="Retention Rate (%)",
        show_legend=True,
        right_margin=60,
    )

    _fig.update_layout(height=400)
    _fig.update_xaxes(dtick=1)
    _fig.update_yaxes(range=[0, 105], tickformat='.0f', ticksuffix='%')

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def setup_imports():
    import plotly.graph_objects as go
    return (go,)


@app.cell(hide_code=True)
def helper_apply_ec_style():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True, right_margin=180):
        title_text = ""
        if title:
            title_text = f"<b>{title}</b>"
            if subtitle:
                title_text += f"<br><span style='font-size:14px;color:#666666'>{subtitle}</span>"

        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=22, color="#1B4F72", family="Arial, sans-serif"),
                x=0,
                xanchor="left",
                y=0.95,
                yanchor="top"
            ) if title else None,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12, color="#333"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100 if title else 40, l=70, r=right_margin, b=60),
            hovermode='x unified',
            showlegend=show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.8)"
            )
        )

        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title="",
            tickformat="%b %Y"
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#E5E7EB",
            gridwidth=1,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=y_title if y_title else "",
            title_font=dict(size=12, color="#666"),
        )

        return fig
    return (apply_ec_style,)


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
