import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../styles/insights.css")


@app.cell(hide_code=True)
def header_title(mo):
    mo.md("""
    # Lifecycle Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Visualize the full lifecycle of a developer joining, contributing, and leaving an ecosystem.
    """)
    return


@app.cell(hide_code=True)
def header_accordion(mo):
    mo.accordion({
        "Overview": mo.md("""
- This notebook tracks developer lifecycle states — the month-by-month progression of developers joining, contributing, and eventually churning from an ecosystem
- It reveals how the balance between newcomers, established contributors, and churned developers shifts over time and across ecosystems
- Key metrics: monthly active developers by lifecycle state, churn ratio, dormant developer count
        """),
        "Context": mo.md("""
**Lifecycle labels** classify each developer's monthly activity into one of 16 granular states. These roll up into 4 categories used in the summary chart:

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

**Churn Ratio** = sum(churned + dormant) / sum(active) over the trailing window (12mo or all-time)

Data is bucketed monthly; private repos excluded; contributions include commits, issues, pull requests, and code reviews.

**Metric Definitions**
- Lifecycle — Developer stage definitions
- Activity — Monthly Active Developer (MAD) methodology
        """),
        "Data Sources": mo.md("""
- **Open Dev Data (Electric Capital)** — Ecosystem and developer taxonomy, [github.com/electric-capital/crypto-ecosystems](https://github.com/electric-capital/crypto-ecosystems)
- **Key Models** — `oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated`
        """),
    })
    return


@app.cell(hide_code=True)
def label_constants():
    ACTIVE_LABELS = [
        'first time', 'full time', 'new full time', 'part time to full time',
        'dormant to full time', 'part time', 'new part time',
        'full time to part time', 'dormant to part time',
    ]
    FT_LABELS = ['full time', 'new full time', 'part time to full time', 'dormant to full time']
    PT_LABELS = ['part time', 'new part time', 'full time to part time', 'dormant to part time']
    DORMANT_LABELS = [
        'dormant', 'first time to dormant', 'part time to dormant', 'full time to dormant',
    ]
    CHURNED_LABELS = [
        'churned (after first time)', 'churned (after reaching part time)',
        'churned (after reaching full time)',
    ]
    return ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, PT_LABELS


@app.cell(hide_code=True)
def section_ecosystem_overview(mo):
    mo.md("""
    ## Ecosystem Overview
    *Monthly developer snapshot for the selected ecosystem*
    """)
    return


@app.cell(hide_code=True)
def ecosystem_overview_tabs(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, PT_LABELS, LIFECYCLE_COLORS, df, mo, go, pd):
    import json as _json
    import html as _html_mod

    _ECOSYSTEMS = ['Ethereum', 'Bitcoin', 'Solana', 'Arbitrum', 'Base', 'Polygon', 'AI']

    def _stat(value, label, caption=''):
        return (
            f'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px;flex:1;min-width:140px">'
            f'<div style="font-size:20px;font-weight:700;color:#111">{value}</div>'
            f'<div style="font-size:12px;font-weight:600;color:#374151;margin-top:2px">{label}</div>'
            + (f'<div style="font-size:11px;color:#9ca3af;margin-top:2px">{caption}</div>' if caption else '')
            + '</div>'
        )

    _states = {}
    for _eco in _ECOSYSTEMS:
        _edf = df[df['project_display_name'] == _eco].copy()
        if _edf.empty:
            continue

        _latest_month = _edf['bucket_month'].max()
        _latest = _edf[_edf['bucket_month'] == _latest_month]

        _active_count = int(_latest[_latest['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
        _ft_count = int(_latest[_latest['label'].isin(FT_LABELS)]['developers_count'].sum())
        _pt_count = int(_latest[_latest['label'].isin(PT_LABELS)]['developers_count'].sum())
        _new_count = int(_latest[_latest['label'].isin(['first time'])]['developers_count'].sum())

        _twelve_months_ago = _latest_month - pd.DateOffset(months=12)
        _trailing_12 = _edf[_edf['bucket_month'] > _twelve_months_ago]
        _churn_12_sum = int(_trailing_12[_trailing_12['label'].isin(CHURNED_LABELS + DORMANT_LABELS)]['developers_count'].sum())
        _active_12_sum = int(_trailing_12[_trailing_12['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
        _churn_ratio_12 = (_churn_12_sum / _active_12_sum * 100) if _active_12_sum > 0 else 0

        _stats_html = (
            '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px">'
            + _stat(f'{_active_count:,}', 'Active Developers', f'Latest month ({str(_latest_month)[:7]})')
            + _stat(f'{_ft_count:,}', 'Full-Time', '10+ active days/month')
            + _stat(f'{_pt_count:,}', 'Part-Time', '1-9 active days/month')
            + _stat(f'{_new_count:,}', 'First-Time Contributors', 'New this month')
            + _stat(f'{_churn_ratio_12:.1f}%', 'Churn Ratio (12mo)', 'Churned+dormant / active')
            + '</div>'
        )

        def _categorize(label):
            if label == 'first time':
                return 'First Time'
            elif label in FT_LABELS:
                return 'Full Time'
            elif label in DORMANT_LABELS or label in CHURNED_LABELS:
                return 'Churned / Dormant'
            else:
                return 'Part Time'

        _edf['category'] = _edf['label'].apply(_categorize)
        _grouped = _edf.groupby(['bucket_month', 'category'])['developers_count'].sum().reset_index()

        _fig = go.Figure()
        for _cat in ['First Time', 'Part Time', 'Full Time']:
            _cat_data = _grouped[_grouped['category'] == _cat]
            _fig.add_trace(go.Bar(
                x=_cat_data['bucket_month'],
                y=_cat_data['developers_count'],
                name=_cat,
                marker_color=LIFECYCLE_COLORS[_cat],
                hovertemplate=f'<b>{_cat}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>',
            ))

        _cd = _grouped[_grouped['category'] == 'Churned / Dormant']
        _fig.add_trace(go.Bar(
            x=_cd['bucket_month'],
            y=-_cd['developers_count'],
            name='Churned / Dormant',
            marker_color=LIFECYCLE_COLORS['Churned / Dormant'],
            hovertemplate='<b>Churned / Dormant</b><br>%{x|%b %Y}<br>Developers: %{customdata:,.0f}<extra></extra>',
            customdata=_cd['developers_count'],
        ))

        _title_text = f'<b>{_active_count:,} monthly active developers in {_eco}</b><br><span style="font-size:14px;color:#666666">Developer lifecycle transitions — active (above zero) vs. churned/dormant (below zero)</span>'
        _fig.update_layout(
            barmode='relative',
            height=500,
            title=dict(text=_title_text, font=dict(size=22, color='#1B4F72', family='Arial, sans-serif'), x=0, xanchor='left', y=0.95, yanchor='top'),
            template='plotly_white',
            font=dict(family='Arial, sans-serif', size=12, color='#333'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100, l=70, r=60, b=60),
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(255,255,255,0.8)'),
        )
        _fig.update_xaxes(showgrid=False, showline=True, linecolor='#1F2937', linewidth=1, tickfont=dict(size=11, color='#666'), title='', tickformat='%b %Y')
        _fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB', gridwidth=1, showline=True, linecolor='#1F2937', linewidth=1, tickfont=dict(size=11, color='#666'), title='', tickformat=',d', zeroline=True, zerolinecolor='#1F2937', zerolinewidth=1.5)

        _states[_eco] = {'stats': _stats_html, 'chart': _json.loads(_fig.to_json())}

    _opts = [o for o in _ECOSYSTEMS if o in _states]
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _sel_html = '<div style="margin-bottom:8px"><span style="font-size:11px;color:#6b7280;display:block;margin-bottom:2px">Ecosystem</span><select id="sel" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;color:#374151;background:#fff;cursor:pointer">' + ''.join(f'<option value="{i}">{o}</option>' for i, o in enumerate(_opts)) + '</select></div>'

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
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
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:580px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def section_ecosystem_comparison(mo):
    mo.md("""
    ## Ecosystem Comparison
    *Compare lifecycle patterns across Bitcoin, Ethereum, and Solana*
    """)
    return


@app.cell(hide_code=True)
def ecosystem_comparison_tabs(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, df, mo, go):
    import json as _json
    import html as _html_mod

    _ECOSYSTEMS_COMP = ['Ethereum', 'Bitcoin', 'Solana']
    _METRICS = ['Monthly Active', 'Monthly Churn Rate', 'Full-Time Count', 'First-Time Count']

    _eco_colors = ['#1B4F72', '#7EB8DA', '#5DADE2']

    _states = {}
    for _metric in _METRICS:
        _fig = go.Figure()
        for _i, _eco in enumerate(_ECOSYSTEMS_COMP):
            _eco_df = df[df['project_display_name'] == _eco]
            if _eco_df.empty:
                continue

            if _metric == 'Monthly Active':
                _vals = _eco_df[_eco_df['label'].isin(ACTIVE_LABELS)].groupby('bucket_month')['developers_count'].sum()
            elif _metric == 'Full-Time Count':
                _vals = _eco_df[_eco_df['label'].isin(FT_LABELS)].groupby('bucket_month')['developers_count'].sum()
            elif _metric == 'First-Time Count':
                _vals = _eco_df[_eco_df['label'] == 'first time'].groupby('bucket_month')['developers_count'].sum()
            elif _metric == 'Monthly Churn Rate':
                _active = _eco_df[_eco_df['label'].isin(ACTIVE_LABELS)].groupby('bucket_month')['developers_count'].sum()
                _churn = _eco_df[_eco_df['label'].isin(CHURNED_LABELS + DORMANT_LABELS)].groupby('bucket_month')['developers_count'].sum()
                _vals = (_churn / _active * 100).replace([float('inf'), float('-inf')], 0).fillna(0)

            _fig.add_trace(go.Scatter(
                x=_vals.index,
                y=_vals.values,
                mode='lines',
                name=_eco,
                line=dict(color=_eco_colors[_i % len(_eco_colors)], width=2),
                hovertemplate=f'<b>{_eco}</b><br>%{{x|%b %Y}}<br>{_metric}: %{{y:,.0f}}<extra></extra>',
            ))

        _title_ecosystems = ', '.join(_ECOSYSTEMS_COMP)
        _title_text = f'<b>{_metric}: {_title_ecosystems}</b><br><span style="font-size:14px;color:#666666">Monthly trends across selected ecosystems</span>'
        _fig.update_layout(
            height=450,
            title=dict(text=_title_text, font=dict(size=22, color='#1B4F72', family='Arial, sans-serif'), x=0, xanchor='left', y=0.95, yanchor='top'),
            template='plotly_white',
            font=dict(family='Arial, sans-serif', size=12, color='#333'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100, l=70, r=60, b=60),
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(255,255,255,0.8)'),
        )
        _fig.update_xaxes(showgrid=False, showline=True, linecolor='#1F2937', linewidth=1, tickfont=dict(size=11, color='#666'), title='', tickformat='%b %Y')
        _fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB', gridwidth=1, showline=True, linecolor='#1F2937', linewidth=1, tickfont=dict(size=11, color='#666'), title=_metric, title_font=dict(size=12, color='#666'), tickformat=',d')

        if _metric == 'Monthly Churn Rate':
            _fig.update_yaxes(tickformat='.1f', ticksuffix='%')

        _states[_metric] = {'chart': _json.loads(_fig.to_json())}

    _opts = [m for m in _METRICS if m in _states]
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _sel_html = '<div style="margin-bottom:8px"><span style="font-size:11px;color:#6b7280;display:block;margin-bottom:2px">Metric</span><select id="sel" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;color:#374151;background:#fff;cursor:pointer">' + ''.join(f'<option value="{i}">{o}</option>' for i, o in enumerate(_opts)) + '</select></div>'

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '</style></head><body>'
        f'{_sel_html}'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'var sel=document.getElementById("sel");'
        'function show(i){Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});}'
        'sel.addEventListener("change",function(){show(parseInt(this.value))});'
        'show(0);'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def query_all_data(mo, pd, pyoso_db_conn):
    with mo.persistent_cache("lifecycle_data"):
        df = mo.sql(
            f"""
            SELECT
              project_display_name,
              bucket_month,
              label,
              developers_count
            FROM oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated
            ORDER BY 1,2,3
            """,
            output=False,
            engine=pyoso_db_conn
        )
        df['bucket_month'] = pd.to_datetime(df['bucket_month'])
    return (df,)


@app.cell(hide_code=True)
def setup_imports():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


@app.cell(hide_code=True)
def setup_constants():
    LIFECYCLE_COLORS = {
        'First Time': '#4C78A8',
        'Part Time': '#41AB5D',
        'Full Time': '#7A4D9B',
        'Churned / Dormant': '#D62728',
    }
    return (LIFECYCLE_COLORS,)


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
            tickformat=",d"
        )

        return fig
    return (apply_ec_style,)


@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
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
