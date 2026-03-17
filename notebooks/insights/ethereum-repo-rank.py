import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../styles/insights.css")


# =============================================================================
# HEADER + PANEL FILTER
# =============================================================================


@app.cell(hide_code=True)
def _(mo):
    _header_html = '<div class="ddp-header"><h1>Ethereum Repo Rank</h1><p>Trending repos and scouts in the Ethereum builder community.</p><div class="ddp-header-meta"><span>Created: <span class="ddp-badge">2026-03-16</span></span></div></div>'
    mo.Html(_header_html)
    return


# =============================================================================
# HEADLINE KPIs
# =============================================================================


@app.cell(hide_code=True)
def _(df_trending, eth_dev_set, df_engagement_raw, mo):
    _panel_size = len(eth_dev_set)
    _active_eth = int(df_engagement_raw[df_engagement_raw["username_lower"].isin(eth_dev_set)]["username_lower"].nunique())

    _top_eth = df_trending.sort_values("eth_devs_30d", ascending=False).iloc[0]
    _top_eth_repo = _top_eth["repo_name"].split("/")[-1]
    _top_eth_devs = int(_top_eth["eth_devs_30d"])

    _top_all = df_trending.sort_values("global_engagers_30d", ascending=False).iloc[0]
    _top_all_repo = _top_all["repo_name"].split("/")[-1]
    _top_all_devs = int(_top_all["global_engagers_30d"])

    mo.hstack(
        [
            mo.stat(value=f"{_panel_size:,}", label="Ethereum Builders Tracked", bordered=True, caption="≥12 months commit activity"),
            mo.stat(value=f"{_active_eth}", label="Active on Trending Repos", bordered=True, caption=f"{_active_eth/_panel_size*100:.1f}% of panel"),
            mo.stat(value=_top_eth_repo, label="#1 by Eth Builder Attention", bordered=True, caption=f"{_top_eth_devs} distinct eth builders"),
            mo.stat(value=_top_all_repo, label="#1 by All Builder Attention", bordered=True, caption=f"{_top_all_devs:,} distinct builders"),
        ],
        widths="equal",
        gap=1,
    )
    return


# =============================================================================
# LEADERBOARD
# =============================================================================


@app.cell(hide_code=True)
def _(df_trending, mo):
    import json as _json
    import html as _html_mod

    # Prepare top 100 rows with momentum
    _df = df_trending.sort_values("global_engagers_30d", ascending=False).head(100).reset_index(drop=True)
    _df["rate_7d"] = _df["global_engagers_7d"] / 7
    _df["rate_30d"] = _df["global_engagers_30d"] / 30
    _df["momentum"] = _df["rate_7d"] / _df["rate_30d"].clip(lower=0.01)

    _records = []
    for _i in range(len(_df)):
        _r = _df.iloc[_i]
        _desc = str(_r.get("description", ""))
        if len(_desc) > 72:
            _desc = _desc[:69] + "..."
        _records.append({
            "repo_name": str(_r["repo_name"]),
            "description": _desc,
            "eth_dev_pct": float(_r["eth_dev_pct"]),
            "eth_devs_30d": int(_r["eth_devs_30d"]),
            "eth_devs_7d": int(_r["eth_devs_7d"]),
            "global_engagers_30d": int(_r["global_engagers_30d"]),
            "global_engagers_7d": int(_r["global_engagers_7d"]),
            "momentum": float(_r["momentum"]),
        })

    _data_js = _json.dumps(_records).replace("</", "<\\/")

    _inner = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>'
        '*{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;}'
        'body{margin:0;padding:0;font-size:14px;color:#0f172a;}'
        '.ddp-select{padding:4px 8px;border:1px solid #e2e8f0;border-radius:4px;font-size:0.8125em;color:#0f172a;background:#fff;cursor:pointer;}'
        '.ddp-card{border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.04);}'
        '.ddp-rank-badge{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;font-size:0.75em;}'
        '.ddp-note{font-size:0.8125em;color:#64748b;}'
        'table{width:100%;border-collapse:collapse;}'
        'th{padding:6px 8px;font-size:0.68em;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;white-space:nowrap;}'
        'td{padding:4px 8px;vertical-align:middle;}'
        'a{color:#2563eb;text-decoration:none;}'
        '.controls{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;}'
        '.controls-right{margin-left:auto;display:flex;align-items:center;gap:8px;}'
        '.footer{display:flex;align-items:center;justify-content:space-between;margin-top:6px;}'
        '</style></head><body>'
        '<div class="controls">'
        '<div class="controls-right">'
        '<label style="font-size:0.8125em;color:#64748b;">Sort by</label>'
        '<select id="sortSel" class="ddp-select">'
        '<option value="eth">Eth Builder Attention</option>'
        '<option value="all">All Builder Attention</option>'
        '</select>'
        '<select id="windowSel" class="ddp-select">'
        '<option value="30d">Past 30 Days</option>'
        '<option value="7d">Past 7 Days</option>'
        '</select>'
        '</div></div>'
        '<div id="tableWrap"></div>'
        '<div class="footer">'
        '<span id="footerText" class="ddp-note"></span>'
        '<select id="pageSel" class="ddp-select"></select>'
        '</div>'
        '<script>'
        f'var DATA={_data_js};'
        'var PAGE_SIZE=25;'
        'function fmt(n){if(n>=10000)return(n/1000).toFixed(1)+"K";if(n>=1000)return(n/1000).toFixed(2)+"K";return String(Math.floor(n));}'
        'function heat(m){if(m>=1.5)return"\\ud83c\\udf36\\ufe0f\\ud83c\\udf36\\ufe0f\\ud83c\\udf36\\ufe0f";if(m>=0.7)return"\\ud83c\\udf36\\ufe0f\\ud83c\\udf36\\ufe0f";return"\\ud83c\\udf36\\ufe0f";}'
        'function rankBadge(i){if(i===0)return\'<span class="ddp-rank-badge">\\ud83e\\udd47</span>\';if(i===1)return\'<span class="ddp-rank-badge">\\ud83e\\udd48</span>\';if(i===2)return\'<span class="ddp-rank-badge">\\ud83e\\udd49</span>\';return\'<span class="ddp-rank-badge">#\'+(i+1)+\'</span>\';}'
        'function community(pct){if(pct>=0.01)return\'<span style="display:inline-block;padding:1px 8px;border-radius:10px;background:#ecfdf5;color:#059669;font-weight:600;font-size:0.72em;letter-spacing:0.02em;">Crypto</span>\';return\'<span style="display:inline-block;padding:1px 8px;border-radius:10px;background:#f1f5f9;color:#64748b;font-size:0.72em;letter-spacing:0.02em;">Mainstream</span>\';}'
        'function render(){'
        '  var sortVal=document.getElementById("sortSel").value;'
        '  var winVal=document.getElementById("windowSel").value;'
        '  var is30d=winVal==="30d";'
        '  var allCol=is30d?"global_engagers_30d":"global_engagers_7d";'
        '  var ethCol=is30d?"eth_devs_30d":"eth_devs_7d";'
        '  var sortCol=sortVal==="eth"?ethCol:allCol;'
        '  var sorted=DATA.slice().sort(function(a,b){return b[sortCol]-a[sortCol];});'
        '  var totalPages=Math.max(1,Math.ceil(sorted.length/PAGE_SIZE));'
        '  var pageSel=document.getElementById("pageSel");'
        '  var curPage=parseInt(pageSel.value)||1;'
        '  if(curPage>totalPages)curPage=1;'
        '  pageSel.innerHTML="";'
        '  for(var p=1;p<=totalPages;p++){var o=document.createElement("option");o.value=p;o.textContent="Page "+p;if(p===curPage)o.selected=true;pageSel.appendChild(o);}'
        '  var start=(curPage-1)*PAGE_SIZE;'
        '  var end=Math.min(start+PAGE_SIZE,sorted.length);'
        '  var ethArrow=sortVal==="eth"?" \\u2193":"";'
        '  var allArrow=sortVal==="all"?" \\u2193":"";'
        '  var h=\'<div class="ddp-card"><table style="table-layout:fixed;"><colgroup><col style="width:44px;"><col style="width:26%;"><col style="width:auto;"><col style="width:84px;"><col style="width:84px;"><col style="width:84px;"><col style="width:60px;"></colgroup>\';'
        '  h+=\'<thead><tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">\';'
        '  h+=\'<th style="text-align:center;">#</th>\';'
        '  h+=\'<th style="text-align:left;">Repository</th>\';'
        '  h+=\'<th style="text-align:left;">Description</th>\';'
        '  h+=\'<th style="text-align:center;">Community</th>\';'
        '  h+=\'<th style="text-align:right;">Eth Builders\'+ethArrow+\'</th>\';'
        '  h+=\'<th style="text-align:right;">All Builders\'+allArrow+\'</th>\';'
        '  h+=\'<th style="text-align:center;">Heat</th>\';'
        '  h+=\'</tr></thead><tbody>\';'
        '  for(var i=start;i<end;i++){'
        '    var r=sorted[i];var rank=i;'
        '    var bg=((i-start)%2===1)?"background:#fafbfc;":"";'
        '    h+=\'<tr style="border-bottom:1px solid #f1f5f9;\'+bg+\'">\';'
        '    h+=\'<td style="text-align:center;">\'+rankBadge(rank)+\'</td>\';'
        '    h+=\'<td style="white-space:nowrap;"><a href="https://github.com/\'+r.repo_name+\'" target="_blank" style="font-family:ui-monospace,SFMono-Regular,monospace;font-size:0.82em;">\'+r.repo_name+\'</a></td>\';'
        '    h+=\'<td style="color:#64748b;font-size:0.78em;">\'+r.description+\'</td>\';'
        '    h+=\'<td style="text-align:center;">\'+community(r.eth_dev_pct)+\'</td>\';'
        '    h+=\'<td style="text-align:right;font-size:0.88em;font-variant-numeric:tabular-nums;color:#0f172a;">\'+fmt(r[ethCol])+\'</td>\';'
        '    h+=\'<td style="text-align:right;font-size:0.88em;font-variant-numeric:tabular-nums;color:#0f172a;">\'+fmt(r[allCol])+\'</td>\';'
        '    h+=\'<td style="text-align:center;font-size:0.82em;letter-spacing:-1px;">\'+heat(r.momentum)+\'</td>\';'
        '    h+=\'</tr>\';'
        '  }'
        '  h+=\'</tbody></table></div>\';'
        '  document.getElementById("tableWrap").innerHTML=h;'
        '  document.getElementById("footerText").textContent="Showing "+(start+1)+"\\u2013"+end+" of "+sorted.length+" repos with Ethereum builder signal";'
        '}'
        'document.getElementById("sortSel").addEventListener("change",function(){render();});'
        'document.getElementById("windowSel").addEventListener("change",function(){render();});'
        'document.getElementById("pageSel").addEventListener("change",function(){render();});'
        'render();'
        '</script></body></html>'
    )
    _src = _html_mod.escape(_inner, quote=True)

    mo.vstack([
        mo.md("### Trending Repos"),
        mo.Html(f'<iframe srcdoc="{_src}" class="ddp-chart-frame-tall" scrolling="no" style="height:780px;"></iframe>'),
    ])
    return


# =============================================================================
# QUADRANT MAP (Global Popularity x Eth Dev Concentration)
# =============================================================================


@app.cell(hide_code=True)
def _(df_signal_strength, mo, go, PLOTLY_LAYOUT, np, CATEGORY_COLORS):
    _df = df_signal_strength.dropna(subset=["eth_dev_pct", "total_engagers"]).copy()
    _df = _df[(_df["total_engagers"] >= 10) & (_df["eth_engagers"] >= 1)]
    _df["short_name"] = _df["repo_name"].str.split("/").str[-1]
    _df = _df.sort_values("eth_dev_pct", ascending=False)

    # Cap the view just above the highest "More Crypto" repo (≥4% concentration)
    _crypto_max = _df[_df["eth_dev_pct"] >= 4.0]["eth_dev_pct"].max() if (_df["eth_dev_pct"] >= 4.0).any() else 10.0
    _y_cap = round(_crypto_max + 2.0)
    _outliers = _df[_df["eth_dev_pct"] > _y_cap].copy()
    _df_plot = _df[_df["eth_dev_pct"] <= _y_cap].copy()

    # Bubble size: sqrt-scaled eth dev count, bounded
    _df_plot["_size"] = np.clip(np.sqrt(_df_plot["eth_engagers"]) * 8, 6, 38)

    # Only label repos above 2% — they're the story
    _label_idx = set(_df_plot[_df_plot["eth_dev_pct"] >= 2.0].index)
    # Also label top 3 by total_engagers for mainstream context
    _label_idx.update(_df_plot.nlargest(3, "total_engagers").index)

    # Spectrum color based on eth dev concentration
    def _spectrum_color(pct):
        if pct >= 4.0: return "#10b981"
        elif pct >= 1.0: return "#34d399"
        elif pct >= 0.3: return "#94a3b8"
        else: return "#6366f1"

    _fig = go.Figure()

    # Background: unlabeled dots (below 2% or not top-3 mainstream)
    _sub = _df_plot[~_df_plot.index.isin(_label_idx)]
    if len(_sub) > 0:
        _fig.add_trace(go.Scatter(
            x=_sub["total_engagers"],
            y=_sub["eth_dev_pct"],
            mode="markers",
            showlegend=False,
            marker=dict(
                color=[_spectrum_color(p) for p in _sub["eth_dev_pct"]],
                opacity=0.25, size=_sub["_size"], line=dict(width=0),
            ),
            text=_sub["short_name"],
            customdata=np.stack([_sub["eth_engagers"], _sub["total_engagers"]], axis=-1),
            hovertemplate="<b>%{text}</b><br>%{customdata[0]:.0f} Eth builders / %{customdata[1]:,.0f} total<br>%{y:.1f}% concentration<extra></extra>",
        ))

    # Foreground: labeled dots
    _sub = _df_plot[_df_plot.index.isin(_label_idx)]
    if len(_sub) > 0:
        _fig.add_trace(go.Scatter(
            x=_sub["total_engagers"],
            y=_sub["eth_dev_pct"],
            mode="markers+text",
            showlegend=False,
            marker=dict(
                color=[_spectrum_color(p) for p in _sub["eth_dev_pct"]],
                opacity=0.85, size=_sub["_size"],
                line=dict(width=1.5, color="white"),
            ),
            text=_sub["short_name"],
            textposition="top right",
            textfont=dict(size=10, color="#334155"),
            customdata=np.stack([_sub["eth_engagers"], _sub["total_engagers"]], axis=-1),
            hovertemplate="<b>%{text}</b><br>%{customdata[0]:.0f} Eth builders / %{customdata[1]:,.0f} total<br>%{y:.1f}% concentration<extra></extra>",
        ))

    # Reference line at 1% threshold
    _fig.add_hline(
        y=1.0, line_dash="dot", line_color="#cbd5e1", line_width=1,
        annotation_text="1% — Crypto community threshold",
        annotation_position="top left",
        annotation_font=dict(size=9, color="#94a3b8"),
    )

    # Annotate outliers above the cap as arrows at the top
    for _, _out in _outliers.iterrows():
        _fig.add_annotation(
            x=np.log10(_out["total_engagers"]),
            y=_y_cap - 0.3,
            xref="x", yref="y",
            text=f"<b>{_out['short_name']}</b> ({_out['eth_dev_pct']:.0f}%)",
            showarrow=True, arrowhead=2, arrowsize=0.8, arrowcolor="#10b981",
            ay=-30, ax=0,
            font=dict(size=10, color="#059669"),
            bordercolor="#d1fae5", borderwidth=1, borderpad=3,
            bgcolor="#ecfdf5",
        )

    _fig.update_layout(
        **{
            **PLOTLY_LAYOUT,
            "xaxis": {
                **PLOTLY_LAYOUT["xaxis"],
                "type": "log",
                "title": dict(text="Total builders (log scale)", font=dict(size=11, color="#94a3b8")),
                "showgrid": False,
                "tickvals": [10, 50, 200, 1000, 5000, 20000, 100000],
                "ticktext": ["10", "50", "200", "1K", "5K", "20K", "100K"],
                "tickfont": dict(size=11, color="#64748b"),
            },
            "yaxis": {
                **PLOTLY_LAYOUT["yaxis"],
                "title": dict(text="Eth builder concentration (%)", font=dict(size=11, color="#94a3b8")),
                "showgrid": True,
                "gridcolor": "#f1f5f9",
                "zeroline": False,
                "range": [-0.3, _y_cap + 0.5],
                "dtick": 2,
            },
            "height": 600,
            "showlegend": False,
            "margin": dict(t=40, l=60, r=60, b=90),
        },
    )

    # Spectrum annotations
    _fig.add_annotation(
        x=0.01, y=0.92, xref="paper", yref="paper",
        text="<b>← More Crypto</b>", showarrow=False,
        font=dict(size=11, color="#10b981"), xanchor="left", yanchor="top",
    )
    _fig.add_annotation(
        x=0.99, y=-0.13, xref="paper", yref="paper",
        text="<b>More mainstream →</b>", showarrow=False,
        font=dict(size=11, color="#6366f1"), xanchor="right", yanchor="top",
    )

    _n_crypto = int((_df["eth_dev_pct"] >= 1.0).sum())

    mo.vstack([
        mo.md(f"""### Where Ethereum builders diverge from the mainstream

        Bubble size = Eth builders engaged. Repos above the 1% line have disproportionate Ethereum builder interest — {_n_crypto} repos clear this threshold. Higher and further left = stronger insider signal."""),
        mo.ui.plotly(_fig, config={"displayModeBar": False}),
    ])
    return


# =============================================================================
# SIGNAL STRENGTH BAR CHART (TOP 30)
# =============================================================================


@app.cell(hide_code=True)
def _(df_signal_strength, mo, go, PLOTLY_LAYOUT, np):
    # Top 25 by eth_dev_pct, same criteria as bubble chart (≥10 total, ≥1 eth)
    _df = (
        df_signal_strength
        .dropna(subset=["eth_dev_pct"])
        .query("total_engagers >= 10 and eth_engagers >= 1")
        .nlargest(25, "eth_dev_pct")
        .sort_values("eth_dev_pct", ascending=True)
        .copy()
    )
    _df["short_name"] = _df["repo_name"].str.split("/").str[-1]

    # Color gradient: single green scale by eth_dev_pct intensity
    _max_pct = _df["eth_dev_pct"].max()
    _df["_color"] = _df["eth_dev_pct"].apply(
        lambda p: f"rgba(16,185,129,{0.3 + 0.7 * (p / _max_pct):.2f})"
    )

    # Annotation: absolute eth dev count at bar end
    _fig = go.Figure()
    _fig.add_trace(go.Bar(
        y=_df["short_name"],
        x=_df["eth_dev_pct"],
        orientation="h",
        marker=dict(color=_df["_color"].tolist(), line=dict(width=0)),
        text=_df.apply(lambda r: f"  {r['eth_dev_pct']:.1f}%  ·  {int(r['eth_engagers'])} builders / {int(r['total_engagers']):,}", axis=1),
        textposition="outside",
        textfont=dict(size=10, color="#64748b"),
        customdata=np.stack([_df["repo_name"], _df["eth_engagers"], _df["total_engagers"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} Eth builders / %{customdata[2]:,} total (%{x:.1f}%)<extra></extra>",
        showlegend=False,
    ))

    _fig.update_layout(
        **{
            **PLOTLY_LAYOUT,
            "xaxis": {
                **PLOTLY_LAYOUT["xaxis"],
                "title": "",
                "showticklabels": False,
                "showline": False,
                "showgrid": False,
                "zeroline": False,
            },
            "yaxis": {
                **PLOTLY_LAYOUT["yaxis"],
                "title": "",
                "showgrid": False,
                "zeroline": False,
                "showline": False,
                "tickfont": dict(
                    size=11, color="#334155",
                    family="ui-monospace, SFMono-Regular, monospace",
                ),
            },
            "height": max(400, len(_df) * 24 + 60),
            "margin": dict(t=10, l=150, r=200, b=10),
        },
    )

    mo.vstack([
        mo.md("""### Eth builder concentration

        Repos where Ethereum builders are most over-represented relative to total audience. Minimum 3 Eth builders engaged. A 2–4% concentration is 20–40x above the <0.1% baseline."""),
        mo.ui.plotly(_fig, config={"displayModeBar": False}),
    ])
    return


# =============================================================================
# STARGAZER OVERLAP HEATMAP
# =============================================================================


@app.cell(hide_code=True)
def _(df_overlap_matrix, mo, go, PLOTLY_LAYOUT, np):
    _labels = [l.split("/")[-1] for l in df_overlap_matrix.columns.tolist()]
    _full_labels = df_overlap_matrix.columns.tolist()

    _z = df_overlap_matrix.values.copy().astype(float)
    _diag = np.diag(_z).copy()
    np.fill_diagonal(_z, np.nan)

    # Normalize to Jaccard-like overlap: shared / min(a, b)
    # This prevents huge repos from dominating the color scale
    _n = len(_labels)
    _z_norm = np.full_like(_z, np.nan)
    for _i in range(_n):
        for _j in range(_n):
            if _i == _j:
                continue
            _min_diag = min(_diag[_i], _diag[_j])
            if _min_diag > 0:
                _z_norm[_i][_j] = _z[_i][_j] / _min_diag * 100

    _fig = go.Figure(data=go.Heatmap(
        z=_z_norm,
        x=_labels,
        y=_labels,
        customdata=[[f"{_full_labels[j]} ↔ {_full_labels[i]}" for j in range(_n)] for i in range(_n)],
        # Raw counts for hover
        text=_z,
        colorscale=[
            [0, "#f8fafc"],
            [0.15, "#e0f2fe"],
            [0.35, "#7dd3fc"],
            [0.6, "#2563eb"],
            [1.0, "#1e3a5f"],
        ],
        hoverongaps=False,
        hovertemplate="<b>%{customdata}</b><br>%{text:,.0f} shared engagers (%{z:.0f}% overlap)<extra></extra>",
        colorbar=dict(
            title=dict(text="Overlap %", font=dict(size=11, color="#64748b")),
            tickfont=dict(size=10, color="#94a3b8"),
            thickness=12,
            len=0.6,
        ),
    ))
    _fig.update_layout(
        **{
            **PLOTLY_LAYOUT,
            "xaxis": {
                **PLOTLY_LAYOUT["xaxis"],
                "tickangle": -45,
                "tickformat": None,
                "tickfont": dict(
                    size=10, color="#475569",
                    family="ui-monospace, SFMono-Regular, monospace",
                ),
                "showline": False,
                "side": "bottom",
            },
            "yaxis": {
                **PLOTLY_LAYOUT["yaxis"],
                "showgrid": False, "zeroline": False, "showline": False,
                "tickfont": dict(
                    size=10, color="#475569",
                    family="ui-monospace, SFMono-Regular, monospace",
                ),
                "autorange": "reversed",
            },
            "height": max(500, _n * 26 + 160),
            "margin": dict(t=10, l=130, r=60, b=130),
        },
    )

    mo.vstack([
        mo.md("""### Engager overlap between repos

        How much audience do repos share? Each cell shows the overlap as a percentage of the smaller repo's audience. Dark clusters reveal repos explored by the same builders."""),
        mo.ui.plotly(_fig, config={"displayModeBar": False}),
    ])
    return


# =============================================================================
# CROSSOVER DEVELOPERS
# =============================================================================


@app.cell(hide_code=True)
def _(df_crossover_devs, df_signal_strength, mo):
    _n_crossover = len(df_crossover_devs)
    _n_eth = int(df_crossover_devs["is_eth_dev"].sum())
    _n_outside = _n_crossover - _n_eth

    def _make_table(df_slice, show_repos=True):
        _th_s = "padding:6px 8px;font-size:0.68em;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;white-space:nowrap;"
        _t = df_slice.head(25).copy().reset_index(drop=True)
        _rows = []
        for _i, _r in _t.iterrows():
            _u = _r["username"]
            _n_repos = int(_r["repos_engaged"])
            _repo_list = str(_r.get("repo_list", ""))
            _repos_short = ", ".join(r.split("/")[-1] for r in _repo_list.split(", ")[:5])
            if _r["repos_engaged"] > 5:
                _repos_short += f" +{int(_r['repos_engaged']) - 5} more"
            _row_bg = "background:#fafbfc;" if _i % 2 == 1 else ""

            _rows.append(f"""<tr style="border-bottom:1px solid #f1f5f9;{_row_bg}">
        <td style="padding:4px 8px;vertical-align:middle;"><a href="https://github.com/{_u}" target="_blank" style="color:#2563eb;text-decoration:none;font-family:ui-monospace,SFMono-Regular,monospace;font-size:0.82em;">{_u}</a></td>
        <td style="padding:4px 8px;text-align:center;vertical-align:middle;font-variant-numeric:tabular-nums;font-size:0.88em;color:#0f172a;">{_n_repos}</td>
        <td style="padding:4px 8px;vertical-align:middle;color:#94a3b8;font-size:0.75em;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_repos_short}</td>
            </tr>""")

        return f"""<div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
        <th style="{_th_s}text-align:left;">Builder</th>
        <th style="{_th_s}text-align:center;">Repos</th>
        <th style="{_th_s}text-align:left;">Exploring</th>
        </tr></thead>
        <tbody>{"".join(_rows)}</tbody>
        </table></div>"""

    # Eth scouts: sort by repos_engaged (most active scouts first)
    _eth_df = df_crossover_devs[df_crossover_devs["is_eth_dev"]].sort_values(
        "repos_engaged", ascending=False
    )

    # Adjacent builders: score by alignment with Eth builder interests
    # Weight each repo by its eth_dev_pct from df_signal_strength
    _repo_weights = dict(zip(
        df_signal_strength["repo_name"],
        df_signal_strength["eth_dev_pct"].fillna(0),
    ))
    _outside_df = df_crossover_devs[~df_crossover_devs["is_eth_dev"]].copy()
    _outside_df["alignment_score"] = _outside_df["repo_list"].apply(
        lambda rl: sum(_repo_weights.get(r.strip().lower(), 0) for r in str(rl).split(", "))
    )
    _outside_df = _outside_df.sort_values("alignment_score", ascending=False)

    _eth_html = _make_table(_eth_df)
    _outside_html = _make_table(_outside_df)

    mo.vstack([
        mo.md(f"""### {_n_eth} Ethereum builder scouts and {_n_outside:,} adjacent builders"""),
        mo.hstack([
            mo.vstack([
                mo.md("**Ethereum Builder Scouts**"),
                mo.Html(_eth_html),
            ]),
            mo.vstack([
                mo.md("**High Adjacency Builders**"),
                mo.Html(_outside_html),
            ]),
        ], widths="equal", gap=2),
    ])
    return


# =============================================================================
# TEMPORAL DYNAMICS: STAR VELOCITY COMPARISON
# =============================================================================


@app.cell(hide_code=True)
def _(df_trending, df_engagement_daily, mo):
    import json as _json2
    import html as _html_mod2

    # Build repo options (sorted by popularity)
    _repo_opts = (
        df_trending[df_trending["global_engagers_30d"] > 0]
        .sort_values("global_engagers_30d", ascending=False)["repo_name"]
        .tolist()
    )

    # Default selections
    _preferred = ["zeroclaw-labs/zeroclaw", "nearai/ironclaw", "openclaw/openclaw"]
    _defaults = [r for r in _preferred if r in _repo_opts]

    # Serialize daily engagement data for all top repos
    _daily_subset = df_engagement_daily[df_engagement_daily["repo_name"].isin(_repo_opts)].copy()
    _daily_subset["day_str"] = _daily_subset["day"].dt.strftime("%Y-%m-%d")
    _daily_records = {}
    for _repo in _repo_opts:
        _rd = _daily_subset[_daily_subset["repo_name"] == _repo].sort_values("day")
        if len(_rd) > 0:
            _daily_records[_repo] = {
                "days": _rd["day_str"].tolist(),
                "cum": _rd["cum_engagers"].tolist(),
            }

    _opts_js = _json2.dumps(_repo_opts).replace("</", "<\\/")
    _defaults_js = _json2.dumps(_defaults).replace("</", "<\\/")
    _daily_js = _json2.dumps(_daily_records).replace("</", "<\\/")

    _opt_html = "".join(
        f'<option value="{r}">{r}</option>' for r in _repo_opts
    )

    _inner2 = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></' + 'script>'
        '<style>'
        '*{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;}'
        'body{margin:0;padding:0;font-size:14px;color:#0f172a;}'
        '.ddp-select{padding:4px 8px;border:1px solid #e2e8f0;border-radius:4px;font-size:0.8125em;color:#0f172a;background:#fff;cursor:pointer;}'
        '</style></head><body>'
        '<div style="margin-bottom:8px;">'
        '<label style="font-size:0.8125em;font-weight:600;color:#0f172a;">Compare repos</label><br>'
        '<select id="repoSel" class="ddp-select" multiple size="6" style="width:100%;margin-top:4px;">'
        + _opt_html +
        '</select>'
        '<div style="font-size:0.75em;color:#94a3b8;margin-top:2px;">Select up to 6 repos (Cmd/Ctrl+click)</div>'
        '</div>'
        '<div id="chart" style="width:100%;"></div>'
        '<script>'
        f'var DAILY={_daily_js};'
        f'var DEFAULTS={_defaults_js};'
        'var COLORS=["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4"];'
        'var sel=document.getElementById("repoSel");'
        # Set defaults
        'for(var i=0;i<sel.options.length;i++){if(DEFAULTS.indexOf(sel.options[i].value)>=0)sel.options[i].selected=true;}'
        'function render(){'
        '  var chosen=[];for(var i=0;i<sel.options.length;i++){if(sel.options[i].selected)chosen.push(sel.options[i].value);}'
        '  if(chosen.length>6)chosen=chosen.slice(0,6);'
        '  if(chosen.length===0){document.getElementById("chart").innerHTML="<p style=\\"color:#94a3b8;font-size:0.875em;\\">Select repos above to compare growth curves.</p>";return;}'
        '  var traces=[];'
        '  for(var i=0;i<chosen.length;i++){'
        '    var repo=chosen[i].toLowerCase();'
        '    var d=DAILY[repo];if(!d)continue;'
        '    var short_name=repo.split("/").pop();'
        '    var c=COLORS[i%COLORS.length];'
        '    var cr=parseInt(c.slice(1,3),16),cg=parseInt(c.slice(3,5),16),cb=parseInt(c.slice(5,7),16);'
        '    traces.push({x:d.days,y:d.cum,name:short_name,mode:"lines",line:{color:c,width:2,shape:"hvh"},fill:"tozeroy",fillcolor:"rgba("+cr+","+cg+","+cb+",0.05)",hovertemplate:"%{y:,.0f} builders<extra>"+short_name+"</extra>"});'
        '  }'
        '  var layout={font:{size:12,color:"#0f172a"},plot_bgcolor:"white",paper_bgcolor:"white",margin:{t:40,l:70,r:40,b:50},height:450,hovermode:"x unified",'
        '    legend:{orientation:"h",yanchor:"bottom",y:1.04,xanchor:"left",x:0,bgcolor:"rgba(255,255,255,0.8)",font:{size:11,color:"#475569"}},'
        '    xaxis:{showgrid:false,tickformat:"%b %d",linecolor:"#cbd5e1",linewidth:1,ticks:"outside",tickcolor:"#cbd5e1",tickfont:{color:"#64748b",size:11}},'
        '    yaxis:{showgrid:true,gridcolor:"#f1f5f9",zeroline:true,zerolinecolor:"#e2e8f0",zerolinewidth:1,linecolor:"#cbd5e1",linewidth:1,ticks:"outside",tickcolor:"#cbd5e1",tickfont:{color:"#64748b",size:11},tickformat:","}};'
        '  Plotly.react("chart",traces,layout,{responsive:true});'
        '}'
        'sel.addEventListener("change",render);'
        'render();'
        '</script></body></html>'
    )
    _src2 = _html_mod2.escape(_inner2, quote=True)

    mo.vstack([
        mo.md("""### Cumulative builder engagement

        Each line counts unique builders who starred or forked (first event only). A steep ramp means viral discovery; a flattening curve means the moment has passed."""),
        mo.Html(f'<iframe srcdoc="{_src2}" class="ddp-chart-frame-tall" scrolling="no"></iframe>'),
    ])
    return


# =============================================================================
# METHODOLOGY
# =============================================================================


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "Metrics & Definitions": mo.md("""
        **Ethereum builder panel**: Qualified builders with ≥12 months commit activity on Ethereum panel repos and verified GitHub logins. ~920 infrastructure, ~415 DeFi.

        **Engagement metrics**: Stars + forks collected over 30-day and 7-day rolling windows. Stargazer/forker usernames are scraped directly from the GitHub API and deduplicated within each window.

        **Signal strength (eth_dev_pct)**: For each repo, the share of engagers who are Ethereum panel builders. A high percentage means the repo is drawing disproportionate attention from active Ethereum developers relative to the mainstream GitHub audience.

        **Momentum**: 7-day daily engagement rate divided by 30-day daily engagement rate. A ratio above 1.0 means the repo is accelerating; below 1.0 means interest is cooling.
        """),
        "Assumptions & Limitations": mo.md("""
        **Starring ≠ using.** A star is a lightweight signal of interest, not adoption or production use.

        **Non-random sample.** The repos were selected *because* they attracted Ethereum builder attention — this is not a representative cross-section of all open source software.

        **Panel is a ceiling, not a floor.** The Ethereum builder panel captures the most active slice of Ethereum developers. Many builders fall below the activity threshold and are not counted.

        **Attention is ephemeral.** Engagement patterns shift quickly. A repo trending today may drop out of the rankings next month as the community's focus moves on.
        """),
        "Data Sources": mo.md("""
        **OSO data warehouse** — `ethereum.local_rank_models` (repo rankings and signal strength), `ethereum.dev_engagement_models` (per-repo engagement counts and panel overlap)

        **GitHub API** — GraphQL + REST endpoints used to collect stargazer and forker usernames for each tracked repo over rolling windows.
        """),
    })
    return


# =============================================================================
# DATA: DEVELOPER PANEL (from local_rank_models pipeline)
# =============================================================================


@app.cell
def _(mo, pyoso_db_conn):
    with mo.persistent_cache("panel_devs_v5"):
        df_panel_devs = mo.sql(
            """
            SELECT
              panel_name,
              github_username AS username
            FROM ethereum.local_rank_models.panel_developers
            """,
            engine=pyoso_db_conn,
            output=False,
        )
    return (df_panel_devs,)


# =============================================================================
# DATA: ENGAGEMENT (from dev_engagement_models pipeline)
# =============================================================================


@app.cell
def _(mo, pd, pyoso_db_conn):
    with mo.persistent_cache("engagement_unified_v1"):
        df_engagement_raw = mo.sql(
            """
            SELECT
              repo,
              repo_lower,
              username,
              username_lower,
              event_ts AS ts
            FROM ethereum.dev_engagement_models.engagement_unified
            """,
            engine=pyoso_db_conn,
            output=False,
        )
        df_engagement_raw["ts"] = pd.to_datetime(df_engagement_raw["ts"])
    return (df_engagement_raw,)


@app.cell
def _(mo, pyoso_db_conn):
    with mo.persistent_cache("repo_engagement_v1"):
        df_repo_engagement = mo.sql(
            """
            SELECT
              repo,
              repo_lower,
              global_engagers_30d,
              global_engagers_7d,
              eth_devs_30d,
              eth_devs_7d,
              eth_dev_pct,
              momentum
            FROM ethereum.dev_engagement_models.eth_dev_repo_engagement
            """,
            engine=pyoso_db_conn,
            output=False,
        )
    return (df_repo_engagement,)


@app.cell
def _(mo, pyoso_db_conn):
    with mo.persistent_cache("crossover_devs_v1"):
        df_crossover_devs = mo.sql(
            """
            SELECT
              username,
              username_lower,
              repos_engaged,
              repo_list,
              is_eth_dev
            FROM ethereum.dev_engagement_models.crossover_developers
            """,
            engine=pyoso_db_conn,
            output=False,
        )
    return (df_crossover_devs,)


# =============================================================================
# PANEL FILTER → df_trending, eth_dev_set
# =============================================================================


@app.cell
def _(df_repo_engagement, df_engagement_raw, eth_dev_set, pd, REPO_CATEGORIES, REPO_DESCRIPTIONS):
    df_trending = df_repo_engagement.copy()
    df_trending.rename(columns={"repo_lower": "repo_name"}, inplace=True)
    # Only keep repos in active metadata (filters out excluded/removed repos)
    _active_lower = {k.lower() for k in REPO_CATEGORIES.keys()}
    df_trending = df_trending[df_trending["repo_name"].isin(_active_lower)].copy()

    # Recompute eth dev counts from raw CSV data (more reliable than UDM precomputed)
    _now = pd.Timestamp.now()
    _raw = df_engagement_raw.copy()
    _raw["_is_eth"] = _raw["username_lower"].isin(eth_dev_set)
    _eth_only = _raw[_raw["_is_eth"]]

    _eth_30d = (
        _eth_only[_eth_only["ts"] >= _now - pd.Timedelta(days=30)]
        .groupby("repo_lower")["username_lower"].nunique()
        .rename("eth_devs_30d_csv")
    )
    _eth_7d = (
        _eth_only[_eth_only["ts"] >= _now - pd.Timedelta(days=7)]
        .groupby("repo_lower")["username_lower"].nunique()
        .rename("eth_devs_7d_csv")
    )

    # Replace UDM eth dev counts with CSV-derived counts
    df_trending = df_trending.drop(columns=["eth_devs_30d", "eth_devs_7d"], errors="ignore")
    df_trending = df_trending.merge(_eth_30d, left_on="repo_name", right_index=True, how="left")
    df_trending = df_trending.merge(_eth_7d, left_on="repo_name", right_index=True, how="left")
    df_trending["eth_devs_30d"] = df_trending["eth_devs_30d_csv"].fillna(0).astype(int)
    df_trending["eth_devs_7d"] = df_trending["eth_devs_7d_csv"].fillna(0).astype(int)
    df_trending.drop(columns=["eth_devs_30d_csv", "eth_devs_7d_csv"], inplace=True)

    # Recompute eth_dev_pct from CSV counts
    df_trending["eth_dev_pct"] = (
        df_trending["eth_devs_30d"] / df_trending["global_engagers_30d"].clip(lower=1)
    )

    _cat_lower = {k.lower(): v for k, v in REPO_CATEGORIES.items()}
    df_trending["category"] = df_trending["repo_name"].map(
        lambda r: _cat_lower.get(r, "Dev Tools") if r else "Dev Tools"
    )
    _desc_lower = {k.lower(): v for k, v in REPO_DESCRIPTIONS.items()}
    df_trending["description"] = df_trending["repo_name"].map(
        lambda r: _desc_lower.get(r, "") if r else ""
    )

    # Only keep repos with at least 1 eth dev engagement (star/fork)
    df_trending = df_trending[df_trending["eth_devs_30d"] > 0].copy()
    return (df_trending,)


@app.cell
def _(df_panel_devs):
    eth_dev_set = set(df_panel_devs["username"].str.lower().tolist())
    return (eth_dev_set,)


# =============================================================================
# DERIVED: SIGNAL STRENGTH
# =============================================================================


@app.cell
def _(df_trending):
    df_signal_strength = df_trending.copy()
    df_signal_strength.rename(columns={
        "global_engagers_30d": "total_engagers",
        "eth_devs_30d": "eth_engagers",
    }, inplace=True)
    df_signal_strength["eth_dev_pct"] = df_signal_strength["eth_dev_pct"] * 100
    return (df_signal_strength,)


# =============================================================================
# DERIVED: STARGAZER OVERLAP MATRIX
# =============================================================================


@app.cell
def _(df_engagement_raw, df_trending, np, pd, REPO_CATEGORIES):
    _eth_repos = [k.lower() for k, v in REPO_CATEGORIES.items() if v == "Ethereum & Crypto"]
    _eth_in_data = df_trending[df_trending["repo_name"].isin(_eth_repos)].sort_values("eth_devs_30d", ascending=False).head(12)["repo_name"].tolist()
    _other_top = df_trending[~df_trending["repo_name"].isin(_eth_repos)].sort_values("eth_devs_30d", ascending=False).head(13)["repo_name"].tolist()
    _top_repos = list(dict.fromkeys(_eth_in_data + _other_top))[:25]

    _df = df_engagement_raw[df_engagement_raw["repo_lower"].isin(_top_repos)][["repo_lower", "username_lower"]].drop_duplicates()

    _user_repos = _df.groupby("username_lower")["repo_lower"].apply(set).to_dict()

    _repos = sorted(_top_repos)
    _n = len(_repos)
    _matrix = np.zeros((_n, _n), dtype=int)
    _repo_idx = {r: i for i, r in enumerate(_repos)}

    for _user, _user_repo_set in _user_repos.items():
        _relevant = [_repo_idx[r] for r in _user_repo_set if r in _repo_idx]
        for _a in range(len(_relevant)):
            for _b in range(_a + 1, len(_relevant)):
                _matrix[_relevant[_a]][_relevant[_b]] += 1
                _matrix[_relevant[_b]][_relevant[_a]] += 1

    for _r in _repos:
        _i = _repo_idx[_r]
        _matrix[_i][_i] = _df[_df["repo_lower"] == _r]["username_lower"].nunique()

    _labels = _repos
    df_overlap_matrix = pd.DataFrame(_matrix, index=_labels, columns=_labels)
    return (df_overlap_matrix,)


# =============================================================================
# DERIVED: DAILY CUMULATIVE ENGAGEMENT VELOCITY
# =============================================================================


@app.cell
def _(df_engagement_raw):
    _df = df_engagement_raw.copy()
    _df["day"] = _df["ts"].dt.floor("D")

    _daily = (
        _df
        .groupby(["repo_lower", "day"], as_index=False)
        .agg(engagers=("username", "nunique"))
        .sort_values(["repo_lower", "day"])
    )
    _daily["cum_engagers"] = _daily.groupby("repo_lower")["engagers"].cumsum()
    _daily.rename(columns={"repo_lower": "repo_name"}, inplace=True)
    df_engagement_daily = _daily
    return (df_engagement_daily,)


# =============================================================================
# CONFIGURATION
# =============================================================================


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, pd):
    CATEGORY_COLORS = {
        "AI & Agents": "#6366f1",
        "Ethereum & Crypto": "#10b981",
        "Dev Tools": "#94a3b8",
    }

    _df_meta = mo.sql(
        """
        SELECT repo, description, category, first_seen, removed
        FROM ethereum.dev_engagement_events.repo_metadata
        WHERE repo NOT IN ('lambdaclass/dedaliano', 'ruvnet/wifi-densepose', 'lambdaclass/stabileo')
        """,
        engine=pyoso_db_conn,
        output=False,
    )

    REPO_CATEGORIES = dict(zip(_df_meta["repo"], _df_meta["category"]))
    REPO_DESCRIPTIONS = dict(zip(_df_meta["repo"], _df_meta["description"].fillna("")))
    return CATEGORY_COLORS, REPO_CATEGORIES, REPO_DESCRIPTIONS


@app.cell(hide_code=True)
def _():
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#0f172a"),
        margin=dict(t=20, l=60, r=20, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            bgcolor="rgba(255,255,255,0.8)",
            font=dict(size=11, color="#475569"),
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#cbd5e1", linewidth=1,
            ticks="outside", tickcolor="#cbd5e1",
            tickfont=dict(color="#64748b", size=11),
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#f1f5f9",
            zeroline=True, zerolinecolor="#e2e8f0", zerolinewidth=1,
            linecolor="#cbd5e1", linewidth=1,
            ticks="outside", tickcolor="#cbd5e1",
            tickfont=dict(color="#64748b", size=11),
        ),
    )
    return (PLOTLY_LAYOUT,)


# =============================================================================
# BOILERPLATE
# =============================================================================


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, np, pd, px


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