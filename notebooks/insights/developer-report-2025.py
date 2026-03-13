import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def header_title(mo):
    mo.md("""
    # 2025 Developer Trends
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Explore an interactive reproduction of the [Electric Capital Developer Report](https://www.developerreport.com), updated with 2025 data.
    """)
    return


@app.cell(hide_code=True)
def header_accordion(mo):
    mo.accordion({
        "Overview": mo.md("""
- As of December 2025, the total number of monthly active developers (MADs) across all crypto ecosystems reached its highest recorded level, driven by growth in newer chains and Layer 2s
- Ethereum remains the largest single ecosystem by MAD count, though its share of total crypto developers continued to decline as multi-chain activity increases
- Newcomer developers (those active for less than 1 year) represented a significant portion of 2025 MADs, indicating continued onboarding despite broader market fluctuations
- Full-time developers (active 10+ months of the year) showed resilience, with retention rates improving year-over-year compared to the 2022-2023 downturn
        """),
        "Context": mo.md("""
- This analysis covers monthly active developers across all crypto ecosystems
- Data source: Open Dev Data (Electric Capital) via OSO data warehouse
- Time period: January 2015 to December 2025 (full historical data)
- Developers are original code authors (merge/PR integrators are not counted unless they authored commits)
- Monthly active developers are measured using a 28-day rolling activity window
- Uses curated Open Dev Data repository set (not comprehensive GitHub coverage)
- Developer identity resolution may miss some connections across accounts or pseudonyms
- Data freshness depends on Open Dev Data and OSO pipeline update cadence

**Metric Definitions**
- Activity — Monthly Active Developer (MAD) methodology

**Methodology**
- **Developers**: Original code authors only (merge/PR integrators excluded unless they authored commits)
- **Monthly Active Developers**: 28-day rolling activity window
- **Tenure Categories**: Newcomers (< 1 year), Emerging (1–2 years), Established (2+ years)
- **Activity Levels**: Full-time (sustained activity over 84-day window), Part-time (intermittent), One-time (sporadic)

> This analysis is inspired by the [Electric Capital Developer Report](https://www.developerreport.com). Data sourced from Open Dev Data via the OSO data warehouse.
        """),
        "Data Sources": mo.md("""
- **Open Dev Data** — Electric Capital's developer activity dataset, [github.com/electric-capital/crypto-ecosystems](https://github.com/electric-capital/crypto-ecosystems)
- **OSO API** — Data pipeline and metrics, [docs.oso.xyz](https://docs.oso.xyz/)
- **Key Models** — `oso.stg_opendevdata__eco_mads`, `oso.stg_opendevdata__ecosystems`
        """),
    })
    return


@app.cell(hide_code=True)
def setup_imports():
    import pandas as pd
    import plotly.graph_objects as go
    return go, pd


@app.cell(hide_code=True)
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


@app.cell(hide_code=True)
def setup_constants():
    # Electric Capital color palette (matching the reference charts)
    EC_LIGHT_BLUE = "#7EB8DA"   # Primary fill color for area charts
    EC_DARK_BLUE = "#1B4F72"    # For established developers / titles
    EC_MEDIUM_BLUE = "#5499C7"  # For emerging developers
    EC_TITLE_BLUE = "#1B4F72"   # Title color
    EC_SUBTITLE_GRAY = "#666666"  # Subtitle color

    # Tenure colors (matching EC report: light=newcomers at top, dark=established at bottom)
    TENURE_COLORS = {
        "Newcomers": "#B5D5E8",      # Lightest blue (top of stack)
        "Emerging": "#5DADE2",        # Medium blue (middle)
        "Established": "#1B4F72"      # Dark blue (bottom of stack)
    }

    # Activity level colors
    ACTIVITY_COLORS = {
        "One-time": "#F5B041",   # Orange/gold
        "Part-time": "#EC7063",  # Coral/red
        "Full-time": "#5DADE2"   # Blue
    }

    # Ecosystems to query
    ECOSYSTEMS = ["All Web3 Ecosystems", "Bitcoin", "Ethereum", "Solana"]
    SUPPORTED_ECOSYSTEMS = ["Bitcoin", "Ethereum", "Solana"]
    return (
        ACTIVITY_COLORS,
        ECOSYSTEMS,
        EC_LIGHT_BLUE,
        SUPPORTED_ECOSYSTEMS,
        TENURE_COLORS,
    )


@app.cell(hide_code=True)
def helper_apply_ec_style():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True,
                       right_margin=180):
        # Build title text with HTML styling
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

        # Style x-axis (clean, minimal)
        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title="",
            tickformat="%b %Y"  # Format as "Jan 2020"
        )

        # Style y-axis (light gridlines, clean labels)
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
            tickformat=",d"  # Format with thousands separator
        )

        return fig
    return (apply_ec_style,)


@app.cell(hide_code=True)
def helper_add_callout_annotation():
    def add_callout_annotation(fig, y_value, label, value, description,
                               color="#1B4F72", y_position=None):
        # Build annotation text with line breaks
        text = f"<b>{label}</b><br><br><span style='font-size:18px'>{value}</span><br><br><span style='font-size:11px'>{description}</span>"

        fig.add_annotation(
            x=1.02,
            y=y_value if y_position is None else y_position,
            xref="paper",
            yref="y" if y_position is None else "paper",
            text=text,
            showarrow=True,
            arrowhead=0,
            arrowwidth=1,
            arrowcolor="#999999",
            ax=20,
            ay=0,
            bordercolor="#CCCCCC",
            borderwidth=1,
            borderpad=8,
            bgcolor="white",
            font=dict(size=11, color=color),
            align="left",
            xanchor="left"
        )
        return fig
    return (add_callout_annotation,)


@app.cell(hide_code=True)
def helper_add_tenure_legend():
    def add_tenure_legend(fig, newcomers, emerging, established, colors):
        # Position annotations vertically on right side
        annotations = [
            (0.85, f"<b>{newcomers:,.0f}</b>", "Newcomers", "<1 year in crypto", colors["Newcomers"]),
            (0.55, f"<b>{emerging:,.0f}</b>", "Emerging", "1-2 yrs in crypto", colors["Emerging"]),
            (0.25, f"<b>{established:,.0f}</b>", "Established", "2+ years in crypto", colors["Established"]),
        ]

        for y_pos, value, label, desc, color in annotations:
            fig.add_annotation(
                x=1.02,
                y=y_pos,
                xref="paper",
                yref="paper",
                text=f"{value}<br><b style='color:{color}'>{label}</b><br><span style='font-size:10px;color:#666'>{desc}</span>",
                showarrow=False,
                font=dict(size=12, color="#333"),
                align="left",
                xanchor="left",
                bgcolor="white",
                bordercolor=color,
                borderwidth=2,
                borderpad=6
            )

        return fig
    return (add_tenure_legend,)


@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return


@app.cell(hide_code=True)
def query_all_data(ECOSYSTEMS, mo, pd, pyoso_db_conn):
    ecosystems_str = ", ".join(f"'{e}'" for e in ECOSYSTEMS)

    with mo.persistent_cache("report_data"):
        df_all = mo.sql(
            f"""
            SELECT
                e.name AS ecosystem_name,
                m.day,
                m.all_devs AS total_devs,
                m.devs_0_1y AS newcomers,
                m.devs_1_2y AS emerging,
                m.devs_2y_plus AS established,
                m.one_time_devs AS one_time,
                m.part_time_devs AS part_time,
                m.full_time_devs AS full_time
            FROM oso.stg_opendevdata__eco_mads m
            JOIN oso.stg_opendevdata__ecosystems e ON m.ecosystem_id = e.id
            WHERE e.name IN ({ecosystems_str})
              AND m.day >= DATE '2015-01-01'
              AND m.day < DATE '2026-01-01'
            ORDER BY e.name, m.day
            """,
            engine=pyoso_db_conn,
            output=False
        )

        df_all['day'] = pd.to_datetime(df_all['day'])

        # Add time period columns for aggregation
        df_all['year'] = df_all['day'].dt.year
        df_all['quarter'] = df_all['day'].dt.to_period('Q').dt.to_timestamp()
        df_all['month'] = df_all['day'].dt.to_period('M').dt.to_timestamp()
    return (df_all,)


@app.cell(hide_code=True)
def data_summary(df_all, mo):
    _ecosystems = df_all['ecosystem_name'].unique()
    _date_range = f"{df_all['day'].min().strftime('%Y-%m-%d')} to {df_all['day'].max().strftime('%Y-%m-%d')}"
    _rows = len(df_all)
    mo.md(f"**Data loaded:** {_rows:,} rows across {len(_ecosystems)} ecosystems ({_date_range})")
    return


@app.cell(hide_code=True)
def section_overall_trends(mo):
    mo.md("""
    ## Overall Developer Trends
    *High-level patterns across all crypto ecosystems*
    """)
    return


@app.cell(hide_code=True)
def chart1_total_mads(
    EC_LIGHT_BLUE,
    add_callout_annotation,
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 1: Total Monthly Active Developers Over Time"""
    import json as _json
    import html as _html_mod

    _OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    _states = {}
    for _opt in _OPTS:
        _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()
        _cutoff = _time_filters[_opt]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _current_date = _df['day'].max()
        _current_value = _df[_df['day'] == _current_date]['total_devs'].values[0]

        _fig = go.Figure()

        _fig.add_trace(go.Scatter(
            x=_df['day'],
            y=_df['total_devs'],
            fill='tozeroy',
            fillcolor=EC_LIGHT_BLUE,
            line=dict(color=EC_LIGHT_BLUE, width=1),
            mode='lines',
            name='Monthly Active Developers',
            hovertemplate='<b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>'
        ))

        apply_ec_style(
            _fig,
            title=f"{_current_value:,.0f} monthly active open-source developers contribute to crypto",
            subtitle="All crypto monthly active developers",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        _year = int(_current_date.year)
        _df_year = _df[_df["day"].dt.year == _year]

        if len(_df_year) > 0:
            _start_date = _df_year["day"].min()
            _end_date = _df_year["day"].max()
            _start_value = _df_year[_df_year["day"] == _start_date]["total_devs"].iloc[0]
            _end_value = _df_year[_df_year["day"] == _end_date]["total_devs"].iloc[0]

            _fig.add_trace(
                go.Scatter(
                    x=[_start_date, _end_date],
                    y=[_start_value, _end_value],
                    mode="markers",
                    marker=dict(size=7, color="#1B4F72", line=dict(width=1, color="white")),
                    showlegend=False,
                    hovertemplate="<b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>",
                )
            )

            _fig.add_annotation(
                x=_start_date,
                y=_start_value,
                text=f"<b>{_start_date.strftime('%b %Y')}</b><br>{_start_value:,.0f}",
                showarrow=False,
                yshift=-22,
                font=dict(size=10, color="#333"),
                align="center",
                bgcolor="white",
                bordercolor="#CCCCCC",
                borderwidth=1,
                borderpad=5,
            )

            _fig.add_annotation(
                x=_end_date,
                y=_end_value,
                text=f"<b>{_end_date.strftime('%b %Y')}</b><br>{_end_value:,.0f}",
                showarrow=False,
                yshift=-22,
                font=dict(size=10, color="#333"),
                align="center",
                bgcolor="white",
                bordercolor="#CCCCCC",
                borderwidth=1,
                borderpad=5,
            )

        _peak_idx = _df["total_devs"].idxmax()
        _peak_date = _df.loc[_peak_idx, "day"]
        _peak_value = _df.loc[_peak_idx, "total_devs"]

        _fig.add_trace(
            go.Scatter(
                x=[_peak_date],
                y=[_peak_value],
                mode="markers",
                marker=dict(size=8, color="#1B4F72", line=dict(width=1, color="white")),
                showlegend=False,
                hovertemplate="<b>Peak</b><br>%{x|%b %Y}<br>Developers: %{y:,.0f}<extra></extra>",
            )
        )
        _fig.add_annotation(
            x=_peak_date,
            y=_peak_value,
            text=f"<b>Peak</b><br>{_peak_value:,.0f}<br><span style='font-size:10px;color:#666'>{_peak_date.strftime('%b %Y')}</span>",
            showarrow=True,
            arrowhead=0,
            arrowcolor="#666",
            ax=0,
            ay=-55,
            font=dict(size=11, color="#333"),
            align="center",
            bgcolor="white",
            bordercolor="#CCCCCC",
            borderwidth=1,
            borderpad=6,
        )

        _fig.update_xaxes(range=[_df["day"].min(), _df["day"].max()], autorange=False)
        _fig.update_layout(height=500)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def chart2_tenure_composition(
    TENURE_COLORS,
    add_tenure_legend,
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 2: Developer Composition by Tenure - Stacked Area Chart"""
    import json as _json
    import html as _html_mod

    _OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    _states = {}
    for _opt in _OPTS:
        _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()
        _cutoff = _time_filters[_opt]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _fig = go.Figure()

        for _segment, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_segment,
                mode='lines',
                stackgroup='one',
                fillcolor=TENURE_COLORS[_segment],
                line=dict(width=0.5, color=TENURE_COLORS[_segment]),
                hovertemplate=f'<b>{_segment}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        _current_row = _df.iloc[-1]
        _current_newcomers = _current_row['newcomers']
        _current_emerging = _current_row['emerging']
        _current_established = _current_row['established']

        apply_ec_style(
            _fig,
            title="But devs working in crypto for 1+ years grew steadily",
            subtitle="All crypto monthly active developers by tenure",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        add_tenure_legend(_fig, _current_newcomers, _current_emerging, _current_established, TENURE_COLORS)

        _fig.update_layout(height=500)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def chart3_experienced_devs(
    TENURE_COLORS,
    apply_ec_style,
    df_all,
    go,
    mo,
):
    """Chart 3: The Experienced Developer Story - Stacked area with comparison annotations"""
    import json as _json
    import html as _html_mod

    _OPTS = ['YoY (2024 vs 2025)', '3-Year (2022 vs 2025)', '5-Year (2020 vs 2025)']

    _period_map = {
        'YoY (2024 vs 2025)': (2024, 2025, 1),
        '3-Year (2022 vs 2025)': (2022, 2025, 3),
        '5-Year (2020 vs 2025)': (2020, 2025, 5),
    }

    _df_base = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()
    _df_base['experienced'] = _df_base['emerging'] + _df_base['established']

    _states = {}
    for _opt in _OPTS:
        _df = _df_base.copy()
        _start_year, _end_year, _years = _period_map[_opt]

        _start_df = _df[_df['year'] == _start_year]
        _end_df = _df[_df['year'] == _end_year]

        _start_row = _start_df.iloc[-1] if len(_start_df) > 0 else None
        _end_row = _end_df.iloc[-1] if len(_end_df) > 0 else None

        if _start_row is not None and _end_row is not None:
            _start_exp = _start_row['experienced']
            _end_exp = _end_row['experienced']
            _exp_change = _end_exp - _start_exp
            _exp_change_pct = ((_end_exp - _start_exp) / _start_exp) * 100
            _exp_color = "#27AE60" if _exp_change_pct > 0 else "#E74C3C"
            _start_date = _start_row['day']
            _end_date = _end_row['day']
        else:
            _start_exp = _end_exp = _exp_change = _exp_change_pct = 0
            _exp_color = "#666"
            _start_date = _end_date = _df['day'].max()

        _fig = go.Figure()

        for _segment, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_segment,
                mode='lines',
                stackgroup='one',
                fillcolor=TENURE_COLORS[_segment],
                line=dict(width=0.5, color=TENURE_COLORS[_segment]),
                hovertemplate=f'<b>{_segment}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        _fig.add_vline(x=_start_date, line_dash="dash", line_color="#666", line_width=1)
        _fig.add_vline(x=_end_date, line_dash="dash", line_color="#666", line_width=1)

        _fig.add_vrect(
            x0=_start_date, x1=_end_date,
            fillcolor="rgba(200, 200, 200, 0.1)",
            line_width=0
        )

        _fig.add_annotation(
            x=_start_date + (_end_date - _start_date) / 2,
            y=1.02, yref="paper",
            text=f"Dec {_start_year} - {_end_year}",
            showarrow=False,
            font=dict(size=11, color="#666")
        )

        apply_ec_style(
            _fig,
            title=f"Experienced devs (1+ years) grew by <span style='color:{_exp_color}'>{_exp_change_pct:+.0f}%</span> ({_exp_change:+,.0f}) in {_end_year}",
            subtitle=f"This reflects an increase of {_exp_change:+,.0f} developers outside of Newcomers",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        _current = _df.iloc[-1]
        _annotations_data = [
            (0.88, "Newcomers", _current['newcomers'], "<1 year in crypto", TENURE_COLORS["Newcomers"]),
            (0.58, "Emerging", _current['emerging'], "1-2 years in crypto", TENURE_COLORS["Emerging"]),
            (0.28, "Established", _current['established'], "2+ years in crypto", TENURE_COLORS["Established"]),
        ]

        for _y, _label, _val, _desc, _color in _annotations_data:
            _fig.add_annotation(
                x=1.02, y=_y, xref="paper", yref="paper",
                text=f"<span style='color:{_color}'>\u25CF</span> <b>{_label}</b><br><span style='font-size:10px;color:#666'>{_desc}</span>",
                showarrow=False, font=dict(size=11), align="left", xanchor="left"
            )

        _fig.add_annotation(
            x=_start_date, y=_start_exp,
            text=f"{_start_exp:,.0f}",
            showarrow=True, arrowhead=0, arrowcolor="#666",
            ax=-30, ay=20,
            font=dict(size=10, color="#666"),
            bgcolor="white", borderpad=2
        )

        _fig.add_annotation(
            x=_end_date, y=_end_exp,
            text=f"<span style='color:{_exp_color}'>{_exp_change_pct:+.0f}%</span><br>{_exp_change:+,.0f} devs",
            showarrow=True, arrowhead=0, arrowcolor=_exp_color,
            ax=40, ay=-20,
            font=dict(size=11),
            bgcolor="white", bordercolor=_exp_color, borderwidth=1, borderpad=4
        )

        _fig.add_annotation(
            x=_end_date, y=_end_exp,
            text=f"{_end_exp:,.0f}",
            showarrow=False,
            yshift=-25,
            font=dict(size=10, color="#666")
        )

        _fig.update_layout(height=500)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def chart4_developer_changes(
    TENURE_COLORS,
    apply_ec_style,
    df_all,
    go,
    mo,
):
    """Chart 4: Where Did Developers Go? - Multi-line chart with change annotations"""
    import json as _json
    import html as _html_mod

    _OPTS = ['2025 vs 2024', '2024 vs 2023', '2023 vs 2022', '2022 vs 2021']

    _df_base = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()

    _states = {}
    for _opt in _OPTS:
        _years_split = _opt.split(' vs ')
        _end_year = int(_years_split[0])
        _start_year = int(_years_split[1])

        _start_df = _df_base[_df_base['year'] == _start_year]
        _end_df = _df_base[_df_base['year'] == _end_year]

        if len(_start_df) == 0 or len(_end_df) == 0:
            _fig = go.Figure()
            _fig.add_annotation(
                text="Insufficient data for selected comparison period",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="#666")
            )
            _states[_opt] = {'chart': _json.loads(_fig.to_json())}
            continue

        _start_row = _start_df.iloc[-1]
        _end_row = _end_df.iloc[-1]
        _start_date = _start_row['day']
        _end_date = _end_row['day']

        _changes = {}
        for _seg in ['newcomers', 'emerging', 'established']:
            _s = _start_row[_seg]
            _e = _end_row[_seg]
            _changes[_seg] = {
                'start': _s,
                'end': _e,
                'diff': _e - _s,
                'pct': ((_e - _s) / _s) * 100 if _s > 0 else 0
            }

        _fig = go.Figure()

        _segment_config = [
            ("Newcomers", "newcomers", TENURE_COLORS["Newcomers"]),
            ("Emerging", "emerging", TENURE_COLORS["Emerging"]),
            ("Established", "established", TENURE_COLORS["Established"]),
        ]

        for _label, _col, _color in _segment_config:
            _fig.add_trace(go.Scatter(
                x=_df_base['day'],
                y=_df_base[_col],
                name=_label,
                mode='lines',
                line=dict(width=2, color=_color),
                hovertemplate=f'<b>{_label}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        _fig.add_vline(x=_start_date, line_dash="dash", line_color="#666", line_width=1)
        _fig.add_vline(x=_end_date, line_dash="dash", line_color="#666", line_width=1)

        _fig.add_annotation(
            x=_start_date + (_end_date - _start_date) / 2,
            y=1.02, yref="paper",
            text=f"Dec {_start_year} - {_end_year}",
            showarrow=False,
            font=dict(size=11, color="#666")
        )

        apply_ec_style(
            _fig,
            title=f"Developer losses came from the least tenured developers:<br>Newcomers fell by <span style='color:#E74C3C'>{_changes['newcomers']['pct']:.0f}%</span>",
            subtitle="All crypto monthly active developers by tenure",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        _y_positions = [0.85, 0.50, 0.20]
        for _i, (_label, _col, _color) in enumerate(_segment_config):
            _c = _changes[_col]
            _pct_color = "#27AE60" if _c['pct'] > 0 else "#E74C3C"

            _fig.add_annotation(
                x=1.02, y=_y_positions[_i], xref="paper", yref="paper",
                text=f"<b>{_label}</b><br><span style='font-size:18px;color:{_pct_color}'>{_c['pct']:+.0f}%</span><br><span style='font-size:10px;color:#666'>{_c['diff']:+,.0f} devs</span>",
                showarrow=False,
                font=dict(size=11),
                align="left",
                xanchor="left",
                bgcolor="white",
                bordercolor=_color,
                borderwidth=2,
                borderpad=6
            )

        for _label, _col, _color in _segment_config:
            _fig.add_trace(go.Scatter(
                x=[_start_date, _end_date],
                y=[_changes[_col]['start'], _changes[_col]['end']],
                mode='markers',
                marker=dict(size=8, color=_color, line=dict(width=1, color='white')),
                showlegend=False,
                hoverinfo='skip'
            ))

        for _label, _col, _color in _segment_config:
            _fig.add_annotation(
                x=_start_date, y=_changes[_col]['start'],
                text=f"{_changes[_col]['start']:,.0f}",
                showarrow=False,
                xshift=-35,
                font=dict(size=9, color="#666")
            )

        _fig.update_layout(height=500)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def section_newcomer_trends(mo):
    mo.md("""
    ## Newcomer Trends
    *How new developer acquisition tracks with market cycles*
    """)
    return


@app.cell(hide_code=True)
def chart5_newcomer_volatility(
    EC_LIGHT_BLUE,
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 5: Newcomer Volatility - Bar Chart by Year (Yearly granularity, selectable time range)"""
    import json as _json
    import html as _html_mod

    _OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
    }

    _states = {}
    for _opt in _OPTS:
        _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()
        _cutoff = _time_filters[_opt]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _df_agg = _df.groupby('year').agg({'newcomers': 'max'}).reset_index()
        _df_agg['label'] = _df_agg['year'].astype(int).astype(str)
        _x_vals = _df_agg['label']

        _peak_idx = _df_agg['newcomers'].idxmax()
        _peak_year = _df_agg.loc[_peak_idx, 'label']
        _peak_value = _df_agg.loc[_peak_idx, 'newcomers']

        _fig = go.Figure()

        _fig.add_trace(go.Bar(
            x=_x_vals,
            y=_df_agg['newcomers'],
            marker_color=EC_LIGHT_BLUE,
            text=_df_agg['newcomers'].apply(lambda x: f'{x:,.0f}'),
            textposition='outside',
            textfont=dict(size=10, color="#666"),
            hovertemplate='<b>%{x}</b><br>Newcomers: %{y:,.0f}<extra></extra>'
        ))

        apply_ec_style(
            _fig,
            title="Newcomers tend to follow crypto asset price appreciation",
            subtitle=f"{_peak_value:,.0f} developers joined crypto in {_peak_year}",
            y_title="Developers",
            show_legend=False,
            right_margin=60
        )

        _max_val = _df_agg['newcomers'].max()
        _fig.update_yaxes(range=[0, _max_val * 1.15])
        _fig.update_layout(height=450)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def section_ecosystem_landscape(mo):
    mo.md("""
    ## Ecosystem Landscape
    *Developer distribution across major ecosystems*
    """)
    return


@app.cell(hide_code=True)
def chart6_btc_eth_share(
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 6: Developer Distribution - tabs for view type, sub-tabs for time range"""
    import json as _json
    import html as _html_mod

    # Tabs: view type x time range combined as "View | Time"
    _VIEW_OPTS = ['Percentage (Stacked)', 'Absolute Counts']
    _TIME_OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    # Build base merged dataframe
    _df_total = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()
    _df_btc = df_all[df_all['ecosystem_name'] == 'Bitcoin'].copy()
    _df_eth = df_all[df_all['ecosystem_name'] == 'Ethereum'].copy()
    _df_sol = df_all[df_all['ecosystem_name'] == 'Solana'].copy()

    _df_merged = _df_total[['day', 'total_devs']].rename(columns={'total_devs': 'total'})
    _df_merged = _df_merged.merge(_df_btc[['day', 'total_devs']].rename(columns={'total_devs': 'bitcoin'}), on='day', how='left')
    _df_merged = _df_merged.merge(_df_eth[['day', 'total_devs']].rename(columns={'total_devs': 'ethereum'}), on='day', how='left')
    _df_merged = _df_merged.merge(_df_sol[['day', 'total_devs']].rename(columns={'total_devs': 'solana'}), on='day', how='left')
    _df_merged = _df_merged.fillna(0)
    _df_merged['other'] = (_df_merged['total'] - _df_merged['bitcoin'] - _df_merged['ethereum'] - _df_merged['solana']).clip(lower=0)
    _df_merged['btc_pct'] = (_df_merged['bitcoin'] / _df_merged['total']) * 100
    _df_merged['eth_pct'] = (_df_merged['ethereum'] / _df_merged['total']) * 100
    _df_merged['sol_pct'] = (_df_merged['solana'] / _df_merged['total']) * 100
    _df_merged['other_pct'] = (_df_merged['other'] / _df_merged['total']) * 100

    _btc_color = "#F7931A"
    _eth_color = "#627EEA"
    _sol_color = "#14F195"
    _other_color = "#9CA3AF"

    # Combine view + time range into a single tab key: "Percentage | All Time" etc.
    _OPTS = [f'{v} | {t}' for v in _VIEW_OPTS for t in _TIME_OPTS]

    _states = {}
    for _opt in _OPTS:
        _view, _time_key = _opt.split(' | ', 1)
        _df = _df_merged.copy()
        _cutoff = _time_filters[_time_key]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _current = _df.iloc[-1]
        _btc_eth_share = _current['btc_pct'] + _current['eth_pct']

        _fig = go.Figure()

        if _view == 'Percentage (Stacked)':
            _segments = [
                ("Other ecosystems", "other_pct", _other_color),
                ("Solana", "sol_pct", _sol_color),
                ("Ethereum", "eth_pct", _eth_color),
                ("Bitcoin", "btc_pct", _btc_color),
            ]
            for _name, _col, _color in _segments:
                _current_val = _current[_col]
                _fig.add_trace(go.Scatter(
                    x=_df['day'],
                    y=_df[_col],
                    name=f"{_name} ({_current_val:.0f}%)",
                    mode='lines',
                    stackgroup='one',
                    groupnorm='percent',
                    fillcolor=_color,
                    line=dict(width=0.5, color=_color),
                    hovertemplate=f'<b>{_name}</b><br>%{{x|%b %Y}}<br>Share: %{{y:.1f}}%<extra></extra>'
                ))
            _fig.update_yaxes(range=[0, 100], ticksuffix="%")
            _y_title = "% of Developers"
        else:
            _segments = [
                ("Other ecosystems", "other", _other_color),
                ("Solana", "solana", _sol_color),
                ("Ethereum", "ethereum", _eth_color),
                ("Bitcoin", "bitcoin", _btc_color),
            ]
            for _name, _col, _color in _segments:
                _current_val = _current[_col]
                _fig.add_trace(go.Scatter(
                    x=_df['day'],
                    y=_df[_col],
                    name=f"{_name} ({_current_val:,.0f})",
                    mode='lines',
                    stackgroup='one',
                    fillcolor=_color,
                    line=dict(width=0.5, color=_color),
                    hovertemplate=f'<b>{_name}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
                ))
            _y_title = "Developers"

        apply_ec_style(
            _fig,
            title=f"Bitcoin and Ethereum account for {_btc_eth_share:.0f}% of all crypto developers",
            subtitle="Monthly active developers by ecosystem",
            y_title=_y_title,
            show_legend=True,
            right_margin=60
        )

        _fig.update_layout(
            height=500,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#CCCCCC",
                borderwidth=1
            )
        )

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def section_ecosystem_deep_dive(mo):
    mo.md("""
    ## Deep Dive: Ecosystem Analysis
    *Explore developer trends for specific ecosystems*
    """)
    return


@app.cell(hide_code=True)
def chart_ecosystem_total_devs(
    EC_LIGHT_BLUE,
    add_callout_annotation,
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Deep Dive Chart 1: Ecosystem Total Active Developers — tabs: ecosystem x time range"""
    import json as _json
    import html as _html_mod

    _ECO_OPTS = ['Bitcoin', 'Ethereum', 'Solana']
    _TIME_OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    _OPTS = [f'{e} | {t}' for e in _ECO_OPTS for t in _TIME_OPTS]

    _states = {}
    for _opt in _OPTS:
        _eco_name, _time_key = _opt.split(' | ', 1)
        _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

        if len(_df) == 0:
            _fig = go.Figure()
            _fig.add_annotation(text="No data available", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#666"))
            _states[_opt] = {'chart': _json.loads(_fig.to_json())}
            continue

        _cutoff = _time_filters[_time_key]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _current_row = _df.iloc[-1]
        _current_devs = _current_row['total_devs']
        _current_date = _current_row['day']

        _fig = go.Figure()

        _fig.add_trace(go.Scatter(
            x=_df['day'],
            y=_df['total_devs'],
            mode='lines',
            line=dict(color=EC_LIGHT_BLUE, width=2),
            fill='tozeroy',
            fillcolor=EC_LIGHT_BLUE,
            hovertemplate='<b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>'
        ))

        apply_ec_style(
            _fig,
            title=f"{_current_devs:,.0f} monthly active developers supported {_eco_name}",
            subtitle=f"{_eco_name} monthly active developers",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        add_callout_annotation(
            _fig,
            y_value=_current_devs,
            label=_current_date.strftime('%B %Y'),
            value=f"{_current_devs:,.0f}",
            description="monthly active<br>developers"
        )

        _fig.update_layout(height=450)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def chart_ecosystem_tenure(
    TENURE_COLORS,
    add_tenure_legend,
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Deep Dive Chart 2: Ecosystem Developer Composition by Tenure"""
    import json as _json
    import html as _html_mod

    _ECO_OPTS = ['Bitcoin', 'Ethereum', 'Solana']
    _TIME_OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    _OPTS = [f'{e} | {t}' for e in _ECO_OPTS for t in _TIME_OPTS]

    _states = {}
    for _opt in _OPTS:
        _eco_name, _time_key = _opt.split(' | ', 1)
        _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

        if len(_df) == 0:
            _fig = go.Figure()
            _fig.add_annotation(text="No data available", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#666"))
            _states[_opt] = {'chart': _json.loads(_fig.to_json())}
            continue

        _cutoff = _time_filters[_time_key]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _fig = go.Figure()

        for _segment, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_segment,
                mode='lines',
                stackgroup='one',
                fillcolor=TENURE_COLORS[_segment],
                line=dict(width=0.5, color=TENURE_COLORS[_segment]),
                hovertemplate=f'<b>{_segment}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        _current = _df.iloc[-1]

        apply_ec_style(
            _fig,
            title=f"{_eco_name} Developer Composition by Tenure",
            subtitle="Segmented by Newcomers, Emerging, and Established developers",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        add_tenure_legend(_fig, _current['newcomers'], _current['emerging'], _current['established'], TENURE_COLORS)

        _fig.update_layout(height=450)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def chart_ecosystem_activity(
    ACTIVITY_COLORS,
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Deep Dive Chart 3: Ecosystem Activity Levels"""
    import json as _json
    import html as _html_mod

    _ECO_OPTS = ['Bitcoin', 'Ethereum', 'Solana']
    _TIME_OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    _OPTS = [f'{e} | {t}' for e in _ECO_OPTS for t in _TIME_OPTS]

    _states = {}
    for _opt in _OPTS:
        _eco_name, _time_key = _opt.split(' | ', 1)
        _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

        if len(_df) == 0:
            _fig = go.Figure()
            _fig.add_annotation(text="No data available", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#666"))
            _states[_opt] = {'chart': _json.loads(_fig.to_json())}
            continue

        _cutoff = _time_filters[_time_key]
        if _cutoff is not None:
            _df = _df[_df['day'] >= _cutoff]

        _fig = go.Figure()

        for _level, _col in [("Full-time", "full_time"), ("Part-time", "part_time"), ("One-time", "one_time")]:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_level,
                mode='lines',
                line=dict(width=2, color=ACTIVITY_COLORS[_level]),
                hovertemplate=f'<b>{_level}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        apply_ec_style(
            _fig,
            title=f"{_eco_name} Developers by Activity Level",
            subtitle="Segmented by sustained activity patterns (84-day rolling window)",
            y_title="Developers",
            show_legend=True,
            right_margin=60
        )

        _fig.update_layout(height=450)

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def chart_ecosystem_newcomers_by_year(
    apply_ec_style,
    df_all,
    go,
    mo,
):
    """Deep Dive Chart 4: Ecosystem New Developer Acquisition by Year"""
    import json as _json
    import html as _html_mod

    _ECO_OPTS = ['Bitcoin', 'Ethereum', 'Solana']

    _bar_color = "#B8C9E8"

    _states = {}
    for _eco_name in _ECO_OPTS:
        _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

        if len(_df) == 0:
            _fig = go.Figure()
            _fig.add_annotation(text="No data available", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#666"))
            _states[_eco_name] = {'chart': _json.loads(_fig.to_json())}
            continue

        _df_agg = _df.groupby('year').agg({'newcomers': 'max'}).reset_index()
        _df_agg = _df_agg[_df_agg['year'] >= 2015]

        _recent_years = _df_agg[_df_agg['year'] >= _df_agg['year'].max() - 2]
        _recent_values = _recent_years['newcomers'].tolist()
        _recent_year_labels = _recent_years['year'].astype(int).tolist()

        _min_recent = min(_recent_values) if _recent_values else 0
        if _min_recent >= 10000:
            _threshold = (_min_recent // 5000) * 5000
        elif _min_recent >= 1000:
            _threshold = (_min_recent // 1000) * 1000
        else:
            _threshold = 0

        if _threshold > 0 and len(_recent_year_labels) >= 2:
            _years_str = ", ".join([f"'{str(y)[-2:]}" for y in _recent_year_labels])
            _title = f"{_threshold:,.0f}+ new devs supported {_eco_name} in {_years_str}"
        else:
            _title = f"{_eco_name} new developers"

        _fig = go.Figure()

        _fig.add_trace(go.Bar(
            x=_df_agg['year'].astype(int).astype(str),
            y=_df_agg['newcomers'],
            marker_color=_bar_color,
            text=_df_agg['newcomers'].apply(lambda x: f'{x:,.0f}'),
            textposition='outside',
            textfont=dict(size=10, color="#666"),
            hovertemplate='<b>%{x}</b><br>New Developers: %{y:,.0f}<extra></extra>'
        ))

        if _threshold > 0:
            _fig.add_hline(
                y=_threshold,
                line_dash="dash",
                line_color="#999",
                line_width=1,
                annotation_text=f"{_threshold:,.0f}+ new developers supported {_eco_name} for the last {len(_recent_year_labels)} years",
                annotation_position="top left",
                annotation_font=dict(size=10, color="#666")
            )

        apply_ec_style(
            _fig,
            title=_title,
            subtitle=f"{_eco_name} new developers",
            y_title="Developers",
            show_legend=False,
            right_margin=60
        )

        _max_val = _df_agg['newcomers'].max()
        _fig.update_yaxes(range=[0, _max_val * 1.18])
        _fig.update_layout(height=450)

        _states[_eco_name] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


@app.cell(hide_code=True)
def section_comparative(mo):
    mo.md("""
    ## Comparative Analysis
    *Compare metrics across ecosystems over time*
    """)
    return


@app.cell(hide_code=True)
def comparison_chart(
    apply_ec_style,
    df_all,
    go,
    mo,
    pd,
):
    """Comparative analysis - tabs: metric x time range (fixed: Ethereum vs Bitcoin)"""
    import json as _json
    import html as _html_mod

    _METRIC_OPTS = [
        'Total Developers',
        'Newcomers',
        'Emerging',
        'Established',
        'Full-time',
        'Part-time',
        'One-time',
    ]
    _TIME_OPTS = ['All Time', 'Last 5 Years', 'Last 3 Years', 'Last Year']

    _metric_map = {
        'Total Developers': 'total_devs',
        'Newcomers': 'newcomers',
        'Emerging': 'emerging',
        'Established': 'established',
        'Full-time': 'full_time',
        'Part-time': 'part_time',
        'One-time': 'one_time',
    }

    _time_filters = {
        'All Time': None,
        'Last 5 Years': pd.Timestamp('2020-01-01'),
        'Last 3 Years': pd.Timestamp('2022-01-01'),
        'Last Year': pd.Timestamp('2024-01-01'),
    }

    _selected_ecos = ['Ethereum', 'Bitcoin', 'Solana']
    _colors = ["#5DADE2", "#F5B041", "#58D68D"]

    _OPTS = [f'{m} | {t}' for m in _METRIC_OPTS for t in _TIME_OPTS]

    _states = {}
    for _opt in _OPTS:
        _metric_name, _time_key = _opt.split(' | ', 1)
        _col = _metric_map[_metric_name]
        _cutoff = _time_filters[_time_key]

        _fig = go.Figure()

        for _i, _eco in enumerate(_selected_ecos):
            _df_eco = df_all[df_all['ecosystem_name'] == _eco].copy()
            if _cutoff is not None:
                _df_eco = _df_eco[_df_eco['day'] >= _cutoff]

            if len(_df_eco) > 0:
                _color = _colors[_i % len(_colors)]
                _current_val = _df_eco.iloc[-1][_col]
                _fig.add_trace(go.Scatter(
                    x=_df_eco['day'],
                    y=_df_eco[_col],
                    name=f"{_eco} ({_current_val:,.0f})",
                    mode='lines',
                    line=dict(width=2, color=_color),
                    hovertemplate=f'<b>{_eco}</b><br>%{{x|%b %Y}}<br>{_metric_name}: %{{y:,.0f}}<extra></extra>'
                ))

        _title = f"Ecosystem Comparison: {_metric_name}"

        apply_ec_style(
            _fig,
            title=_title,
            subtitle=f"{_metric_name} over time",
            y_title="Developers",
            show_legend=True,
            right_margin=60
        )

        _fig.update_layout(
            height=450,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#CCCCCC",
                borderwidth=1
            )
        )

        _states[_opt] = {'chart': _json.loads(_fig.to_json())}

    _opts = list(_states.keys())
    _djs_safe = _json.dumps(_states).replace('</', '<\\/')
    _opts_js = _json.dumps(_opts)
    _btn_html = ''.join(f'<button class="tab-btn" data-idx="{i}">{o}</button>' for i, o in enumerate(_opts))

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
        '<style>'
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{font-family:Arial,sans-serif;font-size:13px;padding:4px}'
        '.tab-btn{padding:6px 14px;border:none;background:none;border-radius:6px;font-size:13px;cursor:pointer;color:#6b7280}'
        '.tab-btn:hover{background:#f3f4f6;color:#111}'
        '.tab-btn.active{background:#eff6ff;color:#2563eb;font-weight:600}'
        '.tab-bar{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}'
        '</style></head><body>'
        f'<div class="tab-bar">{_btn_html}</div>'
        '<div id="chart"></div>'
        f'<script>var D={_djs_safe};var O={_opts_js};'
        'document.querySelectorAll(".tab-btn").forEach(function(btn,i){'
        'btn.addEventListener("click",function(){'
        'document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.remove("active")});'
        'btn.classList.add("active");'
        'Plotly.react("chart",D[O[i]].chart.data,D[O[i]].chart.layout,{responsive:true});'
        '});});'
        'var _b=document.querySelectorAll(".tab-btn");if(_b.length)_b[0].click();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)
    mo.Html(f'<iframe srcdoc="{_src}" style="width:100%;height:520px;border:none;display:block" scrolling="no"></iframe>')
    return


if __name__ == "__main__":
    app.run()
