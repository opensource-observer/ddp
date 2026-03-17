import marimo

__generated_with = "unknown"
app = marimo.App(width="full", css_file="../styles/insights.css")


@app.cell(hide_code=True)
def header_title(mo):
    mo.md(r"""
    # DeFi Builder Journeys
    <small>Owner: <span class="ddp-badge">OSO Team</span> · Last Updated: <span class="ddp-badge">2026-03-16</span></small>
    """)
    return


@app.cell(hide_code=True)
def define_static_plotly(mo):
    def static_plotly(figure):
        figure.update_layout(width=1100)
        return mo.ui.plotly(figure=figure, config={'displayModeBar': False})
    return (static_plotly,)


@app.cell(hide_code=True)
def build_highlighted_tables(ECO_COLORS, OTHER_CRYPTO_COLOR, df_protocol_table, mo):
    # Build per-ecosystem highlighted protocol tables for embedding in CSS tabs
    _df = df_protocol_table.copy().reset_index(drop=True)
    _df['top_chain'] = _df['top_chain'].fillna('').str.replace('_', ' ').str.title()

    def _fmt_tvl(v):
        if v >= 1e9:
            return f'${v / 1e9:.1f}B'
        if v >= 1e6:
            return f'${v / 1e6:.0f}M'
        return f'${v / 1e3:.0f}K'

    _display = _df.rename(columns={
        'tvl_rank': 'Rank',
        'project_display_name': 'Project',
        'ecosystem_category': 'Category',
        'current_tvl': 'Total TVL',
        'ethereum_pct': 'ETH TVL Share (%)',
        'top_chain': 'Top Chain',
        'total_repos': 'Repos',
        'qualifying_developers': 'Qualifying Builders',
    })[['Rank', 'Project', 'Category', 'Total TVL', 'ETH TVL Share (%)', 'Top Chain', 'Repos', 'Qualifying Builders']]
    _display['Rank'] = _display['Rank'].astype(int)
    _display['ETH TVL Share (%)'] = _display['ETH TVL Share (%)'].apply(lambda v: f'{v:.0f}')
    _display['Total TVL'] = _display['Total TVL'].apply(_fmt_tvl)

    _table_styles = [
        {'selector': 'th', 'props': [
            ('font-size', '0.8em'), ('color', '#64748B'),
            ('padding', '6px 12px'), ('border-bottom', '2px solid #E2E8F0'),
            ('text-align', 'left'),
        ]},
        {'selector': 'td', 'props': [('border-bottom', '1px solid #F1F5F9')]},
        {'selector': 'table', 'props': [('width', '100%'), ('max-width', '1100px'), ('border-collapse', 'collapse')]},
    ]

    def _make_table(highlight_cat=None):
        def _highlight_rows(row):
            if highlight_cat and row['Category'] == highlight_cat:
                _color = ECO_COLORS.get(highlight_cat, OTHER_CRYPTO_COLOR)
                return [f'background-color: {_color}18'] * len(row)
            return [''] * len(row)
        return (
            _display.style
            .apply(_highlight_rows, axis=1)
            .set_properties(**{'font-size': '0.85em', 'padding': '5px 12px'})
            .set_table_styles(_table_styles)
            .hide(axis='index')
        )

    protocol_table_ethereum = mo.as_html(_make_table('Ethereum')).text
    protocol_table_solana = mo.as_html(_make_table('Solana')).text
    protocol_table_other = mo.as_html(_make_table('Other')).text
    return (protocol_table_ethereum, protocol_table_other, protocol_table_solana)


@app.cell(hide_code=True)
def query_defi_projects(mo, pyoso_db_conn):
    # Load top DeFi projects (40 selected) — TVL, chain share, and developer metrics
    with mo.persistent_cache("df_defi_projects"):
        df_defi_projects = mo.sql(
            """
            SELECT
                project_id,
                project_name,
                project_display_name,
                current_tvl,
                logo,
                defillama_urls,
                ethereum_tvl,
                other_tvl,
                chain_total_tvl,
                ethereum_pct,
                top_chain,
                total_repos,
                qualifying_developers
            FROM ethereum.devpanels.mart_defi_project_summary
            ORDER BY current_tvl DESC NULLS LAST
            """,
            engine=pyoso_db_conn,
            output=False
        )
    return (df_defi_projects,)


@app.cell(hide_code=True)
def query_tvl_history(mo, pyoso_db_conn):
    # Monthly TVL time series for top DeFi protocols (2020+)
    with mo.persistent_cache("df_tvl_history"):
        df_tvl_history = mo.sql(
            """
            SELECT
              project_name,
              project_display_name,
              sample_date,
              tvl,
              current_tvl
            FROM ethereum.devpanels.mart_project_tvl_history
            ORDER BY current_tvl DESC, sample_date
            """,
            engine=pyoso_db_conn,
            output=False
        )
    return (df_tvl_history,)


@app.cell(hide_code=True)
def query_top_devs(mo, pyoso_db_conn):
    # Load top developers per project
    with mo.persistent_cache("df_top_devs"):
        df_top_devs = mo.sql(
            """
            SELECT
                t.project_id,
                t.project_display_name,
                t.canonical_developer_id,
                t.dev_rank,
                t.total_active_days,
                t.first_commit_date,
                t.last_commit_date
            FROM ethereum.devpanels.mart_top_devs_by_project AS t
            JOIN ethereum.devpanels.dim_projects_by_collection AS p
                ON t.project_id = p.project_id
            WHERE p.collection_name = 'defillama-top-50-protocols'
            """,
            engine=pyoso_db_conn,
            output=False
        )
    return (df_top_devs,)


@app.cell(hide_code=True)
def query_alignment(mo, pd, pyoso_db_conn):
    # Load five-track alignment data per developer-month
    # SCOPED to only developers in our DeFi project set
    with mo.persistent_cache("df_alignment"):
        df_alignment = mo.sql(
            """
            SELECT
                a.canonical_developer_id,
                a.actor_login,
                a.month,
                a.home_project_repo_event_days,
                a.home_project_events,
                a.home_project_primary_ecosystem,
                a.home_project_name,
                a.crypto_repo_event_days,
                a.crypto_events,
                a.crypto_primary_ecosystem,
                a.crypto_primary_project,
                a.personal_repo_event_days,
                a.personal_events,
                a.personal_primary_ecosystem,
                a.oss_repo_event_days,
                a.oss_events,
                a.oss_primary_ecosystem,
                a.oss_primary_project,
                a.interest_repo_event_days,
                a.interest_events,
                a.total_repo_event_days,
                a.has_home_project_activity,
                a.has_crypto_activity,
                a.has_personal_activity,
                a.has_oss_activity,
                a.has_interest_activity
            FROM ethereum.devpanels.mart_developer_alignment_monthly AS a
            JOIN ethereum.devpanels.mart_top_devs_by_project AS dpb
              ON a.canonical_developer_id = dpb.canonical_developer_id
            JOIN ethereum.devpanels.dim_projects_by_collection AS pbc
              ON dpb.project_id = pbc.project_id
            WHERE pbc.collection_name = 'defillama-top-50-protocols'
            ORDER BY a.canonical_developer_id, a.month
            """,
            engine=pyoso_db_conn,
            output=False
        )
        df_alignment['month'] = pd.to_datetime(df_alignment['month'])
    return (df_alignment,)


@app.cell(hide_code=True)
def query_interest_projects(mo, pd, pyoso_db_conn):
    # Interest (Watch/Fork events) project names + ecosystem for feeder analysis
    with mo.persistent_cache("df_interest_projects"):
        df_interest_projects = mo.sql(
            """
            SELECT
                a.canonical_developer_id,
                a.month,
                COALESCE(
                    a.project_display_name,
                    a.nearest_eco,
                    SPLIT_PART(a.repo_name, '/', 1)
                ) AS interest_project,
                BOOL_OR(COALESCE(a.is_crypto, FALSE)) AS is_crypto,
                MAX(a.farthest_eco) AS farthest_eco,
                SUM(a.count_days) AS interest_days,
                SUM(a.count_events) AS interest_events
            FROM ethereum.devpanels.fact_top_dev_activity_monthly_enriched AS a
            JOIN ethereum.devpanels.mart_top_devs_by_project AS dpb
              ON a.canonical_developer_id = dpb.canonical_developer_id
            JOIN ethereum.devpanels.dim_projects_by_collection AS pbc
              ON dpb.project_id = pbc.project_id
            WHERE pbc.collection_name = 'defillama-top-50-protocols'
              AND a.event_type IN ('WatchEvent', 'ForkEvent')
            GROUP BY 1, 2, 3
            ORDER BY 1, 2
            """,
            engine=pyoso_db_conn,
            output=False
        )
        df_interest_projects['month'] = pd.to_datetime(df_interest_projects['month'])
    return (df_interest_projects,)


@app.cell(hide_code=True)
def query_activity(mo, pd, pyoso_db_conn):
    # Load detailed activity data (monthly active devs per project)
    with mo.persistent_cache("df_activity"):
        df_activity = mo.sql(
            """
            SELECT
                p.project_display_name,
                t.month,
                t.canonical_developer_id,
                t.actor_login,
                t.event_type,
                t.count_days,
                t.count_events,
                t.farthest_eco,
                t.is_home_project
            FROM ethereum.devpanels.fact_top_dev_activity_monthly_enriched AS t
            JOIN ethereum.devpanels.dim_projects_by_collection AS p
              ON t.project_id = p.project_id
            WHERE p.collection_name = 'defillama-top-50-protocols'
              AND t.event_type IN ('PushEvent', 'PullRequestEvent', 'PullRequestReviewEvent')
            """,
            engine=pyoso_db_conn,
            output=False
        )
        df_activity['month'] = pd.to_datetime(df_activity['month'])
    return (df_activity,)


@app.cell(hide_code=True)
def transform_protocol_table(df_projects_with_eco):
    # Prepare per-project stats for protocol summary table
    # Columns sourced from mart_defi_project_summary via df_projects_with_eco
    _projects = df_projects_with_eco[
        ['project_display_name', 'current_tvl', 'ecosystem_category', 'tvl_rank',
         'ethereum_pct', 'top_chain', 'total_repos', 'qualifying_developers']
    ].copy()
    _projects['ethereum_pct'] = _projects['ethereum_pct'].fillna(0)
    _projects['total_repos'] = _projects['total_repos'].fillna(0).astype(int)
    _projects['qualifying_developers'] = _projects['qualifying_developers'].fillna(0).astype(int)
    _projects = _projects.sort_values('tvl_rank')
    df_protocol_table = _projects
    return (df_protocol_table,)


@app.cell(hide_code=True)
def transform_project_ecosystem_classification(
    PROJECT_ECOSYSTEM,
    df_defi_projects,
    pd,
):
    # Classify projects as Ethereum vs Other using manual mapping
    df_projects_with_eco = df_defi_projects.copy()

    # Apply manual ecosystem mapping (using display names)
    df_projects_with_eco['ecosystem_category'] = df_projects_with_eco['project_display_name'].map(PROJECT_ECOSYSTEM)
    # Default unmapped projects to 'Other'
    df_projects_with_eco['ecosystem_category'] = df_projects_with_eco['ecosystem_category'].fillna('Other')
    # Add TVL rank
    df_projects_with_eco['tvl_rank'] = range(1, len(df_projects_with_eco) + 1)

    return (df_projects_with_eco,)


@app.cell(hide_code=True)
def transform_monthly_active_devs(df_activity, df_projects_with_eco, pd):
    # Calculate monthly active developers per project
    # Filter to home project activity only
    _home_activity = df_activity[df_activity['is_home_project'] == True].copy()

    # Ensure month is datetime and filter to 2020+ (DeFi Summer onwards)
    _home_activity['month'] = pd.to_datetime(_home_activity['month'], errors='coerce')
    _home_activity = _home_activity[_home_activity['month'].notna()]
    _home_activity = _home_activity[_home_activity['month'] >= '2020-01-01']

    # Count unique developers per project per month
    df_monthly_devs = (
        _home_activity
        .groupby(['project_display_name', 'month'])['canonical_developer_id']
        .nunique()
        .reset_index()
        .rename(columns={'canonical_developer_id': 'monthly_active_devs'})
    )

    # Merge with project metadata
    df_monthly_devs = df_monthly_devs.merge(
        df_projects_with_eco[['project_display_name', 'tvl_rank', 'ecosystem_category', 'current_tvl']],
        on='project_display_name',
        how='left'
    )

    # Create month string for display (sorted chronologically)
    df_monthly_devs['month_str'] = df_monthly_devs['month'].dt.strftime('%Y-%m')
    return (df_monthly_devs,)


@app.cell(hide_code=True)
def transform_qualified_developers(df_alignment, df_top_devs):
    # Filter to developers with 12+ months on home project
    # Count months with home project activity per developer
    _home_months = (
        df_alignment[df_alignment['has_home_project_activity'] == True]
        .groupby('canonical_developer_id')
        .size()
        .reset_index(name='home_project_months')
    )

    # Filter to 12+ months
    _qualified_ids = _home_months[_home_months['home_project_months'] >= 12]['canonical_developer_id']

    # Get qualified developers with their metadata
    df_qualified_developers = df_top_devs[
        df_top_devs['canonical_developer_id'].isin(_qualified_ids)
    ].merge(_home_months, on='canonical_developer_id')

    return (df_qualified_developers,)


@app.cell(hide_code=True)
def transform_developer_lifecycle(df_alignment, df_qualified_developers):
    # Define onboarding and offboarding periods per (developer, project)
    # Onboarding = first month with home project activity
    # Offboarding = last activity 6+ months before end of timeseries

    _qualified_ids = df_qualified_developers['canonical_developer_id'].unique()

    # Filter alignment to qualified developers only
    _dev_activity = df_alignment[
        df_alignment['canonical_developer_id'].isin(_qualified_ids)
    ].copy().sort_values(['canonical_developer_id', 'month'])

    # Forward-fill home_project_name so inactive months inherit the last active project
    _dev_activity['home_project_name'] = _dev_activity.groupby('canonical_developer_id')['home_project_name'].ffill()

    # Calculate onboarding month per (developer, project) - first month with activity
    _onboard = (
        _dev_activity[_dev_activity['has_home_project_activity'] == True]
        .groupby(['canonical_developer_id', 'home_project_name'])
        .nth(0)  # 0-indexed, so 0 = 1st month
        .reset_index()[['canonical_developer_id', 'home_project_name', 'month']]
        .rename(columns={'month': 'onboard_month', 'home_project_name': 'project_display_name'})
    )

    # Calculate offboarding per (developer, project) - only look AFTER onboard date
    _dev_activity = _dev_activity.merge(
        _onboard,
        left_on=['canonical_developer_id', 'home_project_name'],
        right_on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )
    _post_onboard = _dev_activity[_dev_activity['month'] >= _dev_activity['onboard_month']].copy()

    # Find each developer's last active month on home project
    _last_active = (
        _post_onboard[_post_onboard['has_home_project_activity'] == True]
        .groupby(['canonical_developer_id', 'home_project_name'])['month']
        .max()
        .reset_index()
        .rename(columns={'month': 'last_active_month', 'home_project_name': 'project_display_name'})
    )

    # Offboard if last activity was 6+ months before end of timeseries
    _latest_month = df_alignment['month'].max()
    _last_active['months_since_active'] = (
        (_latest_month - _last_active['last_active_month']).dt.days // 30
    )
    _offboard = _last_active[_last_active['months_since_active'] >= 6][
        ['canonical_developer_id', 'project_display_name', 'last_active_month']
    ].rename(columns={'last_active_month': 'offboard_month'})

    # Combine into lifecycle dataframe - join on (developer, project)
    df_developer_lifecycle = df_qualified_developers.merge(
        _onboard, on=['canonical_developer_id', 'project_display_name'], how='left'
    ).merge(
        _offboard, on=['canonical_developer_id', 'project_display_name'], how='left'
    )

    # Calculate tenure (vectorized)
    _latest_month = df_alignment['month'].max()
    _end_month = df_developer_lifecycle['offboard_month'].fillna(_latest_month)
    df_developer_lifecycle['tenure_months'] = (
        (_end_month - df_developer_lifecycle['onboard_month']).dt.days // 30
    )

    df_developer_lifecycle['is_still_active'] = df_developer_lifecycle['offboard_month'].isna()
    return (df_developer_lifecycle,)


@app.cell(hide_code=True)
def transform_onboarding_features(df_alignment, df_developer_lifecycle):
    # Engineer features for pre-onboarding period clustering
    # Look at what developers were doing BEFORE they onboarded to their DeFi project

    # Get onboard dates per (developer, project)
    _onboard_dates = df_developer_lifecycle[['canonical_developer_id', 'project_display_name', 'onboard_month']].dropna()

    # Merge onboard dates into alignment data - join only on developer ID
    # This keeps ALL activity for each developer, not just rows with matching home_project_name
    _activity = df_alignment.merge(
        _onboard_dates,
        on='canonical_developer_id',
        how='inner'
    )

    # Filter to pre-onboarding months only (all activity before first home project contribution)
    _pre_onboard = _activity[_activity['month'] < _activity['onboard_month']].copy()

    # Filter to only months with actual activity (total_repo_event_days > 0)
    # The alignment table has rows for all months, but many have zero activity
    _pre_active = _pre_onboard[_pre_onboard['total_repo_event_days'] > 0]

    # Aggregate pre-onboarding activity per (developer, project)
    _pre_features = _pre_active.groupby(['canonical_developer_id', 'project_display_name']).agg(
        pre_total_days=('total_repo_event_days', 'sum'),
        pre_crypto_days=('crypto_repo_event_days', 'sum'),
        pre_personal_days=('personal_repo_event_days', 'sum'),
        pre_oss_days=('oss_repo_event_days', 'sum'),
        pre_interest_days=('interest_repo_event_days', 'sum'),
        pre_months_active=('month', 'nunique'),  # Now only counts months with activity
        pre_crypto_events=('crypto_events', 'sum'),
        pre_personal_events=('personal_events', 'sum'),
        pre_oss_events=('oss_events', 'sum'),
    ).reset_index()

    # Calculate percentages (of total pre-onboarding activity)
    _pre_features['pre_crypto_pct'] = (
        _pre_features['pre_crypto_days'] / _pre_features['pre_total_days'].replace(0, 1) * 100
    )
    _pre_features['pre_personal_pct'] = (
        _pre_features['pre_personal_days'] / _pre_features['pre_total_days'].replace(0, 1) * 100
    )
    _pre_features['pre_oss_pct'] = (
        _pre_features['pre_oss_days'] / _pre_features['pre_total_days'].replace(0, 1) * 100
    )

    # Find primary pre-onboarding ecosystem (by months, then days as tiebreaker)
    _primary_eco = (
        _pre_active[_pre_active['crypto_primary_ecosystem'].notna()]
        .groupby(['canonical_developer_id', 'project_display_name', 'crypto_primary_ecosystem'])
        .agg(eco_months=('month', 'nunique'), eco_days=('crypto_repo_event_days', 'sum'))
        .reset_index()
        .sort_values(['eco_months', 'eco_days'], ascending=[False, False])
        .drop_duplicates(['canonical_developer_id', 'project_display_name'], keep='first')
        [['canonical_developer_id', 'project_display_name', 'crypto_primary_ecosystem']]
        .rename(columns={'crypto_primary_ecosystem': 'pre_primary_ecosystem'})
    )
    _pre_features = _pre_features.merge(_primary_eco, on=['canonical_developer_id', 'project_display_name'], how='left')

    # Merge back to lifecycle dataframe
    df_onboarding_features = df_developer_lifecycle.merge(
        _pre_features,
        on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )

    # Fill NaN for developers with no pre-onboarding activity
    df_onboarding_features['pre_total_days'] = df_onboarding_features['pre_total_days'].fillna(0)
    df_onboarding_features['pre_months_active'] = df_onboarding_features['pre_months_active'].fillna(0)
    # Direct to DeFi: less than 6 months of activity before joining home project
    df_onboarding_features['is_direct_to_defi'] = df_onboarding_features['pre_months_active'] < 6
    return (df_onboarding_features,)


@app.cell(hide_code=True)
def transform_onboarding_clusters(df_onboarding_features):
    # Classify developers by onboarding background: Newcomer vs Experienced
    # Newcomer = < 6 months of pre-onboarding activity ("came in cold")
    # Experienced = 6+ months of pre-onboarding activity (crypto, OSS, or personal)

    _df = df_onboarding_features.copy()

    _df['onboarding_cluster_id'] = _df['is_direct_to_defi'].map({True: 0, False: 1})
    _df['onboarding_cluster'] = _df['is_direct_to_defi'].map({True: 'Newcomer', False: 'Experienced'})

    df_with_clusters = _df

    return (df_with_clusters,)


@app.cell(hide_code=True)
def transform_contribution_features(df_alignment, df_with_clusters):
    # Engineer features for contribution clustering
    # Look at how developers contributed DURING their time on the home project

    # Get lifecycle info per (developer, project)
    _lifecycle = df_with_clusters[['canonical_developer_id', 'project_display_name', 'onboard_month', 'offboard_month', 'tenure_months']].copy()

    # Merge with alignment data
    _activity = df_alignment.merge(
        _lifecycle,
        left_on=['canonical_developer_id', 'home_project_name'],
        right_on=['canonical_developer_id', 'project_display_name'],
        how='inner'
    )

    # Filter to post-onboarding activity only
    _post_onboard = _activity[_activity['month'] >= _activity['onboard_month']].copy()

    # For offboarded devs, also filter to before offboard
    _post_onboard = _post_onboard[
        (_post_onboard['offboard_month'].isna()) |
        (_post_onboard['month'] <= _post_onboard['offboard_month'])
    ]

    # Filter to months with home project activity
    _home_active = _post_onboard[_post_onboard['has_home_project_activity'] == True]

    # Aggregate contribution features per (developer, project)
    _contrib_features = _home_active.groupby(['canonical_developer_id', 'project_display_name']).agg(
        contrib_months=('month', 'nunique'),
        contrib_total_days=('home_project_repo_event_days', 'sum'),
        contrib_total_events=('home_project_events', 'sum'),
    ).reset_index()

    # Calculate derived features
    _contrib_features['avg_days_per_month'] = (
        _contrib_features['contrib_total_days'] / _contrib_features['contrib_months'].replace(0, 1)
    )

    # Merge tenure from lifecycle
    _contrib_features = _contrib_features.merge(
        _lifecycle[['canonical_developer_id', 'project_display_name', 'tenure_months']],
        on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )

    # Consistency: what % of tenure months had activity
    _contrib_features['consistency'] = (
        _contrib_features['contrib_months'] / _contrib_features['tenure_months'].replace(0, 1) * 100
    )

    # Merge back to df_with_clusters
    df_contribution_features = df_with_clusters.merge(
        _contrib_features[['canonical_developer_id', 'project_display_name', 'contrib_months',
                          'contrib_total_days', 'avg_days_per_month', 'consistency']],
        on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )

    # Fill NaN (shouldn't happen, but safety)
    df_contribution_features['contrib_months'] = df_contribution_features['contrib_months'].fillna(0)
    df_contribution_features['contrib_total_days'] = df_contribution_features['contrib_total_days'].fillna(0)
    df_contribution_features['avg_days_per_month'] = df_contribution_features['avg_days_per_month'].fillna(0)
    df_contribution_features['consistency'] = df_contribution_features['consistency'].fillna(0)

    # Classify contribution intensity
    def _classify_intensity(avg_days):
        if avg_days > 10:
            return 'Frequent Contributor'
        elif avg_days >= 5:
            return 'Regular Contributor'
        return 'Occasional Contributor'

    df_contribution_features['contribution_cluster'] = df_contribution_features['avg_days_per_month'].apply(_classify_intensity)
    return (df_contribution_features,)


@app.cell(hide_code=True)
def transform_current_status(df_alignment, df_contribution_features, pd):
    # Classify current developer status
    # "Current" = activity in the last 6 months of the timeseries

    _latest_month = df_alignment['month'].max()
    _cutoff_month = _latest_month - pd.DateOffset(months=6)

    # Get recent activity (last 6 months) for each developer
    _recent = df_alignment[df_alignment['month'] >= _cutoff_month].copy()

    # Aggregate recent activity by developer
    _recent_summary = _recent.groupby('canonical_developer_id').agg(
        recent_home_days=('home_project_repo_event_days', 'sum'),
        recent_crypto_days=('crypto_repo_event_days', 'sum'),
        recent_personal_days=('personal_repo_event_days', 'sum'),
        recent_oss_days=('oss_repo_event_days', 'sum'),
        recent_total_days=('total_repo_event_days', 'sum'),
    ).reset_index()

    # Classify current status
    def _classify_status(row):
        if row['recent_home_days'] > 0:
            return 'Still Active on Home Project'
        elif row['recent_crypto_days'] > 0:
            return 'Active Elsewhere in Crypto'
        elif row['recent_personal_days'] > 0 or row['recent_oss_days'] > 0:
            return 'Active in Non-Crypto'
        else:
            return 'Inactive'

    _recent_summary['current_status'] = _recent_summary.apply(_classify_status, axis=1)

    # Merge with contribution features
    df_with_status = df_contribution_features.merge(
        _recent_summary[['canonical_developer_id', 'current_status',
                        'recent_home_days', 'recent_crypto_days',
                        'recent_personal_days', 'recent_oss_days']],
        on='canonical_developer_id',
        how='left'
    )

    # Fill NaN (developers with no recent activity at all)
    df_with_status['current_status'] = df_with_status['current_status'].fillna('Inactive')

    # Calculate stats
    _total = len(df_with_status)
    _status_counts = df_with_status['current_status'].value_counts()

    current_status_stats = {
        'total_developers': _total,
        'still_active': _status_counts.get('Still Active on Home Project', 0),
        'active_crypto': _status_counts.get('Active Elsewhere in Crypto', 0),
        'active_non_crypto': _status_counts.get('Active in Non-Crypto', 0),
        'inactive': _status_counts.get('Inactive', 0),
        'cutoff_month': _cutoff_month.strftime('%Y-%m'),
        'latest_month': _latest_month.strftime('%Y-%m')
    }
    current_status_stats['pct_still_active'] = (
        current_status_stats['still_active'] / _total * 100 if _total > 0 else 0
    )
    current_status_stats['pct_left_crypto'] = (
        (current_status_stats['active_non_crypto'] + current_status_stats['inactive'])
        / _total * 100 if _total > 0 else 0
    )
    return (df_with_status,)


@app.cell(hide_code=True)
def transform_temporal_status(
    PROJECT_ECOSYSTEM,
    df_alignment,
    df_developer_lifecycle,
    pd,
):
    # Compute cohort retention for both ecosystems
    _eco_map = df_developer_lifecycle['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')

    def _compute_cohort(lifecycle_df):
        _qualified_ids = lifecycle_df['canonical_developer_id'].unique()
        _alignment = df_alignment[df_alignment['canonical_developer_id'].isin(_qualified_ids)].copy()
        _alignment['quarter'] = _alignment['month'].dt.to_period('Q')

        _quarterly = _alignment.groupby(['canonical_developer_id', 'quarter']).agg(
            home_days=('home_project_repo_event_days', 'sum'),
            crypto_days=('crypto_repo_event_days', 'sum'),
            personal_days=('personal_repo_event_days', 'sum'),
            oss_days=('oss_repo_event_days', 'sum'),
        ).reset_index()

        def _classify(row):
            if row['home_days'] > 0: return 'Active on Home Project'
            elif row['crypto_days'] > 0: return 'Active Elsewhere in Crypto'
            elif row['personal_days'] > 0 or row['oss_days'] > 0: return 'Active in Non-Crypto'
            return 'Inactive'

        _quarterly['status'] = _quarterly.apply(_classify, axis=1)

        # Anchor cohorts to first quarter of HOME PROJECT activity (not overall onboard)
        # so retention starts at 100% and decays — never climbs
        _first_home = _quarterly[_quarterly['status'] == 'Active on Home Project'].groupby('canonical_developer_id')['quarter'].min().reset_index()
        _first_home.columns = ['canonical_developer_id', 'onboard_quarter']
        _dev_onboard = _first_home.copy()
        _dev_onboard['onboard_year'] = _dev_onboard['onboard_quarter'].apply(lambda p: p.year)

        _all_quarters = pd.DataFrame({'quarter': sorted(_quarterly['quarter'].unique())})
        _full_grid = _dev_onboard[['canonical_developer_id', 'onboard_quarter', 'onboard_year']].merge(_all_quarters, how='cross')
        _full_grid = _full_grid[_full_grid['quarter'] >= _full_grid['onboard_quarter']]
        _full_grid = _full_grid.merge(_quarterly[['canonical_developer_id', 'quarter', 'status']], on=['canonical_developer_id', 'quarter'], how='left')
        _full_grid['status'] = _full_grid['status'].fillna('Inactive')

        def _p2i(s):
            return s.apply(lambda p: p.year * 4 + p.quarter - 1)

        _full_grid['quarters_since'] = _p2i(_full_grid['quarter']) - _p2i(_full_grid['onboard_quarter'])
        _full_grid['is_home_active'] = _full_grid['status'] == 'Active on Home Project'

        _agg = _full_grid.groupby(['onboard_year', 'quarters_since']).agg(
            active=('is_home_active', 'sum'), observable=('canonical_developer_id', 'count'),
        ).reset_index()
        _cohort_sizes = _agg[_agg['quarters_since'] == 0][['onboard_year', 'observable']].rename(columns={'observable': 'cohort_size'})
        _agg = _agg.merge(_cohort_sizes, on='onboard_year')
        _agg['pct_active'] = _agg['active'] / _agg['cohort_size'] * 100
        _agg['observability'] = _agg['observable'] / _agg['cohort_size']
        return _agg[(_agg['observability'] >= 0.8) & (_agg['onboard_year'].between(2020, 2024))].copy()

    cohort_retention_by_eco = {
        'Ethereum': _compute_cohort(df_developer_lifecycle[_eco_map == 'Ethereum']),
        'Solana': _compute_cohort(df_developer_lifecycle[_eco_map == 'Solana']),
        'Other': _compute_cohort(df_developer_lifecycle[~_eco_map.isin(['Ethereum', 'Solana'])]),
    }
    return (cohort_retention_by_eco,)


@app.cell(hide_code=True)
def transform_alluvial_data(
    PROJECT_ECOSYSTEM,
    df_alignment,
    df_developer_lifecycle,
    df_with_status,
    pd,
):
    # Build yearly state classification for each developer (2020-2025)
    # Computes for all three ecosystems, returns dicts keyed by ecosystem

    _DISPLAY_NAMES = {
        'Sky (prev. MakerDAO)': 'Sky/Maker',
        'Wormhole Foundation': 'Wormhole',
        'Spark Foundation': 'Spark',
        'Offchain Labs': 'Arbitrum',
        'Steakhouse Financial': 'Steakhouse',
        'Aerodrome Finance': 'Aerodrome',
        'Convex Finance': 'Convex',
        'Euler Finance': 'Euler',
        'Renzo Protocol': 'Renzo',
        'Jupiter Exchange': 'Jupiter',
        'Kamino Finance': 'Kamino',
        'Polygon zkEVM': 'Polygon zk',
        'Falcon Finance': 'Falcon',
        'Bedrock Technology': 'Bedrock',
        'Tornado Cash': 'Tornado',
        'BlackRock BUIDL': 'BlackRock',
        'Solv Protocol': 'Solv',
        'Kelp': 'Kelp DAO',
    }
    _YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

    def _compute_one(selected, is_eth):
        if not selected:
            return None, {'empty': True}

        _pool = df_developer_lifecycle[
            df_developer_lifecycle['project_display_name'].isin(selected)
        ].copy()
        _pool_ids = _pool['canonical_developer_id'].unique()

        _onboard = _pool[['canonical_developer_id', 'onboard_month']].dropna(subset=['onboard_month']).copy()
        _onboard['onboard_year'] = _onboard['onboard_month'].dt.year
        _dev_onboard = _onboard.groupby('canonical_developer_id')['onboard_year'].min().reset_index()

        _dev_bg = (
            df_with_status[df_with_status['canonical_developer_id'].isin(_pool_ids)]
            .drop_duplicates('canonical_developer_id')
            [['canonical_developer_id', 'is_direct_to_defi', 'pre_primary_ecosystem']]
        )

        _align = df_alignment[df_alignment['canonical_developer_id'].isin(_pool_ids)].copy()
        _align['year'] = _align['month'].dt.year
        _align = _align[_align['year'].between(2020, 2025)]

        _yearly_totals = (
            _align.groupby(['canonical_developer_id', 'year'])
            .agg(
                home_days=('home_project_repo_event_days', 'sum'),
                crypto_days=('crypto_repo_event_days', 'sum'),
                oss_days=('oss_repo_event_days', 'sum'),
                personal_days=('personal_repo_event_days', 'sum'),
            )
            .reset_index()
        )

        _home_activity = _align[_align['has_home_project_activity'] == True].copy()
        _home_by_year = (
            _home_activity.groupby(['canonical_developer_id', 'year', 'home_project_name'])
            .agg(days=('home_project_repo_event_days', 'sum'))
            .reset_index()
            .sort_values('days', ascending=False)
            .drop_duplicates(['canonical_developer_id', 'year'], keep='first')
            .rename(columns={'home_project_name': 'primary_project'})
            [['canonical_developer_id', 'year', 'primary_project']]
        )

        _crypto_eco = (
            _align[_align['crypto_repo_event_days'] > 0]
            .groupby(['canonical_developer_id', 'year', 'crypto_primary_ecosystem'])
            .agg(days=('crypto_repo_event_days', 'sum'))
            .reset_index()
            .sort_values('days', ascending=False)
            .drop_duplicates(['canonical_developer_id', 'year'], keep='first')
            .rename(columns={'crypto_primary_ecosystem': 'crypto_ecosystem'})
            [['canonical_developer_id', 'year', 'crypto_ecosystem']]
        )

        _dev_ids = pd.DataFrame({'canonical_developer_id': _pool_ids})
        _years_df = pd.DataFrame({'year': _YEARS})
        _grid = _dev_ids.merge(_years_df, how='cross')
        _grid = _grid.merge(_dev_onboard, on='canonical_developer_id', how='left')
        _grid = _grid.merge(_dev_bg, on='canonical_developer_id', how='left')
        _grid = _grid.merge(_yearly_totals, on=['canonical_developer_id', 'year'], how='left')
        _grid = _grid.merge(_home_by_year, on=['canonical_developer_id', 'year'], how='left')
        _grid = _grid.merge(_crypto_eco, on=['canonical_developer_id', 'year'], how='left')
        for col in ['home_days', 'crypto_days', 'oss_days', 'personal_days']:
            _grid[col] = _grid[col].fillna(0)

        def _classify(row):
            if pd.notna(row['onboard_year']) and row['year'] < row['onboard_year']:
                if pd.notna(row['pre_primary_ecosystem']) and row['pre_primary_ecosystem'] == 'Ethereum':
                    return 'Ethereum projects'
                if pd.notna(row['pre_primary_ecosystem']):
                    return 'Other crypto'
                if not row['is_direct_to_defi']:
                    return 'Non-crypto OSS'
                return 'Inactive'
            if row['home_days'] > 0 and pd.notna(row['primary_project']):
                _proj = row['primary_project']
                _short = _DISPLAY_NAMES.get(_proj, _proj)
                if _proj in selected:
                    return _short
                _eco = PROJECT_ECOSYSTEM.get(_proj, 'Other')
                return 'Ethereum projects' if _eco == 'Ethereum' else 'Other crypto'
            if row['crypto_days'] > 0:
                return 'Ethereum projects' if row.get('crypto_ecosystem') == 'Ethereum' else 'Other crypto'
            if row['oss_days'] > 0 or row['personal_days'] > 0:
                return 'Non-crypto OSS'
            if pd.isna(row['onboard_year']):
                if pd.notna(row['pre_primary_ecosystem']) and row['pre_primary_ecosystem'] == 'Ethereum':
                    return 'Ethereum projects'
                if pd.notna(row['pre_primary_ecosystem']):
                    return 'Other crypto'
                if not row['is_direct_to_defi']:
                    return 'Non-crypto OSS'
                return 'Inactive'
            return 'Inactive'

        _grid['display_state'] = _grid.apply(_classify, axis=1)

        _project_states = set()
        for _p in selected:
            _project_states.add(_DISPLAY_NAMES.get(_p, _p))

        _node_counts = _grid.groupby(['year', 'display_state']).size().reset_index(name='count')

        def _state_sort_key(state):
            if state == 'Inactive':
                return (0, 0, '')
            if state == 'Non-crypto OSS':
                return (1, 0, '')
            if is_eth and state == 'Other crypto':
                return (2, 0, '')
            if not is_eth and state == 'Ethereum projects':
                return (2, 0, '')
            if is_eth and state == 'Ethereum projects':
                return (3, 0, '')
            if not is_eth and state == 'Other crypto':
                return (3, 0, '')
            if state in _project_states:
                return (4, 0, state)
            return (5, 0, state)

        _nodes_by_year = {}
        for _yr in _YEARS:
            _yr_nodes = _node_counts[_node_counts['year'] == _yr].copy()
            _yr_nodes['sort_key'] = _yr_nodes['display_state'].apply(_state_sort_key)
            _yr_nodes = _yr_nodes.sort_values('sort_key').reset_index(drop=True)
            _nodes_by_year[_yr] = _yr_nodes[['display_state', 'count']].to_dict('records')

        _links = []
        for _i in range(len(_YEARS) - 1):
            _yr_a, _yr_b = _YEARS[_i], _YEARS[_i + 1]
            _left = _grid[_grid['year'] == _yr_a][['canonical_developer_id', 'display_state']].rename(
                columns={'display_state': 'source_state'})
            _right = _grid[_grid['year'] == _yr_b][['canonical_developer_id', 'display_state']].rename(
                columns={'display_state': 'target_state'})
            _transitions = _left.merge(_right, on='canonical_developer_id')
            _link_counts = _transitions.groupby(['source_state', 'target_state']).size().reset_index(name='count')
            for _, _row in _link_counts.iterrows():
                _links.append({
                    'source_year': _yr_a, 'target_year': _yr_b,
                    'source_state': _row['source_state'], 'target_state': _row['target_state'],
                    'count': _row['count'],
                })

        data = {
            'nodes_by_year': _nodes_by_year, 'links': _links, 'years': _YEARS,
            'project_states': _project_states, '_selected_projects': selected,
            '_display_names': _DISPLAY_NAMES, '_project_ecosystem': PROJECT_ECOSYSTEM,
        }
        stats = {'empty': False, 'total_devs': len(_pool_ids), 'n_projects': len(selected)}
        return data, stats

    # Use all projects for each ecosystem (no interactive filter)
    _all_projects = sorted(df_with_status['project_display_name'].unique())
    _eth_selected = set(p for p in _all_projects if PROJECT_ECOSYSTEM.get(p) == 'Ethereum')
    _solana_selected = set(p for p in _all_projects if PROJECT_ECOSYSTEM.get(p) == 'Solana')
    _other_selected = set(p for p in _all_projects if PROJECT_ECOSYSTEM.get(p) not in ('Ethereum', 'Solana'))

    _eth_data, _eth_stats = _compute_one(_eth_selected, True)
    _solana_data, _solana_stats = _compute_one(_solana_selected, False)
    _other_data, _other_stats = _compute_one(_other_selected, False)

    alluvial_data_by_eco = {'Ethereum': _eth_data, 'Solana': _solana_data, 'Other': _other_data}
    alluvial_stats_by_eco = {'Ethereum': _eth_stats, 'Solana': _solana_stats, 'Other': _other_stats}
    return alluvial_data_by_eco, alluvial_stats_by_eco


@app.cell(hide_code=True)
def transform_balance_of_trade(
    PROJECT_ECOSYSTEM,
    df_alignment,
    df_with_status,
    pd,
):
    # Yearly ecosystem snapshots → year-over-year Ethereum DeFi imports/exports
    _qualified_ids = df_with_status['canonical_developer_id'].unique()
    _align = df_alignment[df_alignment['canonical_developer_id'].isin(_qualified_ids)]
    # Only use fully complete calendar years (12 months) to avoid partial-year artifacts
    _month_counts = _align.groupby(_align['month'].dt.year)['month'].apply(lambda x: x.dt.month.nunique())
    _complete_years = sorted(_month_counts[_month_counts >= 12].index)
    # Focus on 2019+ (so flow chart starts at 2020)
    _years = [y for y in _complete_years if y >= 2019]

    def _classify_year(year_data):
        """Classify each developer's primary ecosystem for a given year's data."""
        _dev = year_data.groupby('canonical_developer_id').agg(
            home_days=('home_project_repo_event_days', 'sum'),
            crypto_days=('crypto_repo_event_days', 'sum'),
            oss_days=('oss_repo_event_days', 'sum'),
            personal_days=('personal_repo_event_days', 'sum'),
        ).reset_index()
        # Primary home project
        _home = (
            year_data[year_data['home_project_repo_event_days'] > 0]
            .groupby(['canonical_developer_id', 'home_project_name'])
            .agg(_m=('month', 'nunique'), _d=('home_project_repo_event_days', 'sum'))
            .reset_index().sort_values(['_m', '_d'], ascending=False)
            .drop_duplicates('canonical_developer_id', keep='first')
        )
        _dev = _dev.merge(_home[['canonical_developer_id', 'home_project_name']], on='canonical_developer_id', how='left')
        _dev['_heco'] = _dev['home_project_name'].map(PROJECT_ECOSYSTEM)
        # Primary crypto ecosystem
        _crypto = (
            year_data[year_data['crypto_repo_event_days'] > 0]
            .groupby(['canonical_developer_id', 'crypto_primary_ecosystem'])
            .agg(_m=('month', 'nunique'), _d=('crypto_repo_event_days', 'sum'))
            .reset_index().sort_values(['_m', '_d'], ascending=False)
            .drop_duplicates('canonical_developer_id', keep='first')
        )
        _dev = _dev.merge(_crypto[['canonical_developer_id', 'crypto_primary_ecosystem']], on='canonical_developer_id', how='left')

        def _classify(row):
            if row['home_days'] > 0 and pd.notna(row.get('_heco')):
                if row['_heco'] == 'Ethereum': return 'Ethereum'
                if row['_heco'] == 'Solana': return 'Solana'
                return 'Other Crypto'
            if row['crypto_days'] > 0:
                eco = row.get('crypto_primary_ecosystem')
                if pd.notna(eco) and eco == 'Ethereum':
                    return 'Ethereum'
                if pd.notna(eco) and eco == 'Solana':
                    return 'Solana'
                if pd.notna(eco):
                    return 'Other Crypto'
            if row['oss_days'] > 0 or row['personal_days'] > 0:
                return 'Non-Crypto OSS'
            return 'Inactive'

        _dev['eco'] = _dev.apply(_classify, axis=1)
        # Include all qualified devs (no activity in this year = Inactive)
        _all = pd.DataFrame({'canonical_developer_id': _qualified_ids})
        _dev = _all.merge(_dev[['canonical_developer_id', 'eco']], on='canonical_developer_id', how='left')
        _dev['eco'] = _dev['eco'].fillna('Inactive')
        return _dev.set_index('canonical_developer_id')['eco']

    # Build yearly ecosystem classifications
    _yearly_eco = {_y: _classify_year(_align[_align['month'].dt.year == _y]) for _y in _years}

    # Year-over-year flows for each focal ecosystem
    _FOCALS = ['Ethereum', 'Solana', 'Other Crypto']
    _records = []
    for _focal in _FOCALS:
        for _i in range(len(_years) - 1):
            _y1, _y2 = _years[_i], _years[_i + 1]
            _comp = pd.DataFrame({'before': _yearly_eco[_y1], 'after': _yearly_eco[_y2]})
            _imp = _comp[(_comp['before'] != _focal) & (_comp['after'] == _focal)]
            for _src, _cnt in _imp.groupby('before').size().items():
                _records.append({'focal': _focal, 'year': _y2, 'direction': 'import', 'partner': _src, 'count': int(_cnt)})
            _exp = _comp[(_comp['before'] == _focal) & (_comp['after'] != _focal)]
            for _dst, _cnt in _exp.groupby('after').size().items():
                _records.append({'focal': _focal, 'year': _y2, 'direction': 'export', 'partner': _dst, 'count': int(_cnt)})

    df_balance_flows = pd.DataFrame(_records)

    balance_stats = {}
    for _focal in _FOCALS:
        _before = int((_yearly_eco[_years[0]] == _focal).sum())
        _after = int((_yearly_eco[_years[-1]] == _focal).sum())
        balance_stats[_focal] = {
            'total_devs': len(_qualified_ids),
            'count_before': _before,
            'count_after': _after,
            'net': _after - _before,
            'first_year': _years[0],
            'last_year': _years[-1],
        }
    return balance_stats, df_balance_flows


@app.cell(hide_code=True)
def transform_non_eth_origins(PROJECT_ECOSYSTEM, df_contribution_features):
    # Bidirectional talent flow: Ethereum ↔ Other ecosystems
    _df = df_contribution_features.copy()
    _df['home_ecosystem'] = _df['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')

    # Export: Ethereum-trained devs now working on non-Ethereum projects
    _non_eth_devs = _df[_df['home_ecosystem'] != 'Ethereum']
    _eth_exports = _non_eth_devs[_non_eth_devs['pre_primary_ecosystem'].fillna('') == 'Ethereum']
    _export_count = _eth_exports['canonical_developer_id'].nunique()

    # Import: Non-Ethereum-trained devs now working on Ethereum projects
    _eth_devs = _df[_df['home_ecosystem'] == 'Ethereum']
    _non_eth_imports = _eth_devs[
        (_eth_devs['pre_primary_ecosystem'].notna()) &
        (_eth_devs['pre_primary_ecosystem'] != 'Ethereum')
    ]
    _import_count = _non_eth_imports['canonical_developer_id'].nunique()

    # Temporal pattern: imports by year
    _non_eth_imports_by_year = (
        _non_eth_imports.copy()
        .assign(onboard_year=lambda x: x['onboard_month'].dt.year)
        .groupby('onboard_year')
        .agg(imports=('canonical_developer_id', 'nunique'))
        .reset_index()
    )

    non_eth_stats = {
        'export_count': _export_count,
        'import_count': _import_count,
        'net_flow': _import_count - _export_count,
        'total_non_eth_devs': _non_eth_devs['canonical_developer_id'].nunique(),
        'total_eth_devs': _eth_devs['canonical_developer_id'].nunique(),
        'imports_by_year': _non_eth_imports_by_year,
    }
    return (non_eth_stats,)


@app.cell(hide_code=True)
def transform_feeder_projects(
    PROJECT_ECOSYSTEM,
    df_alignment,
    df_contribution_features,
    df_interest_projects,
    pd,
):
    # Feeder projects: 2x2 grid (home ecosystem × engagement) with crypto/OSS lists
    # Dedup: contributed wins over starred for the same (dev, project)
    # Category: from contribution track when available, interest track as fallback

    # --- NAME NORMALIZATION ---
    # Merge duplicate project names to canonical forms
    _NAME_MAP = {
        # Ecosystem categories → cleaner labels
        'ethereum w/o l2s': 'Ethereum Core',
        'ethereum dev tools': 'Ethereum Dev Tools',
        # Babylon variants
        'babylonchain': 'Babylon',
        'babylon chain': 'Babylon',
        'babylonchain-io': 'Babylon',
        # Uniswap variants
        'uniswap': 'Uniswap',
        # Aave variants
        'aave': 'Aave',
        # Cosmos variants
        'cosmos': 'Cosmos',
        'cosmos network': 'Cosmos',
        # Solana variants → unified
        'solana labs': 'Solana',
        'solana foundation': 'Solana',
        'solana developers': 'Solana',
        'solana': 'Solana',
        # Maker variants
        'maker': 'Sky (prev. MakerDAO)',
        # Compound variants
        'compound-developers': 'Compound',
        'compounddev': 'Compound',
        # Curve variants
        'curve-labs': 'Curve',
        'curveresearch': 'Curve',
        # Truffle variants
        'trufflesuite': 'Truffle',
        # Polkadot variants
        '@polkadot{.js}': 'Polkadot',
        'polkadot network': 'Polkadot',
        'polkadot-io': 'Polkadot',
        # Near variants
        'near-one': 'NEAR',
        'near': 'NEAR',
        # Facebook
        'facebook open source': 'Meta OSS',
        # Rust variants → unified
        'the rust programming language': 'Rust',
        'rust crypto': 'Rust',
        # Ethereum misc
        'ethereum miscellenia': 'Ethereum Core',
        'ethereum miscellaneous': 'Ethereum Core',
        'ethereum core': 'Ethereum Core',
        # Keep Network
        'keep-network': 'Keep Network',
        # Meta Research
        'meta research': 'Meta OSS',
        # sporkdao → cleaner name
        'sporkdaoofficial': 'SporkDAO',
    }

    # --- CLASSIFICATION OVERRIDES ---
    # Projects misclassified by the is_crypto heuristic
    _FORCE_CRYPTO = {
        'solana labs', 'solana', 'delvtech', 'polygon', 'trustwallet', 'cosmostation',
        'babylonchain', 'babylon chain', 'babylon', 'near', 'near-one',
        'avalanche', 'bnb chain', 'polkadot network', '@polkadot{.js}',
        'polkadot-io', 'cosmos', 'cosmos network', 'keep network', 'keep-network',
    }
    _FORCE_OSS = {
        'rust', 'the rust programming language', 'rust crypto', 'deno',
        'microsoft', 'google', 'vercel', 'openai', 'meta oss',
        'facebook open source', 'oven-sh',
    }

    # --- PROJECTS TO EXCLUDE ---
    # Not interpretable as feeders (org names, not projects)
    _EXCLUDE = {
        'ethereum-lists',  # just a list repo, not a project
    }

    def _normalize(name):
        """Normalize a project name via canonical name mapping."""
        key = name.strip().lower()
        if key in _EXCLUDE:
            return None
        return _NAME_MAP.get(key, name)


    _lifecycle = df_contribution_features[
        ['canonical_developer_id', 'project_display_name', 'onboard_month']
    ].drop_duplicates(subset='canonical_developer_id', keep='first')

    # Developer home ecosystem: Ethereum DeFi vs Solana DeFi vs Other DeFi
    def _map_eco(p):
        _e = PROJECT_ECOSYSTEM.get(p, 'Other')
        if _e == 'Ethereum': return 'Ethereum DeFi'
        if _e == 'Solana': return 'Solana DeFi'
        return 'Other DeFi'
    _lifecycle['home_ecosystem'] = _lifecycle['project_display_name'].map(_map_eco)

    # --- CONTRIBUTION FEEDERS ---
    _pre = df_alignment.merge(
        _lifecycle[['canonical_developer_id', 'onboard_month', 'home_ecosystem']],
        on='canonical_developer_id', how='inner',
    )
    _pre = _pre[_pre['month'] < _pre['onboard_month']]

    # Crypto contributions
    _crypto = _pre[
        _pre['crypto_primary_project'].notna() & (_pre['crypto_repo_event_days'] > 0)
    ][['canonical_developer_id', 'crypto_primary_project', 'crypto_repo_event_days', 'home_ecosystem']].copy()
    _crypto['feeder_type'] = 'Crypto'
    _crypto = _crypto.rename(columns={
        'canonical_developer_id': 'dev_id', 'crypto_primary_project': 'project',
        'crypto_repo_event_days': 'days',
    })[['dev_id', 'project', 'days', 'feeder_type', 'home_ecosystem']]

    # OSS contributions
    _oss = _pre[
        _pre['oss_primary_project'].notna() & (_pre['oss_repo_event_days'] > 0)
    ][['canonical_developer_id', 'oss_primary_project', 'oss_repo_event_days', 'home_ecosystem']].copy()
    _oss['feeder_type'] = 'OSS'
    _oss = _oss.rename(columns={
        'canonical_developer_id': 'dev_id', 'oss_primary_project': 'project',
        'oss_repo_event_days': 'days',
    })[['dev_id', 'project', 'days', 'feeder_type', 'home_ecosystem']]

    _contrib = pd.concat([_crypto, _oss], ignore_index=True)
    _contrib['engagement'] = 'Contributing'

    # Apply normalization and classification overrides
    _contrib['project'] = _contrib['project'].apply(_normalize)
    _contrib = _contrib[_contrib['project'].notna()]  # drop excluded
    _contrib['project_key'] = _contrib['project'].str.lower().str.strip()
    _force_crypto_mask = _contrib['project_key'].isin(_FORCE_CRYPTO)
    _force_oss_mask = _contrib['project_key'].isin(_FORCE_OSS)
    _contrib.loc[_force_crypto_mask, 'feeder_type'] = 'Crypto'
    _contrib.loc[_force_oss_mask, 'feeder_type'] = 'OSS'

    # --- INTEREST FEEDERS (Watch events, pre-onboard) ---
    _interest_pre = df_interest_projects.merge(
        _lifecycle[['canonical_developer_id', 'onboard_month', 'home_ecosystem']],
        on='canonical_developer_id', how='inner',
    )
    _interest_pre = _interest_pre[_interest_pre['month'] < _interest_pre['onboard_month']]

    _int = _interest_pre[['canonical_developer_id', 'interest_project', 'interest_days', 'is_crypto', 'home_ecosystem']].copy()
    _int['feeder_type'] = _int['is_crypto'].map({True: 'Crypto', False: 'OSS'})
    _int = _int.rename(columns={
        'canonical_developer_id': 'dev_id', 'interest_project': 'project', 'interest_days': 'days',
    })[['dev_id', 'project', 'days', 'feeder_type', 'home_ecosystem']]
    _int['engagement'] = 'Starred / Forked'

    # Apply normalization and classification overrides
    _int['project'] = _int['project'].apply(_normalize)
    _int = _int[_int['project'].notna()]  # drop excluded
    _int['project_key'] = _int['project'].str.lower().str.strip()
    _force_crypto_mask = _int['project_key'].isin(_FORCE_CRYPTO)
    _force_oss_mask = _int['project_key'].isin(_FORCE_OSS)
    _int.loc[_force_crypto_mask, 'feeder_type'] = 'Crypto'
    _int.loc[_force_oss_mask, 'feeder_type'] = 'OSS'

    # --- DEDUP: contributed wins over starred per (dev, project) ---
    _int_deduped = _int.merge(
        _contrib[['dev_id', 'project_key']].drop_duplicates(),
        on=['dev_id', 'project_key'], how='left', indicator=True,
    )
    _int_deduped = _int_deduped[_int_deduped['_merge'] == 'left_only'].drop(columns=['_merge'])

    _all = pd.concat([_contrib, _int_deduped], ignore_index=True)

    # Exclude home project from feeder lists (a project shouldn't feed itself)
    _home_keys = _lifecycle.set_index('canonical_developer_id')['project_display_name'].str.lower().str.strip()
    _all['_home_key'] = _all['dev_id'].map(_home_keys)
    _all = _all[_all['project_key'] != _all['_home_key']].drop(columns=['_home_key'])

    # Display name: most common casing per project_key (post-normalization)
    _display = _all.groupby('project_key')['project'].agg(lambda x: x.mode().iloc[0])

    # Feeder type per project: from contribution records first, interest as fallback
    _contrib_type = _contrib.groupby('project_key')['feeder_type'].agg(lambda x: x.mode().iloc[0])
    _int_type = _int_deduped.groupby('project_key')['feeder_type'].agg(lambda x: x.mode().iloc[0])
    _proj_type = _contrib_type.combine_first(_int_type)

    # --- AGGREGATE per (home_ecosystem, engagement, feeder_type, project) ---
    _agg = _all.groupby(['home_ecosystem', 'engagement', 'project_key']).agg(
        devs=('dev_id', 'nunique'),
    ).reset_index()
    _agg['project_name'] = _agg['project_key'].map(_display)
    _agg['feeder_type'] = _agg['project_key'].map(_proj_type)

    # Reclassify Ethereum-ecosystem projects out of "Crypto" feeders
    # so the Crypto column only shows Non-Ethereum crypto projects
    _eth_project_keys = {p.lower().strip() for p, eco in PROJECT_ECOSYSTEM.items() if eco == 'Ethereum'}
    _eth_crypto_mask = (_agg['feeder_type'] == 'Crypto') & _agg['project_key'].isin(_eth_project_keys)
    _agg = _agg[~_eth_crypto_mask]

    # Build nested dict for grid
    # {(home_eco, engagement): {'Crypto': [(name, count), ...], 'OSS': [...]}}
    _grid = {}
    for (_eco, _eng), _grp in _agg.groupby(['home_ecosystem', 'engagement']):
        _cell = {}
        for _ft in ['Crypto', 'OSS']:
            _sub = _grp[_grp['feeder_type'] == _ft].sort_values('devs', ascending=False)
            _cell[_ft] = list(zip(_sub['project_name'], _sub['devs']))
        _grid[(_eco, _eng)] = _cell

    # Stats
    _total_qualified = _lifecycle['canonical_developer_id'].nunique()
    _devs_with_contrib = _contrib['dev_id'].nunique()

    feeder_stats = {
        'total_qualified': _total_qualified,
        'devs_with_feeder': _devs_with_contrib,
        'pct_with_feeder': (_devs_with_contrib / _total_qualified * 100) if _total_qualified > 0 else 0,
        'grid': _grid,
    }
    return (feeder_stats,)


@app.cell(hide_code=True)
def transform_pipeline_composition(
    PROJECT_ECOSYSTEM,
    df_contribution_features,
):
    # Onboarding pipeline composition by year — for both ecosystems
    _df = df_contribution_features.copy()
    _df['home_ecosystem'] = _df['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')
    _df['onboard_year'] = _df['onboard_month'].dt.year

    _df['pipeline_category'] = 'Non-crypto experienced'
    _df.loc[_df['is_direct_to_defi'], 'pipeline_category'] = 'Newcomer'
    _df.loc[
        ~_df['is_direct_to_defi'] & _df['pre_primary_ecosystem'].notna(),
        'pipeline_category'
    ] = 'Crypto-experienced'

    _results = {}
    for _eco_key, _eco_filter in [('Ethereum', 'Ethereum'), ('Solana', 'Solana'), ('Other', None)]:
        if _eco_filter:
            _sub = _df[_df['home_ecosystem'] == _eco_filter]
        else:
            _sub = _df[~_df['home_ecosystem'].isin(['Ethereum', 'Solana'])]
        _pipeline = _sub.groupby(['onboard_year', 'pipeline_category']).size().reset_index(name='count')
        _pipeline = _pipeline[_pipeline['onboard_year'].between(2020, 2024)]
        _newcomers = _sub[_sub['pipeline_category'] == 'Newcomer'].groupby('onboard_year').size().to_dict()
        _results[_eco_key] = {'df_pipeline': _pipeline, 'newcomer_counts': _newcomers}

    pipeline_by_eco = _results
    return (pipeline_by_eco,)


@app.cell(hide_code=True)
def settings_color_palette():
    # Color palette — semantic colors reused across all charts
    ETHEREUM_COLOR = '#6F5AE0'
    SOLANA_COLOR = '#10B981'
    OTHER_CRYPTO_COLOR = '#1F9E9A'
    INACTIVE_COLOR = '#B0B7C3'
    MADS_COLOR = '#6B7280'  # medium gray — developer activity count (neutral metric)
    NET_LINE_COLOR = '#374151'
    # Mapping from ecosystem key to display color
    ECO_COLORS = {
        'Ethereum': ETHEREUM_COLOR,
        'Solana': SOLANA_COLOR,
        'Other': OTHER_CRYPTO_COLOR,
    }
    return ECO_COLORS, ETHEREUM_COLOR, INACTIVE_COLOR, MADS_COLOR, NET_LINE_COLOR, OTHER_CRYPTO_COLOR, SOLANA_COLOR


@app.cell(hide_code=True)
def settings_ecosystem_mapping(df_defi_projects):
    # Data-driven ecosystem classification using mart_defi_project_summary.
    # Projects with >80% of TVL on Ethereum (L1 + L2s) are classified as Ethereum.
    # Projects with top_chain = SOLANA are classified as Solana.
    _eth_threshold = 80.0
    _manual_overrides = {
        'Hyperliquid': 'Other',  # Own L1; Arbitrum used only for deposits
        'Fluid': 'Ethereum',     # Primarily Mainnet (76.8% ETH TVL, just below threshold)
    }
    PROJECT_ECOSYSTEM = {}
    for _, _row in df_defi_projects.iterrows():
        _name = _row['project_display_name']
        if _name in _manual_overrides:
            PROJECT_ECOSYSTEM[_name] = _manual_overrides[_name]
        else:
            _pct = _row['ethereum_pct'] if _row['ethereum_pct'] is not None else 0
            if _pct > _eth_threshold:
                PROJECT_ECOSYSTEM[_name] = 'Ethereum'
            elif _row.get('top_chain') == 'SOLANA':
                PROJECT_ECOSYSTEM[_name] = 'Solana'
            else:
                PROJECT_ECOSYSTEM[_name] = 'Other'
    return (PROJECT_ECOSYSTEM,)


@app.cell(hide_code=True)
def settings_plotly_layout(ETHEREUM_COLOR, INACTIVE_COLOR, OTHER_CRYPTO_COLOR):
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#1F2937"),
        margin=dict(t=20, l=60, r=20, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#1F2937", linewidth=1,
            ticks="outside"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#E5E7EB",
            zeroline=True, zerolinecolor="#1F2937", zerolinewidth=1,
            linecolor="#1F2937", linewidth=1,
            ticks="outside"
        ),
        colorway=[ETHEREUM_COLOR, OTHER_CRYPTO_COLOR, INACTIVE_COLOR, '#374151']
    )
    return (PLOTLY_LAYOUT,)


@app.cell(hide_code=True)
def import_libraries():
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return go, make_subplots, pd


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


@app.cell(hide_code=True)
def insight_protocol_table(
    ETHEREUM_COLOR,
    OTHER_CRYPTO_COLOR,
    SOLANA_COLOR,
    df_protocol_table,
    mo,
):
    # Clean protocol summary table using mo.ui.table
    _df = df_protocol_table.copy().reset_index(drop=True)
    _df['top_chain'] = _df['top_chain'].fillna('').str.replace('_', ' ').str.title()

    _display = _df.rename(columns={
        'tvl_rank': 'Rank',
        'project_display_name': 'Project',
        'ecosystem_category': 'Category',
        'current_tvl': 'Total TVL',
        'ethereum_pct': 'ETH TVL Share (%)',
        'top_chain': 'Top Chain',
        'total_repos': 'Repos',
        'qualifying_developers': 'Qualifying Builders',
    })[['Rank', 'Project', 'Category', 'Total TVL', 'ETH TVL Share (%)', 'Top Chain', 'Repos', 'Qualifying Builders']]

    def _fmt_tvl(v):
        if v >= 1e9:
            return f'${v / 1e9:.1f}B'
        if v >= 1e6:
            return f'${v / 1e6:.0f}M'
        return f'${v / 1e3:.0f}K'

    _table = mo.ui.table(
        _display,
        format_mapping={
            'Total TVL': _fmt_tvl,
            'ETH TVL Share (%)': '{:.0f}'.format,
            'Rank': '{:.0f}'.format,
        },
        selection=None,
        page_size=len(_display),
        show_column_summaries=False,
    )

    protocol_table_content = mo.vstack([
        mo.md(
            f'*Qualified* builders have 12+ months of sustained contribution. '
            f'<span style="color:{ETHEREUM_COLOR}">&#9632;</span> Ethereum = &gt;80% TVL on Ethereum (L1+L2s). '
            f'<span style="color:{SOLANA_COLOR}">&#9632;</span> Solana = top chain is Solana. '
            f'<span style="color:{OTHER_CRYPTO_COLOR}">&#9632;</span> Other = remaining chains. '
            f'Manual overrides applied for select projects (e.g., Hyperliquid).'
        ),
        _table,
        mo.md(
            '<small class="ddp-note">'
            '**Note on TVL figures:** TVL values are sourced from DefiLlama and may differ from other sources '
            'due to double-counting across chains, stablecoin classification differences, or timing of snapshots. '
            'ETH TVL Share includes Ethereum L1 and major L2s.'
            '</small>'
        ),
    ])
    return (protocol_table_content,)


@app.cell(hide_code=True)
def insight_alluvial_journeys(
    SOLANA_COLOR,
    ETHEREUM_COLOR,
    INACTIVE_COLOR,
    OTHER_CRYPTO_COLOR,
    alluvial_data_by_eco,
    alluvial_stats_by_eco,
    mo,
):
    # Renders alluvial SVG for all ecosystems, returns content dict
    _CLR_ETH_POOL = '#CDC4F5'
    _CLR_OTHER_POOL = '#A0DCD8'
    _CLR_NON_CRYPTO = '#B8D9F8'
    _CLR_INACTIVE = '#FEF7E0'

    def _hex_to_rgba(hex_color, alpha=0.35):
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f'rgba({r},{g},{b},{alpha})'

    def _render_one(alluvial_data, alluvial_stats, active_color):
        if alluvial_data is None or alluvial_stats.get('empty'):
            return mo.callout(mo.md('**No data available for this ecosystem.**'), kind='warn')

        _years = alluvial_data['years']
        _nodes_by_year = alluvial_data['nodes_by_year']
        _links = alluvial_data['links']
        _project_states = alluvial_data['project_states']

        def _state_color(state):
            if state == 'Ethereum projects': return _CLR_ETH_POOL
            if state == 'Other crypto': return _CLR_OTHER_POOL
            if state == 'Non-crypto OSS': return _CLR_NON_CRYPTO
            if state == 'Inactive': return _CLR_INACTIVE
            if state in _project_states: return active_color
            return INACTIVE_COLOR

        _VB_W = 1600
        _NW = 14
        _COL_X = [220, 450, 680, 910, 1140, 1360]
        _MTOP = 50
        _PAD = 4
        _MIN_H = 1.5

        _total = max(sum(n['count'] for n in _nodes_by_year[_years[0]]), 1)
        _max_nodes = max(len(_nodes_by_year[yr]) for yr in _years)
        _target_h = max(600, _max_nodes * 30)
        _avail = _target_h - 2 * _MTOP
        _pad_total = max(0, _max_nodes - 1) * _PAD
        _node_area = _avail - _pad_total
        _scale = _node_area / _total

        _all_counts = [n['count'] for yr in _years for n in _nodes_by_year[yr]]
        _min_count = min(_all_counts) if _all_counts else 1
        if _min_count * _scale < _MIN_H:
            _scale = _MIN_H / max(_min_count, 1)
            _target_h = _total * _scale + _pad_total + 2 * _MTOP
            _avail = _target_h - 2 * _MTOP

        _node_positions = {}
        for ci, yr in enumerate(_years):
            _col_nodes = _nodes_by_year[yr]
            _col_total = sum(n['count'] for n in _col_nodes)
            _col_pads = max(0, len(_col_nodes) - 1) * _PAD
            _col_h = _col_total * _scale + _col_pads
            _y = _MTOP + (_avail - _col_h) / 2
            for n in _col_nodes:
                _nh = max(_MIN_H, n['count'] * _scale)
                _key = (yr, n['display_state'])
                _node_positions[_key] = {
                    'y0': _y, 'y1': _y + _nh, 'x0': _COL_X[ci], 'x1': _COL_X[ci] + _NW,
                    'count': n['count'], 'state': n['display_state'],
                    'color': _state_color(n['display_state']),
                }
                _y += _nh + _PAD

        _src_y_offsets = {k: v['y0'] for k, v in _node_positions.items()}
        _tgt_y_offsets = {k: v['y0'] for k, v in _node_positions.items()}
        _link_paths = []
        for _i in range(len(_years) - 1):
            _yr_a, _yr_b = _years[_i], _years[_i + 1]
            _zone_links = sorted(
                [l for l in _links if l['source_year'] == _yr_a],
                key=lambda l: (
                    _node_positions.get((_yr_a, l['source_state']), {}).get('y0', 0),
                    _node_positions.get((_yr_b, l['target_state']), {}).get('y0', 0),
                ),
            )
            for l in _zone_links:
                _sk = (_yr_a, l['source_state'])
                _tk = (_yr_b, l['target_state'])
                if _sk not in _node_positions or _tk not in _node_positions:
                    continue
                _s, _t = _node_positions[_sk], _node_positions[_tk]
                _lw = max(_MIN_H, l['count'] * _scale)
                _sy, _ty = _src_y_offsets[_sk], _tgt_y_offsets[_tk]
                _src_y_offsets[_sk] += _lw
                _tgt_y_offsets[_tk] += _lw
                _sx, _tx = _s['x1'], _t['x0']
                _mx = (_sx + _tx) / 2
                _d = (
                    f"M {_sx:.1f},{_sy:.1f} "
                    f"C {_mx:.1f},{_sy:.1f} {_mx:.1f},{_ty:.1f} {_tx:.1f},{_ty:.1f} "
                    f"L {_tx:.1f},{_ty + _lw:.1f} "
                    f"C {_mx:.1f},{_ty + _lw:.1f} {_mx:.1f},{_sy + _lw:.1f} {_sx:.1f},{_sy + _lw:.1f} Z"
                )
                _link_paths.append((_d, _hex_to_rgba(_s['color'], 0.25), l['count'], l['source_state'], l['target_state']))

        _svg = [
            f'<svg viewBox="0 0 {_VB_W} {_target_h:.0f}" '
            f'style="width:100%;height:auto;" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="system-ui, -apple-system, sans-serif">',
            '<style>.al-lk{transition:opacity .15s}.al-lk:hover{opacity:.7!important}</style>',
        ]
        for _d, _c, _v, _sl, _tl in _link_paths:
            _svg.append(f'<path class="al-lk" d="{_d}" fill="{_c}" opacity="0.4"/>')
        for _key, _n in _node_positions.items():
            _nh = max(_MIN_H, _n['y1'] - _n['y0'])
            _svg.append(f'<rect x="{_n["x0"]}" y="{_n["y0"]:.1f}" width="{_NW}" height="{_nh:.1f}" fill="{_n["color"]}" stroke="#fff" stroke-width="0.5"/>')
        for _key, _n in _node_positions.items():
            _yr, _state = _key
            _ym = (_n['y0'] + _n['y1']) / 2
            if _yr == _years[0]:
                _lx, _anc, _fs = _n['x0'] - 6, 'end', 10
            else:
                _lx, _anc = _n['x1'] + 5, 'start'
                _fs = 9 if _yr == _years[-1] else 8
            _svg.append(f'<text x="{_lx}" y="{_ym:.1f}" dy="0.35em" text-anchor="{_anc}" font-size="{_fs}" fill="#1F2937">{_state} <tspan fill="#6B7280">\u00b7 {_n["count"]}</tspan></text>')
        for _ci, _yr in enumerate(_years):
            _cx = _COL_X[_ci] + _NW / 2
            _label = str(_yr)
            _svg.append(f'<text x="{_cx}" y="25" text-anchor="middle" font-size="13" font-weight="600" fill="#6B7280">{_label}</text>')
        _svg.append('</svg>')

        _legend = (
            f'<span style="color:{active_color}">&#9632;</span> Home projects &nbsp; '
            f'<span style="color:{_CLR_ETH_POOL}">&#9632;</span> Ethereum &nbsp; '
            f'<span style="color:{_CLR_OTHER_POOL}">&#9632;</span> Other crypto &nbsp; '
            f'<span style="color:{_CLR_NON_CRYPTO}">&#9632;</span> Non-crypto OSS &nbsp; '
            f'<span style="color:{_CLR_INACTIVE}">&#9632;</span> Inactive'
        )
        _n_devs = alluvial_stats['total_devs']
        _n_proj = alluvial_stats['n_projects']
        return mo.vstack([
            mo.md(
                f'Most builders stay on their home project or within the same ecosystem year over year ({_n_devs} builders across {_n_proj} projects, 2020\u20132025). '
                'The dominant outflow destination is inactivity, not competing ecosystems.'
            ),
            mo.md('<small>' + _legend + '</small>'),
            mo.Html('\n'.join(_svg)),
        ])

    alluvial_content = {
        'Ethereum': _render_one(alluvial_data_by_eco['Ethereum'], alluvial_stats_by_eco['Ethereum'], ETHEREUM_COLOR),
        'Solana': _render_one(alluvial_data_by_eco['Solana'], alluvial_stats_by_eco['Solana'], SOLANA_COLOR),
        'Other': _render_one(alluvial_data_by_eco['Other'], alluvial_stats_by_eco['Other'], OTHER_CRYPTO_COLOR),
    }
    return (alluvial_content,)


@app.cell(hide_code=True)
def insight_feeder_projects(
    ECO_COLORS,
    ETHEREUM_COLOR,
    OTHER_CRYPTO_COLOR,
    SOLANA_COLOR,
    feeder_stats,
    mo,
):
    # 1x2 grid: Contributing | Starred/Forked — rendered for all ecosystems
    _grid = feeder_stats['grid']
    _N_DEFAULT = 10
    _N_MAX = 30

    _ECO_LABEL_MAP = {'Ethereum': 'Ethereum DeFi', 'Solana': 'Solana DeFi', 'Other': 'Other DeFi'}
    _ECO_HEADER_BG = {'Ethereum': '#F3F1FD', 'Solana': '#F0FDF4', 'Other': '#F0FAF9'}
    _ECO_HEADER_BORDER = {'Ethereum': '#E8E4FA', 'Solana': '#D1FAE5', 'Other': '#D5EDEC'}

    def _render_one(eco_key):
        _active_color = ECO_COLORS.get(eco_key, OTHER_CRYPTO_COLOR)
        _active_label = _ECO_LABEL_MAP.get(eco_key, 'Other DeFi')
        _header_bg = _ECO_HEADER_BG.get(eco_key, '#F0FAF9')
        _header_border = _ECO_HEADER_BORDER.get(eco_key, '#D5EDEC')

        def _render_list(items, color):
            if not items:
                return '<div style="color:#6B7280;font-size:12px;padding:4px 0">\u2014</div>'

            def _render_rows(rows, start_idx=0):
                _out = []
                for _i, (_name, _count) in enumerate(rows, start=start_idx):
                    _bold = 'font-weight:700;color:#1F2937' if _i < 3 else 'font-weight:400;color:#6B7280'
                    _bg = '#FAFAFA' if _i % 2 == 1 else 'white'
                    _out.append(
                        f'<div style="display:flex;justify-content:space-between;padding:3px 4px;'
                        f'font-size:12px;border-bottom:1px solid #F3F4F6;background:{_bg}">'
                        f'<span style="{_bold}">{_name}</span>'
                        f'<span style="color:{color};font-weight:600;min-width:28px;text-align:right">{_count}</span>'
                        f'</div>'
                    )
                return ''.join(_out)

            _capped = items[:_N_MAX]
            if len(_capped) <= _N_DEFAULT:
                return _render_rows(_capped)

            _top = _render_rows(_capped[:_N_DEFAULT])
            _rest = _render_rows(_capped[_N_DEFAULT:], start_idx=_N_DEFAULT)
            _remaining = len(_capped) - _N_DEFAULT
            _suffix = f' ({len(items) - _N_MAX} more not shown)' if len(items) > _N_MAX else ''
            return (
                f'{_top}'
                f'<details style="margin-top:4px">'
                f'<summary style="font-size:11px;color:#6B7280;cursor:pointer;padding:2px 0">'
                f'Show {_remaining} more...{_suffix}</summary>'
                f'{_rest}</details>'
            )

        def _render_cell(eng):
            _cell = _grid.get((_active_label, eng), {'Crypto': [], 'OSS': []})
            return (
                f'<div class="ddp-grid-2">'
                f'<div><div style="font-size:11px;font-weight:600;color:{_active_color};text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px;border-bottom:2px solid {_active_color}">Crypto Ecosystems</div>{_render_list(_cell.get("Crypto", []), _active_color)}</div>'
                f'<div><div style="font-size:11px;font-weight:600;color:{_active_color};text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px;border-bottom:2px solid {_active_color}">Other / Non-Crypto OSS</div>{_render_list(_cell.get("OSS", []), _active_color)}</div>'
                f'</div>'
            )

        _html = (
            f'<div style="margin:0;font-family:system-ui,-apple-system,sans-serif">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden">'
            f'<div style="background:{_header_bg};padding:10px 16px;border-bottom:1px solid {_header_border};border-right:1px solid #E5E7EB;text-align:center">'
            f'<span style="font-size:13px;font-weight:700;color:#1F2937">Contributing</span>'
            f'<span style="font-size:11px;color:#6B7280;display:block">Code contributions pre-onboard</span>'
            f'</div>'
            f'<div style="background:{_header_bg};padding:10px 16px;border-bottom:1px solid {_header_border};text-align:center">'
            f'<span style="font-size:13px;font-weight:700;color:#1F2937">Starred / Forked</span>'
            f'<span style="font-size:11px;color:#6B7280;display:block">GitHub stars &amp; forks pre-onboard</span>'
            f'</div>'
            f'<div style="border-right:1px solid #E5E7EB">'
            f'<div style="background:{_header_bg};padding:8px 16px;border-bottom:1px solid {_header_border}">'
            f'<span style="font-size:12px;font-weight:700;color:{_active_color}">{_active_label}</span>'
            f'<span style="font-size:11px;color:#6B7280"> builders</span>'
            f'</div>'
            f'<div style="padding:8px 16px">{_render_cell("Contributing")}</div>'
            f'</div>'
            f'<div>'
            f'<div style="background:{_header_bg};padding:8px 16px;border-bottom:1px solid {_header_border}">'
            f'<span style="font-size:12px;font-weight:700;color:{_active_color}">{_active_label}</span>'
            f'<span style="font-size:11px;color:#6B7280"> builders</span>'
            f'</div>'
            f'<div style="padding:8px 16px">{_render_cell("Starred / Forked")}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        return mo.vstack([
            mo.md(
                f'{feeder_stats["pct_with_feeder"]:.0f}% of qualified builders had prior '
                f'project engagement before joining DeFi. '
                f'Developer tooling projects trained more future DeFi '
                f'contributors than educational programs.'
            ),
            mo.Html(_html),
        ])

    feeder_content = {
        'Ethereum': _render_one('Ethereum'),
        'Solana': _render_one('Solana'),
        'Other': _render_one('Other'),
    }
    return (feeder_content,)


@app.cell(hide_code=True)
def insight_balance_of_trade(
    ECO_COLORS,
    ETHEREUM_COLOR,
    INACTIVE_COLOR,
    NET_LINE_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    SOLANA_COLOR,
    balance_stats,
    df_balance_flows,
    go,
    mo,
    static_plotly,
):
    # Renders balance-of-trade charts for all ecosystems
    _ALL_COLORS = {
        'Ethereum': '#CDC4F5',
        'Solana': '#A0DCD8',
        'Other Crypto': '#A0DCD8',
        'Non-Crypto OSS': '#B8D9F8',
        'Inactive': '#FEF7E0',
    }
    _PATTERNS = {
        'Solana': '/',
        'Other Crypto': '',
    }

    _FOCAL_LABELS = {'Ethereum': 'Ethereum DeFi', 'Solana': 'Solana DeFi', 'Other Crypto': 'Other Crypto'}

    def _render_one(focal):
        _PARTNERS = [k for k in _ALL_COLORS if k != focal]
        _focal_label = _FOCAL_LABELS.get(focal, focal)
        _focal_color = ECO_COLORS.get(focal, OTHER_CRYPTO_COLOR)

        _df = df_balance_flows[df_balance_flows['focal'] == focal]
        _years = sorted(_df['year'].unique())
        _year_pos = list(range(len(_years)))

        _net_vals = []
        for _y in _years:
            _imp = int(_df[(_df['year'] == _y) & (_df['direction'] == 'import')]['count'].sum())
            _exp = int(_df[(_df['year'] == _y) & (_df['direction'] == 'export')]['count'].sum())
            _net_vals.append(_imp - _exp)

        _stats = balance_stats[focal]
        _total_net = _stats['net']
        _total_sign = '+' if _total_net >= 0 else ''

        _net_by_partner = {}
        for _p in _PARTNERS:
            _imp_sum = int(_df[(_df['direction'] == 'import') & (_df['partner'] == _p)]['count'].sum())
            _exp_sum = int(_df[(_df['direction'] == 'export') & (_df['partner'] == _p)]['count'].sum())
            _net_by_partner[_p] = _imp_sum - _exp_sum

        if focal == 'Ethereum':
            _interpretation = (
                f'Ethereum DeFi shifted from net inflows through 2022 to net outflows after 2023. '
                'This is driven primarily by a decline in newcomer and non-crypto builder inflows, '
                'not competitive displacement by other ecosystems.'
            )
        else:
            _interpretation = (
                f'{_focal_label} shows a net flow of {_total_sign}{_total_net} builders ({_stats["first_year"]}\u2013{_stats["last_year"]}). '
                'Year-over-year changes reflect shifts in builder inflows and outflows across ecosystem boundaries.'
            )

        def _hex_to_rgb(hex_color):
            _h = hex_color.lstrip('#')
            return int(_h[0:2], 16), int(_h[2:4], 16), int(_h[4:6], 16)

        _fig_detail = go.Figure()
        for _p in _PARTNERS:
            _r, _g, _b = _hex_to_rgb(_ALL_COLORS[_p])
            _pat = _PATTERNS.get(_p, '')
            _vals = [int(_df[(_df['year'] == _y) & (_df['direction'] == 'import') & (_df['partner'] == _p)]['count'].sum()) for _y in _years]
            _fig_detail.add_trace(go.Bar(x=_year_pos, y=_vals, name=_p, marker_color=f'rgba({_r},{_g},{_b},1.0)', marker_pattern_shape=_pat))
        for _p in _PARTNERS:
            _r, _g, _b = _hex_to_rgb(_ALL_COLORS[_p])
            _pat = _PATTERNS.get(_p, '')
            _vals = [-int(_df[(_df['year'] == _y) & (_df['direction'] == 'export') & (_df['partner'] == _p)]['count'].sum()) for _y in _years]
            _fig_detail.add_trace(go.Bar(x=_year_pos, y=_vals, name=_p, marker_color=f'rgba({_r},{_g},{_b},0.55)', marker_pattern_shape=_pat, showlegend=False))
        _fig_detail.add_trace(go.Scatter(x=_year_pos, y=_net_vals, mode='lines+markers+text', line=dict(color=NET_LINE_COLOR, width=4), marker=dict(size=8, color=NET_LINE_COLOR), text=[f'{"+" if v >= 0 else ""}{v}' for v in _net_vals], textposition=['top center' if v >= 0 else 'bottom center' for v in _net_vals], textfont=dict(size=12, color=NET_LINE_COLOR), showlegend=False))
        _fig_detail.update_layout(**{**PLOTLY_LAYOUT, "barmode": "relative", "title": dict(text="Annual builder inflows/outflows by source/destination", font=dict(size=12)), "height": 420, "margin": dict(l=50, r=20, t=80, b=40), "legend": dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=12)), "xaxis": dict(showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', tickvals=_year_pos, ticktext=[str(y) for y in _years]), "yaxis": dict(showgrid=True, gridcolor='#E5E7EB', linecolor='#1F2937', linewidth=1, ticks='outside', zeroline=True, zerolinecolor='#1F2937', zerolinewidth=1.5)})

        _stat_blocks = [
            mo.stat(value=f'{_total_sign}{_total_net}', label='Total net', bordered=True, caption=f'{_stats["count_before"]} \u2192 {_stats["count_after"]} builders ({_stats["first_year"]}\u2013{_stats["last_year"]})'),
            *[mo.stat(value=f'{"+" if _net_by_partner[_p] >= 0 else ""}{_net_by_partner[_p]}', label=f'net from {_p}', bordered=True, caption='of total') for _p in _PARTNERS],
        ]

        return mo.vstack([
            mo.md(_interpretation),
            mo.hstack(_stat_blocks, widths='equal', gap=1),
            static_plotly(_fig_detail),
        ])

    balance_content = {
        'Ethereum': _render_one('Ethereum'),
        'Solana': _render_one('Solana'),
        'Other': _render_one('Other Crypto'),
    }
    return (balance_content,)


@app.cell(hide_code=True)
def insight_cohort_retention(
    ETHEREUM_COLOR,
    INACTIVE_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    SOLANA_COLOR,
    cohort_retention_by_eco,
    go,
    mo,
    static_plotly,
):
    # Renders cohort retention for all ecosystems
    def _render_one(df_cohort, base_color):
        if df_cohort.empty:
            return mo.md("*No cohort data available.*")
        _years = sorted(df_cohort['onboard_year'].unique())
        _bh = base_color.lstrip('#')
        _br, _bg, _bb = int(_bh[0:2], 16), int(_bh[2:4], 16), int(_bh[4:6], 16)
        _cohort_colors = {}
        for _i, _yr in enumerate(_years):
            _opacity = 0.3 + 0.7 * (_i / max(len(_years) - 1, 1))
            _cohort_colors[_yr] = f'rgba({_br},{_bg},{_bb},{_opacity})'

        _fig = go.Figure()
        for year in _years:
            _data = df_cohort[df_cohort['onboard_year'] == year].sort_values('quarters_since')
            # Downsample: keep every other quarter to reduce output size
            _data = _data.iloc[::2] if len(_data) > 10 else _data
            _n = int(_data['cohort_size'].iloc[0])
            _fig.add_trace(go.Scatter(
                x=_data['quarters_since'] / 4, y=_data['pct_active'], mode='lines',
                name=f'{int(year)} (n={_n})',
                line=dict(color=_cohort_colors.get(year, INACTIVE_COLOR), width=3),
                showlegend=False,
            ))
            _last = _data.iloc[-1]
            _fig.add_annotation(
                x=_last['quarters_since'] / 4, y=_last['pct_active'],
                text=f' {int(year)}', showarrow=False, xanchor='left',
                font=dict(size=12, color=_cohort_colors.get(year, INACTIVE_COLOR)),
            )

        _two_year = df_cohort[df_cohort['quarters_since'] == 8]
        _avg_2yr = _two_year['pct_active'].mean() if len(_two_year) > 0 else 0
        _fig.add_vline(x=2, line_dash='dot', line_color='#E5E7EB', line_width=1)
        _fig.add_annotation(x=2, y=105, text=f'~{_avg_2yr:.0f}% at 2 years', showarrow=False, font=dict(size=12, color='#6B7280'))

        _fig.update_layout(**{**PLOTLY_LAYOUT, "height": 400, "margin": dict(l=60, r=60, t=20, b=50), "showlegend": False, "xaxis": dict(title='Years since first home project activity', showgrid=False, dtick=1, linecolor='#1F2937', linewidth=1, ticks='outside'), "yaxis": dict(title='% Still Active on Home Project', range=[0, 112], showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside')})

        return mo.vstack([
            mo.md(f'Average 2-year retention is ~{_avg_2yr:.0f}%. Cohorts are anchored to each builder\'s first quarter of home project contribution. These curves track builders who already cleared 12+ months of activity, so they represent committed contributors rather than casual participants.'),
            static_plotly(_fig),
        ])

    cohort_content = {
        'Ethereum': _render_one(cohort_retention_by_eco['Ethereum'], ETHEREUM_COLOR),
        'Solana': _render_one(cohort_retention_by_eco['Solana'], SOLANA_COLOR),
        'Other': _render_one(cohort_retention_by_eco['Other'], OTHER_CRYPTO_COLOR),
    }
    return (cohort_content,)


@app.cell(hide_code=True)
def insight_new_developer_inflow(
    ETHEREUM_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    SOLANA_COLOR,
    go,
    mo,
    pipeline_by_eco,
    static_plotly,
):
    # Renders inflow charts for all ecosystems
    def _render_one(eco_key, active_color):
        _data = pipeline_by_eco[eco_key]
        _df_pipeline = _data['df_pipeline']
        _newcomer_counts = _data['newcomer_counts']

        _cat_order = ['Newcomer', 'Non-crypto experienced']
        _cat_colors = {'Newcomer': '#FEF7E0', 'Non-crypto experienced': '#B8D9F8'}
        _cat_labels = {'Newcomer': 'Newcomers (new to crypto)', 'Non-crypto experienced': 'Non-crypto OSS builders'}

        _filtered = _df_pipeline[_df_pipeline['pipeline_category'].isin(_cat_order)]
        _pivot = _filtered.pivot(index='onboard_year', columns='pipeline_category', values='count').fillna(0).reindex(columns=_cat_order)
        _year_labels = [str(int(y)) for y in _pivot.index.tolist()]
        _year_pos = list(range(len(_year_labels)))

        _fig = go.Figure()
        for cat in _cat_order:
            if cat in _pivot.columns:
                _vals = _pivot[cat].tolist()
                _fig.add_trace(go.Bar(
                    x=_year_pos, y=_vals, name=_cat_labels.get(cat, cat),
                    marker_color=_cat_colors[cat],
                    text=[str(int(v)) for v in _vals], textposition='inside',
                    insidetextanchor='middle', textfont=dict(size=11, color='#1F2937'), showlegend=True,
                ))

        _fig.update_layout(**{**PLOTLY_LAYOUT, "barmode": "group", "height": 320, "margin": dict(l=60, r=20, t=20, b=40), "showlegend": True, "legend": dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, bgcolor="rgba(255,255,255,0)", font=dict(size=12)), "xaxis": dict(title='Onboarding Year', showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', tickvals=_year_pos, ticktext=_year_labels), "yaxis": dict(title='Builders', showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside')})

        _newcomer_2021 = _newcomer_counts.get(2021, 0)
        _newcomer_2024 = _newcomer_counts.get(2024, 0)
        _drop_pct = (1 - _newcomer_2024 / max(_newcomer_2021, 1)) * 100

        return mo.vstack([
            mo.md(f'Newcomer inflow peaked in 2021 at {_newcomer_2021} and has since declined ~{_drop_pct:.0f}% to {_newcomer_2024}. Non-crypto OSS builder inflows have also dropped steeply.'),
            static_plotly(_fig),
        ])

    inflow_content = {
        'Ethereum': _render_one('Ethereum', ETHEREUM_COLOR),
        'Solana': _render_one('Solana', SOLANA_COLOR),
        'Other': _render_one('Other', OTHER_CRYPTO_COLOR),
    }
    return (inflow_content,)


@app.cell(hide_code=True)
def insight_ecosystem_overview(
    SOLANA_COLOR,
    ETHEREUM_COLOR,
    MADS_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    PROJECT_ECOSYSTEM,
    df_monthly_devs,
    df_tvl_history,
    df_with_status,
    go,
    make_subplots,
    mo,
    pd,
    static_plotly,
):
    def _render_one(eco_label, active_color):
        if eco_label in ('Ethereum', 'Solana'):
            _eco_projects = {p for p, e in PROJECT_ECOSYSTEM.items() if e == eco_label}
        else:
            _eco_projects = {p for p, e in PROJECT_ECOSYSTEM.items() if e not in ('Ethereum', 'Solana')}

        _eco_devs = df_with_status[df_with_status['project_display_name'].isin(_eco_projects)]
        _eco_devs_dedup = _eco_devs.drop_duplicates(subset='canonical_developer_id', keep='first')
        _total = len(_eco_devs_dedup)
        if _total == 0:
            return mo.md("*No data available.*")
        _newcomers = int(_eco_devs_dedup['is_direct_to_defi'].sum())
        _active = _eco_devs_dedup['is_still_active'].sum()
        _active_pct = (_active / _total * 100) if _total > 0 else 0
        _avg_tenure = _eco_devs_dedup['tenure_months'].mean()

        _tvl = df_tvl_history[df_tvl_history['project_display_name'].isin(_eco_projects)].copy()
        _devs = df_monthly_devs[df_monthly_devs['project_display_name'].isin(_eco_projects)].copy()
        _has_tvl = not _tvl.empty
        _has_devs = not _devs.empty

        _chart = None
        if _has_tvl or _has_devs:
            if _has_tvl:
                _tvl['sample_date'] = pd.to_datetime(_tvl['sample_date'])
                _tvl['month_key'] = _tvl['sample_date'].dt.to_period('M')
                _tvl_agg = _tvl.groupby('month_key')['tvl'].sum().reset_index()
                _tvl_agg = _tvl_agg.sort_values('month_key')
            if _has_devs:
                _devs['month_dt'] = pd.to_datetime(_devs['month_str'])
                _devs['month_key'] = _devs['month_dt'].dt.to_period('M')
                _devs_agg = _devs.groupby('month_key')['monthly_active_devs'].sum().reset_index()
                _devs_agg = _devs_agg.sort_values('month_key')

            _current_month = pd.Timestamp.now().to_period('M')
            if _has_tvl:
                _tvl_agg = _tvl_agg[_tvl_agg['month_key'] < _current_month]
            if _has_devs:
                _devs_agg = _devs_agg[_devs_agg['month_key'] < _current_month]
            _has_tvl = _has_tvl and not _tvl_agg.empty
            _has_devs = _has_devs and not _devs_agg.empty

            _all_months = set()
            if _has_tvl:
                _all_months.update(_tvl_agg['month_key'].unique())
            if _has_devs:
                _all_months.update(_devs_agg['month_key'].unique())
            _all_months = sorted(_all_months)
            _month_labels = [str(m) for m in _all_months]
            _month_pos = list(range(len(_all_months)))
            _month_map = {m: i for i, m in enumerate(_all_months)}

            _fig = make_subplots(specs=[[{"secondary_y": True}]])

            if _has_tvl:
                _tvl_pos = [_month_map[m] for m in _tvl_agg['month_key']]
                _r, _g, _b = int(active_color[1:3], 16), int(active_color[3:5], 16), int(active_color[5:7], 16)
                _fig.add_trace(
                    go.Scatter(x=_tvl_pos, y=_tvl_agg['tvl'].tolist(), mode='lines',
                               line=dict(color=f'rgba({_r},{_g},{_b},0.2)', width=1, shape='hvh'),
                               fill='tozeroy', fillcolor=f'rgba({_r},{_g},{_b},0.06)',
                               name='TVL', showlegend=True),
                    secondary_y=True,
                )
            if _has_devs:
                _dev_pos = [_month_map[m] for m in _devs_agg['month_key']]
                _fig.add_trace(
                    go.Scatter(x=_dev_pos, y=_devs_agg['monthly_active_devs'].tolist(), mode='lines',
                               line=dict(color=MADS_COLOR, width=2.5, shape='hvh'), name='Monthly Active Builders', showlegend=True),
                    secondary_y=False,
                )

            _tick_step = max(1, len(_month_labels) // 8)
            _tick_vals = _month_pos[::_tick_step]
            _tick_text = [_month_labels[i] for i in _tick_vals]

            _fig.update_layout(**{**PLOTLY_LAYOUT, "height": 320, "margin": dict(l=60, r=60, t=20, b=40), "xaxis": dict(showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', tickvals=_tick_vals, ticktext=_tick_text), "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)})
            _fig.update_yaxes(title_text="Active Builders", showgrid=True, gridcolor='#E5E7EB', linecolor='#1F2937', linewidth=1, ticks='outside', rangemode='tozero', secondary_y=False)
            _fig.update_yaxes(title_text="TVL (USD)", showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', rangemode='tozero', tickfont=dict(color='#C0C0C0'), title_font=dict(color='#C0C0C0'), secondary_y=True)
            _chart = static_plotly(_fig)

        _eco_name = {'Ethereum': 'Ethereum', 'Solana': 'Solana', 'Other': 'other'}.get(eco_label, eco_label)
        _elements = [
            mo.md(f"## How large is {_eco_name} DeFi's builder base?"),
            mo.hstack([
                mo.stat(value=f"{_total}", label="Qualifying Builders", bordered=True),
                mo.stat(value=f"{_newcomers}", label="Newcomers", bordered=True),
                mo.stat(value=f"{_active_pct:.0f}%", label="Still Active", bordered=True),
                mo.stat(value=f"{_avg_tenure:.0f} mo", label="Avg Tenure", bordered=True),
            ], justify='space-around', widths='equal'),
        ]
        if _chart is not None:
            _elements.append(mo.md(f'Aggregate TVL and monthly active builders across {_eco_name} DeFi projects over time.<br><small class="ddp-note">This is not a correlation chart --- TVL (background) and builder counts (foreground) are shown together to provide context on ecosystem-level trends, not to imply a causal relationship.</small>'))
            _elements.append(_chart)

        return mo.vstack(_elements)

    ecosystem_overview_content = {
        'Ethereum': _render_one('Ethereum', ETHEREUM_COLOR),
        'Solana': _render_one('Solana', SOLANA_COLOR),
        'Other': _render_one('Other', OTHER_CRYPTO_COLOR),
    }
    return (ecosystem_overview_content,)


@app.cell(hide_code=True)
def ethereum_content(
    alluvial_content,
    balance_content,
    cohort_content,
    ecosystem_overview_content,
    feeder_content,
    inflow_content,
    mo,
):
    _eth = mo.vstack([
        ecosystem_overview_content['Ethereum'],
        mo.md("---"),
        mo.md("## Where does Ethereum DeFi builder talent flow over time?"),
        mo.md('<small class="ddp-note">Each column is a year. Colored bands show where builders are active. Flows between columns trace how builders move between states year-over-year. Wider bands = more builders.</small>'),
        alluvial_content['Ethereum'],
        mo.md("---"),
        mo.md("## Is Ethereum DeFi retaining builder talent over time?"),
        mo.md('<small class="ddp-note">Bars above zero = builders entering the ecosystem; below zero = leaving. The dark line tracks net flow. Categories: **Other Crypto** = non-Ethereum chains, **Non-Crypto OSS** = traditional open source, **Inactive** = no observable activity for 12+ months. 2025 data is partial.</small>'),
        balance_content['Ethereum'],
        mo.md("---"),
        mo.md("## How long do Ethereum DeFi builders stay active after onboarding?"),
        mo.md('<small class="ddp-note">Each line tracks a cohort of builders from their onboarding year. Retention = % still active on home project at each interval. Recent cohorts have shorter curves because less time has elapsed.</small>'),
        cohort_content['Ethereum'],
        mo.md("---"),
        mo.md("## Where do new Ethereum DeFi builders come from?"),
        mo.md('<small class="ddp-note">Breakdown of builder onboarding pipeline by year. Newcomers had less than 6 months of prior OSS activity before joining DeFi.</small>'),
        inflow_content['Ethereum'],
        mo.md("---"),
        mo.md("## Which projects seed the Ethereum DeFi builder pipeline?"),
        mo.md('<small class="ddp-note">Top feeder projects by number of builders who contributed before joining Ethereum DeFi. Includes both crypto and non-crypto open source projects.</small>'),
        feeder_content['Ethereum'],
    ])
    ethereum_tab_content = _eth
    return (ethereum_tab_content,)


@app.cell(hide_code=True)
def solana_content(
    alluvial_content,
    balance_content,
    cohort_content,
    ecosystem_overview_content,
    feeder_content,
    inflow_content,
    mo,
):
    _sol = mo.vstack([
        ecosystem_overview_content['Solana'],
        mo.md("---"),
        mo.md("## Where does Solana DeFi builder talent flow over time?"),
        mo.md('<small class="ddp-note">Each column is a year. Colored bands show where builders are active. Flows between columns trace how builders move between states year-over-year. Wider bands = more builders.</small>'),
        alluvial_content['Solana'],
        mo.md("---"),
        mo.md("## Is Solana DeFi retaining builder talent over time?"),
        mo.md('<small class="ddp-note">Bars above zero = builders entering the ecosystem; below zero = leaving. The dark line tracks net flow. Categories: **Ethereum** = Ethereum L1+L2 projects, **Non-Crypto OSS** = traditional open source, **Inactive** = no observable activity for 12+ months. 2025 data is partial.</small>'),
        balance_content['Solana'],
        mo.md("---"),
        mo.md("## How long do Solana DeFi builders stay active after onboarding?"),
        mo.md('<small class="ddp-note">Each line tracks a cohort of builders from their onboarding year. Retention = % still active on home project at each interval. Recent cohorts have shorter curves because less time has elapsed.</small>'),
        cohort_content['Solana'],
        mo.md("---"),
        mo.md("## Where do new Solana DeFi builders come from?"),
        mo.md('<small class="ddp-note">Breakdown of builder onboarding pipeline by year. Newcomers had less than 6 months of prior OSS activity before joining DeFi.</small>'),
        inflow_content['Solana'],
        mo.md("---"),
        mo.md("## Which projects seed the Solana DeFi builder pipeline?"),
        mo.md('<small class="ddp-note">Top feeder projects by number of builders who contributed before joining Solana DeFi. Includes both crypto and non-crypto open source projects.</small>'),
        feeder_content['Solana'],
    ])
    solana_tab_content = _sol
    return (solana_tab_content,)


@app.cell(hide_code=True)
def other_ecosystem_content(
    alluvial_content,
    balance_content,
    cohort_content,
    ecosystem_overview_content,
    feeder_content,
    inflow_content,
    mo,
):
    _other = mo.vstack([
        ecosystem_overview_content['Other'],
        mo.md("---"),
        mo.md("## Where does other DeFi builder talent flow over time?"),
        mo.md('<small class="ddp-note">Each column is a year. Colored bands show where builders are active. Flows between columns trace how builders move between states year-over-year. Wider bands = more builders.</small>'),
        alluvial_content['Other'],
        mo.md("---"),
        mo.md("## Is other DeFi retaining builder talent over time?"),
        mo.md('<small class="ddp-note">Bars above zero = builders entering the ecosystem; below zero = leaving. The dark line tracks net flow. Categories: **Ethereum** = Ethereum L1+L2 projects, **Non-Crypto OSS** = traditional open source, **Inactive** = no observable activity for 12+ months. 2025 data is partial.</small>'),
        balance_content['Other'],
        mo.md("---"),
        mo.md("## How long do other DeFi builders stay active after onboarding?"),
        mo.md('<small class="ddp-note">Each line tracks a cohort of builders from their onboarding year. Retention = % still active on home project at each interval. Recent cohorts have shorter curves because less time has elapsed.</small>'),
        cohort_content['Other'],
        mo.md("---"),
        mo.md("## Where do new other DeFi builders come from?"),
        mo.md('<small class="ddp-note">Breakdown of builder onboarding pipeline by year. Newcomers had less than 6 months of prior OSS activity before joining DeFi.</small>'),
        inflow_content['Other'],
        mo.md("---"),
        mo.md("## Which projects seed the other DeFi builder pipeline?"),
        mo.md('<small class="ddp-note">Top feeder projects by number of builders who contributed before joining other DeFi ecosystems. Includes both crypto and non-crypto open source projects.</small>'),
        feeder_content['Other'],
    ])
    other_tab_content = _other
    return (other_tab_content,)


@app.cell(hide_code=True)
def comparison_tab(
    ETHEREUM_COLOR,
    NET_LINE_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    PROJECT_ECOSYSTEM,
    SOLANA_COLOR,
    balance_stats,
    cohort_retention_by_eco,
    df_monthly_devs,
    df_projects_with_eco,
    go,
    mo,
    non_eth_stats,
    pd,
    pipeline_by_eco,
    static_plotly,
):
    # 1. Overlaid retention curves (Ethereum vs non-Ethereum)
    _fig_ret = go.Figure()
    _df_eth = cohort_retention_by_eco['Ethereum']
    if not _df_eth.empty:
        _avg_eth = _df_eth.groupby('quarters_since').agg(pct_active=('pct_active', 'mean')).reset_index()
        # Downsample retention curves
        _avg_eth = _avg_eth.iloc[::2] if len(_avg_eth) > 10 else _avg_eth
        _fig_ret.add_trace(go.Scatter(
            x=_avg_eth['quarters_since'] / 4, y=_avg_eth['pct_active'], mode='lines',
            name='Ethereum', line=dict(color=ETHEREUM_COLOR, width=3),
        ))
        _last = _avg_eth.iloc[-1]
        _fig_ret.add_annotation(x=_last['quarters_since'] / 4, y=_last['pct_active'], text=' Ethereum', showarrow=False, xanchor='left', font=dict(size=12, color=ETHEREUM_COLOR))

    _non_eth_parts = [cohort_retention_by_eco[k] for k in ('Solana', 'Other') if not cohort_retention_by_eco[k].empty]
    if _non_eth_parts:
        _df_non_eth = pd.concat(_non_eth_parts, ignore_index=True)
        _avg_non_eth = _df_non_eth.groupby('quarters_since').agg(pct_active=('pct_active', 'mean')).reset_index()
        _avg_non_eth = _avg_non_eth.iloc[::2] if len(_avg_non_eth) > 10 else _avg_non_eth
        _fig_ret.add_trace(go.Scatter(
            x=_avg_non_eth['quarters_since'] / 4, y=_avg_non_eth['pct_active'], mode='lines',
            name='Non-Ethereum', line=dict(color=OTHER_CRYPTO_COLOR, width=3),
        ))
        _last = _avg_non_eth.iloc[-1]
        _fig_ret.add_annotation(x=_last['quarters_since'] / 4, y=_last['pct_active'], text=' Non-Ethereum', showarrow=False, xanchor='left', font=dict(size=12, color=OTHER_CRYPTO_COLOR))

    _fig_ret.add_vline(x=2, line_dash='dot', line_color='#E5E7EB', line_width=1)
    _fig_ret.update_layout(**{**PLOTLY_LAYOUT, "height": 380, "margin": dict(l=60, r=120, t=20, b=50), "showlegend": False, "xaxis": dict(title='Years since first home project activity', showgrid=False, dtick=1, linecolor='#1F2937', linewidth=1, ticks='outside'), "yaxis": dict(title='% Still Active (avg across cohorts)', range=[0, 112], showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside')})

    # 2. Newcomer inflow (Ethereum vs non-Ethereum)
    _fig_inflow = go.Figure()
    _df_eth_p = pipeline_by_eco['Ethereum']['df_pipeline']
    _eth_newcomers = _df_eth_p[_df_eth_p['pipeline_category'] == 'Newcomer'].set_index('onboard_year')['count']
    _years = sorted(_eth_newcomers.index)
    _fig_inflow.add_trace(go.Bar(
        x=[y - 0.2 for y in _years], y=[_eth_newcomers.get(y, 0) for y in _years],
        name='Ethereum', marker_color=ETHEREUM_COLOR, width=0.35,
        text=[str(int(_eth_newcomers.get(y, 0))) for y in _years],
        textposition='outside', textfont=dict(size=10), cliponaxis=False,
    ))
    _non_eth_newcomers = {}
    for _ek in ('Solana', 'Other'):
        _df_p = pipeline_by_eco[_ek]['df_pipeline']
        _nc = _df_p[_df_p['pipeline_category'] == 'Newcomer'].set_index('onboard_year')['count']
        for _y in _nc.index:
            _non_eth_newcomers[_y] = _non_eth_newcomers.get(_y, 0) + _nc[_y]
    _ne_years = sorted(_non_eth_newcomers.keys())
    _fig_inflow.add_trace(go.Bar(
        x=[y + 0.2 for y in _ne_years], y=[_non_eth_newcomers.get(y, 0) for y in _ne_years],
        name='Non-Ethereum', marker_color=OTHER_CRYPTO_COLOR, width=0.35,
        text=[str(int(_non_eth_newcomers.get(y, 0))) for y in _ne_years],
        textposition='outside', textfont=dict(size=10), cliponaxis=False,
    ))
    _fig_inflow.update_layout(**{**PLOTLY_LAYOUT, "barmode": "group", "height": 350, "margin": dict(l=60, r=20, t=40, b=40), "showlegend": True, "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)), "xaxis": dict(title='Onboarding Year', showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', dtick=1), "yaxis": dict(title='Newcomer builders', showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', autorange=True)})

    # 3. Cross-ecosystem tug-of-war
    _eth_imports = non_eth_stats['import_count']
    _eth_exports = non_eth_stats['export_count']
    _eth_net = _eth_imports - _eth_exports
    _eth_sign = '+' if _eth_net >= 0 else ''

    _eth_bs = balance_stats['Ethereum']
    _sol_bs = balance_stats.get('Solana', {'net': 0, 'count_before': 0, 'count_after': 0})
    _oth_bs = balance_stats['Other Crypto']
    _non_eth_net = _sol_bs['net'] + _oth_bs['net']
    _non_eth_sign = '+' if _non_eth_net >= 0 else ''
    _non_eth_before = _sol_bs['count_before'] + _oth_bs['count_before']
    _non_eth_after = _sol_bs['count_after'] + _oth_bs['count_after']

    _fig_tow = go.Figure()
    _fig_tow.add_trace(go.Bar(
        x=[_eth_imports], y=[''], orientation='h',
        marker_color=ETHEREUM_COLOR, showlegend=False,
        text=[f'  +{_eth_imports} to Ethereum'], textposition='outside',
        textfont=dict(size=13, color=ETHEREUM_COLOR),
    ))
    _fig_tow.add_trace(go.Bar(
        x=[-_eth_exports], y=[''], orientation='h',
        marker_color=OTHER_CRYPTO_COLOR, showlegend=False,
        text=[f'{_eth_exports} to Other  '], textposition='outside',
        textfont=dict(size=13, color=OTHER_CRYPTO_COLOR),
    ))
    _max_bar = max(_eth_imports, _eth_exports)
    _fig_tow.add_annotation(
        x=0, y=0, yshift=36,
        text=f"Net: {_eth_sign}{_eth_net} to Ethereum",
        showarrow=False, font=dict(size=13, color=NET_LINE_COLOR),
    )
    _fig_tow.update_layout(**{**PLOTLY_LAYOUT, "barmode": "overlay", "height": 100, "margin": dict(l=20, r=20, t=40, b=20), "showlegend": False, "xaxis": dict(zeroline=True, zerolinecolor=NET_LINE_COLOR, zerolinewidth=2, showgrid=False, showticklabels=False, range=[-_max_bar * 1.8, _max_bar * 1.8]), "yaxis": dict(showticklabels=False, showline=False, ticks='')})

    # 4. Overlaid monthly active devs (Ethereum vs non-Ethereum)
    _fig_devs = go.Figure()
    _current_month = pd.Timestamp.now().to_period('M')
    _eth_projects = {p for p, e in PROJECT_ECOSYSTEM.items() if e == 'Ethereum'}
    _non_eth_projects = {p for p, e in PROJECT_ECOSYSTEM.items() if e != 'Ethereum'}

    for _projects, _color, _label in [
        (_eth_projects, ETHEREUM_COLOR, 'Ethereum'),
        (_non_eth_projects, OTHER_CRYPTO_COLOR, 'Non-Ethereum'),
    ]:
        _d = df_monthly_devs[df_monthly_devs['project_display_name'].isin(_projects)].copy()
        if _d.empty:
            continue
        _d['month_dt'] = pd.to_datetime(_d['month_str'])
        _d['month_key'] = _d['month_dt'].dt.to_period('M')
        _d = _d[_d['month_key'] < _current_month]
        _d_agg = _d.groupby('month_key')['monthly_active_devs'].sum().reset_index().sort_values('month_key')
        _fig_devs.add_trace(go.Scatter(
            x=[str(m) for m in _d_agg['month_key']],
            y=_d_agg['monthly_active_devs'].tolist(),
            mode='lines', name=_label,
            line=dict(color=_color, width=2.5, shape='hvh'),
        ))

    _fig_devs.update_layout(**{**PLOTLY_LAYOUT, "height": 320, "margin": dict(l=60, r=20, t=20, b=40), "showlegend": True, "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)), "xaxis": dict(showgrid=False, linecolor='#1F2937', linewidth=1, ticks='outside', dtick='M12'), "yaxis": dict(title='Monthly Active Builders', showgrid=True, gridcolor='#E5E7EB', linecolor='#1F2937', linewidth=1, ticks='outside', rangemode='tozero')})

    # Protocol grid (Ethereum vs Non-Ethereum)
    _grid_df = df_projects_with_eco.copy()
    _logo_fixes = {'Jito Network': 'https://icons.llama.fi/jito.png'}
    for _n, _u in _logo_fixes.items():
        _grid_df.loc[_grid_df['project_display_name'] == _n, 'logo'] = _u

    _grid_eth = _grid_df[_grid_df['ecosystem_category'] == 'Ethereum'].head(20).reset_index(drop=True)
    _grid_non = _grid_df[_grid_df['ecosystem_category'] != 'Ethereum'].head(20).reset_index(drop=True)

    _fig_grid = go.Figure()
    _G_COLS, _G_GAP = 4, 1.5
    _G_ROWS_L = (len(_grid_eth) + _G_COLS - 1) // _G_COLS
    _G_ROWS_R = (len(_grid_non) + _G_COLS - 1) // _G_COLS
    _G_MAX = max(_G_ROWS_L, _G_ROWS_R)

    def _grid_group(df, col_offset, border_color, label):
        _n_rows = (len(df) + _G_COLS - 1) // _G_COLS
        for _i, (_, _row) in enumerate(df.iterrows()):
            if _i >= _G_COLS * _n_rows:
                break
            _ri, _ci = _i // _G_COLS, _i % _G_COLS
            _x = _ci + col_offset
            _y = (_G_MAX - 1) - _ri
            _dn = _row['project_display_name']
            if len(_dn) > 18:
                _dn = _dn[:16] + '\u2026'
            _fig_grid.add_annotation(x=_x, y=_y - 0.35, text=f"<b>{_dn}</b>", showarrow=False, font=dict(size=9, color="#4B5563"), xanchor="center", yanchor="top")
            if pd.notna(_row.get('logo')):
                _fig_grid.add_layout_image(source=_row['logo'], x=_x, y=_y + 0.1, xref="x", yref="y", sizex=0.55, sizey=0.55, xanchor="center", yanchor="middle", layer="above")
        _x0, _x1 = col_offset - 0.5, col_offset + _G_COLS - 0.5
        _y0 = (_G_MAX - 1) - _n_rows + 0.35
        _y1 = (_G_MAX - 1) + 0.85
        _r, _g, _b = int(border_color[1:3], 16), int(border_color[3:5], 16), int(border_color[5:7], 16)
        _fig_grid.add_shape(type="rect", x0=_x0, y0=_y0, x1=_x1, y1=_y1, line=dict(color=border_color, width=2), fillcolor=f"rgba({_r},{_g},{_b},0.04)", layer="below")
        _fig_grid.add_annotation(x=(_x0 + _x1) / 2, y=_y1 + 0.15, text=f"<b>{label}</b>", showarrow=False, font=dict(size=13, color=border_color), xanchor="center", yanchor="bottom")

    _grid_group(_grid_eth, col_offset=0, border_color=ETHEREUM_COLOR, label="Ethereum DeFi")
    _grid_group(_grid_non, col_offset=_G_COLS + _G_GAP, border_color=OTHER_CRYPTO_COLOR, label="Non-Ethereum DeFi")
    _g_total_w = _G_COLS * 2 + _G_GAP
    _fig_grid.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="system-ui, -apple-system, sans-serif", size=12, color="#1F2937"),
        width=1050, height=max(350, _G_MAX * 85 + 60),
        xaxis=dict(range=[-0.8, _g_total_w - 0.2], showgrid=False, zeroline=False, showticklabels=False, showline=False),
        yaxis=dict(range=[-0.7, _G_MAX + 0.6], showgrid=False, zeroline=False, showticklabels=False, showline=False),
        margin=dict(t=5, l=20, r=60, b=5),
    )

    # Assembly
    comparison_tab_content = mo.vstack([
        static_plotly(_fig_grid),
        mo.md("---"),
        mo.md("### Monthly active builders over time"),
        mo.md('<small class="ddp-note">Aggregate monthly active builder count across all projects in each group.</small>'),
        static_plotly(_fig_devs),
        mo.md("---"),
        mo.md("### Cross-ecosystem flows: tug of war"),
        mo.md('<small class="ddp-note">Direct builder movement between Ethereum and non-Ethereum DeFi. Counts builders whose primary ecosystem changed year-over-year.</small>'),
        static_plotly(_fig_tow),
        mo.hstack([
            mo.stat(value=f'{"+" if _eth_bs["net"] >= 0 else ""}{_eth_bs["net"]}', label='Ethereum total net', bordered=True, caption=f'{_eth_bs["count_before"]} \u2192 {_eth_bs["count_after"]} ({_eth_bs["first_year"]}\u2013{_eth_bs["last_year"]})'),
            mo.stat(value=f'{_non_eth_sign}{_non_eth_net}', label='Non-Ethereum total net', bordered=True, caption=f'{_non_eth_before} \u2192 {_non_eth_after} ({_eth_bs["first_year"]}\u2013{_eth_bs["last_year"]})'),
        ], widths='equal', gap=1),
        mo.md("---"),
        mo.md("### Retention: who sticks around longer?"),
        mo.md('<small class="ddp-note">Average retention across all year cohorts (2020\u20132024). Each curve averages the % still active at each quarter interval.</small>'),
        static_plotly(_fig_ret),
        mo.md("---"),
        mo.md("### Newcomer pipeline: who attracts more fresh talent?"),
        mo.md('<small class="ddp-note">Newcomers = builders with less than 6 months of prior OSS activity before their DeFi onboarding.</small>'),
        static_plotly(_fig_inflow),
    ])
    return (comparison_tab_content,)


@app.cell(hide_code=True)
def section_conclusion(mo):
    mo.accordion({
        "Metrics & Definitions": mo.md("""
        - Ecosystem Classification:
            - Ethereum: Projects with >80% of TVL on Ethereum (L1 + L2s like Arbitrum, Polygon, Base, Optimism, etc.)
            - Solana: Projects whose top chain by TVL is Solana
            - Other: Remaining non-Ethereum, non-Solana projects (including Hyperliquid, Bitcoin, etc.)
        - Project Classifications:
            - Home Project: The DeFi project a builder is primarily associated with, based on their most active repository contributions.
            - Feeder Projects: Projects where a builder contributed or starred repositories before onboarding to their home DeFi project.
        - Builder Classifications:
            - Qualifying Builder: A builder with 12+ months of sustained contribution to a top DeFi project's home repositories.
            - Monthly Active Builders (MABs): Count of unique qualified builders with at least one contribution event in a given month.
            - Newcomer: A qualified builder with fewer than 6 months of observable open-source activity before onboarding to their home project (came in cold).
            - Cohort Retention: The percentage of builders from a given onboarding cohort (year) who remain active on their home project at each subsequent time interval.
        - Lifecycle:
            - Onboarding: A builder's first month of activity on their home project.
            - Offboarding: A builder is considered offboarded if they have been inactive on their home project for 6+ consecutive months.
            - Still Active: A builder who has contributed to their home project within the most recent 6 months of data.
        - Flows:
            - Net Flow: The year-over-year difference between builders entering and exiting an ecosystem. Positive means net talent gain.
            - Cross-Ecosystem Flow (Ethereum <-> Other Crypto): The horizontal bar in the Net Flows section counts unique builders who moved between Ethereum and other crypto ecosystems over the full time period. This uses a different method from the annual inflow/outflow bars, which count year-over-year flows by source/destination category; the two methods do not sum to each other.
            - Year-over-Year Flows: The annual bar chart breaks down builder inflows (entering) and outflows (leaving) by partner category (Other Crypto, Non-Crypto OSS, Inactive). The net flow line shows the cumulative balance; these year-over-year counts sum to the total net flow shown in the stat cards.
        """),
        "Assumptions & Limitations": mo.md("""
        - TVL as inclusion criterion: We use TVL to identify economically meaningful protocols, which excludes low-stakes forks and testnet-only experiments; this analysis focuses on capital-securing DeFi.
        - Excluded protocols: Some high-TVL protocols have minimal observable OSS activity, so they may appear in tables but contribute little to flow analysis.
        - Private repositories: Activity in private repos is not visible to GitHub Archive, so teams that develop behind closed doors (or move to private repos after open-source phases) may appear to go inactive; this is one of the most consequential limitations.
        - Post-hire behavior: Some builders are hired by crypto firms and stop public contributions, so the inactive count may be inflated; we cannot distinguish left crypto from went private.
        - Bot and noise filtering: We exclude known bots, but some automated contributions may still slip through.
        - Identity resolution: OpenDevData maps multiple accounts to canonical IDs, but imperfect mapping may double-count some builders.
        - Scope: This is a structured analysis of visible OSS builder flows across economically significant DeFi protocols, not a census of all crypto builders or proprietary development.
        """),
        "Data Sources": mo.md("""
        - [DefiLlama](https://defillama.com/) --- Top DeFi protocols by TVL (40 selected)
        - [OSS Directory](https://github.com/opensource-observer/oss-directory) --- Protocol to GitHub mapping
        - [OpenDevData (Electric Capital)](https://github.com/electric-capital/crypto-ecosystems) --- Ecosystem classifications
        - [GitHub Archive](https://www.gharchive.org/) --- Builder activity events
        - [OSO API](https://docs.oso.xyz/) --- Data pipeline and metrics
        """),
    })
    return


@app.cell(hide_code=True)
def main_layout(
    comparison_tab_content,
    ethereum_tab_content,
    mo,
    other_tab_content,
    protocol_table_ethereum,
    protocol_table_other,
    protocol_table_solana,
    solana_tab_content,
):
    # CSS-only tabs for static export compatibility
    # Each ecosystem tab includes a highlighted protocol table + content
    _tab_configs = [
        ("Ethereum", protocol_table_ethereum, ethereum_tab_content),
        ("Solana", protocol_table_solana, solana_tab_content),
        ("Other Ecosystems", protocol_table_other, other_tab_content),
        ("Side-by-Side", None, comparison_tab_content),
    ]
    _tab_ids = [f"main-tab-{i}" for i in range(len(_tab_configs))]
    _tab_names = [t[0] for t in _tab_configs]

    # Build panel HTML: highlighted table (if any) + tab content
    # Wrap in max-width container so tables, SVGs, and charts all align
    _wrap = '<div>'
    _wrap_end = '</div>'
    _content_htmls = []
    for _name, _table_html, _content in _tab_configs:
        _content_str = mo.as_html(_content).text
        if _table_html:
            _content_htmls.append(f'{_wrap}{_table_html}<hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;">{_content_str}{_wrap_end}')
        else:
            _content_htmls.append(f'{_wrap}{_content_str}{_wrap_end}')

    _css = (
        '<style>'
        '.html-tabs { margin: 0; }'
        '.html-tabs input[type="radio"] { display: none; }'
        '.html-tabs .tab-bar {'
        '    display: flex;'
        '    border-bottom: 2px solid #e2e8f0;'
        '    margin-bottom: 20px;'
        '}'
        '.html-tabs .tab-bar label {'
        '    padding: 10px 24px;'
        '    cursor: pointer;'
        '    font-weight: 500;'
        '    font-size: 14px;'
        '    color: #64748b;'
        '    border-bottom: 2px solid transparent;'
        '    margin-bottom: -2px;'
        '    transition: color 0.15s, border-color 0.15s;'
        '    user-select: none;'
        '    white-space: nowrap;'
        '}'
        '.html-tabs .tab-bar label:hover {'
        '    color: #334155;'
        '    background: #f8fafc;'
        '}'
        '.html-tabs .tab-panel { display: none; }'
        + ''.join(
            f'.html-tabs input#{tid}:checked ~ .tab-bar label[for="{tid}"] '
            f'{{ color: #2563eb; border-bottom-color: #2563eb; font-weight: 600; }}'
            for tid in _tab_ids
        )
        + ''.join(
            f'.html-tabs input#{tid}:checked ~ .tab-panel.p-{tid} {{ display: block; }}'
            for tid in _tab_ids
        )
        + '</style>'
    )

    _radios = ''.join(
        f'<input type="radio" name="main-tabs" id="{tid}" {"checked" if i == 0 else ""}>'
        for i, tid in enumerate(_tab_ids)
    )
    _bar = '<div class="tab-bar">' + ''.join(
        f'<label for="{tid}">{name}</label>'
        for tid, name in zip(_tab_ids, _tab_names)
    ) + '</div>'
    _panels = ''.join(
        f'<div class="tab-panel p-{tid}">{html}</div>'
        for tid, html in zip(_tab_ids, _content_htmls)
    )

    mo.vstack([
        mo.md("## Which DeFi projects are included?"),
        mo.md("We analyzed builder activity across 40 top DeFi protocols on Ethereum and other major L1s."),
        mo.md("Select an ecosystem to explore:"),
        mo.Html(f'<div class="html-tabs">{_css}{_radios}{_bar}{_panels}</div>'),
    ])
    return


if __name__ == "__main__":
    app.run()
