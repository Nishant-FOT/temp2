"""
Streamlit UI for CFO Operating System
3-screen dashboard for visualization and decision support.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import inspect
from orchestrator import CFOOrchestrator


# Page configuration
st.set_page_config(
    page_title="AI CFO Control Panel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ffcccc;
        color: #111827;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #cc0000;
    }
    .alert-high {
        background-color: #ffe6cc;
        color: #111827;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ff6600;
    }
    .alert-medium {
        background-color: #ffffcc;
        color: #111827;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffcc00;
    }
    .alert-safe {
        background-color: #ccffcc;
        color: #111827;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #00cc00;
    }
    .alert-critical h3, .alert-critical p, .alert-critical strong,
    .alert-high h3, .alert-high p, .alert-high strong,
    .alert-medium h3, .alert-medium p, .alert-medium strong,
    .alert-safe h3, .alert-safe p, .alert-safe strong {
        color: inherit;
    }
    .briefing-card {
        background-color: #f8f9fa;
        color: #111827;
        padding: 20px;
        border-radius: 8px;
        line-height: 1.8;
        font-size: 16px;
        border: 1px solid #d1d5db;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_orchestrator():
    """Initialize orchestrator (cached)."""
    return CFOOrchestrator(current_cash=700000)


def build_orchestrator(**kwargs):
    """Instantiate the orchestrator while tolerating older loaded signatures."""
    signature = inspect.signature(CFOOrchestrator.__init__)
    supported_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in signature.parameters
    }
    return CFOOrchestrator(**supported_kwargs)


def get_risk_color(risk_level):
    """Get color for risk level."""
    colors = {
        'critical': '#cc0000',
        'high': '#ff6600',
        'medium': '#ffcc00',
        'low': '#00cc00',
    }
    return colors.get(risk_level, '#999999')


def get_severity_color(severity):
    """Get color for severity level."""
    return get_risk_color(severity)


def screen_1_alert_dashboard(result):
    """Screen 1: Alert Dashboard with key metrics and charts."""
    st.header("🚨 Alert Dashboard", divider="red")

    if result.get('data_source') == 'zaggle':
        status = result.get('data_source_status', 'connected')
        message = result.get('data_source_message', '')
        if status == 'fallback_synthetic':
            st.warning(f"Zaggle source fallback: {message}")
        else:
            st.info(f"Data source: Zaggle transaction exports. {message}")
    
    # Top Alert Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        spend_data = result['spend_intelligence']
        forecast_data = result['cashflow_forecast']
        
        # Determine combined alert level
        max_alert = max(
            0 if spend_data['severity'] == 'low' else 1,
            0 if forecast_data['risk_level'] == 'low' else 1,
        )
        
        if max_alert == 1:
            if spend_data['severity'] == 'critical' or forecast_data['risk_level'] == 'critical':
                alert_css = "alert-critical"
                icon = "🚨"
                title = "CRITICAL ALERT"
            elif spend_data['severity'] == 'high' or forecast_data['risk_level'] == 'high':
                alert_css = "alert-high"
                icon = "⚠️"
                title = "HIGH ALERT"
            else:
                alert_css = "alert-medium"
                icon = "📊"
                title = "ATTENTION NEEDED"
        else:
            alert_css = "alert-safe"
            icon = "✅"
            title = "HEALTHY STATUS"
        
        st.markdown(f"""
        <div class="{alert_css}">
        <h3>{icon} {title}</h3>
        <p><strong>Issue:</strong> {spend_data['issue']}</p>
        <p><strong>Risk:</strong> {forecast_data['risk_level'].upper()} - {forecast_data['days_to_risk']} days to cash constraint</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Transactions", result['transaction_count'], border=True)
        st.metric("Current Cash", f"${result['current_cash']:,.0f}", border=True)
    
    # Key Metrics Section
    st.subheader("📈 Key Metrics")
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        st.metric(
            "Days to Cash Out",
            result['cashflow_forecast']['days_to_risk'],
            delta="forecast runway",
            delta_color="inverse"
        )
    
    with metric_cols[1]:
        st.metric(
            "Cash Coverage",
            f"{result['cashflow_forecast']['cash_ratio']:.1f}x",
            delta=f"${result['current_cash']:,.0f} on hand",
            delta_color="normal"
        )
    
    with metric_cols[2]:
        liquidity_gap = result['cashflow_forecast']['liquidity_gap']
        st.metric(
            "Liquidity Gap",
            f"${abs(liquidity_gap):,.0f}",
            delta="surplus" if liquidity_gap >= 0 else "shortfall",
            delta_color="normal" if liquidity_gap >= 0 else "inverse"
        )
    
    with metric_cols[3]:
        projected_ending_cash = result['cashflow_forecast']['projected_ending_cash']
        burn_adjustment = result['cashflow_forecast'].get('burn_adjustment', 0.0) * 100
        burn_posture = result['cashflow_forecast'].get('burn_posture', 'steady state')
        st.metric(
            "Projected 30d End Cash",
            f"${projected_ending_cash:,.0f}",
            delta=f"{burn_adjustment:+.0f}% burn | {burn_posture}",
            delta_color="normal" if projected_ending_cash >= 0 else "inverse"
        )

    st.subheader("Spend Intelligence Enhancers")
    spend_data = result['spend_intelligence']
    focus_category = spend_data.get('category')
    budget_rate = spend_data.get('headline_budget_consumption', 0)
    vendor_hhi = spend_data.get('headline_vendor_hhi', 0)
    top_vendor = spend_data.get('headline_top_vendor', 'n/a')
    top_vendor_share = spend_data.get('headline_top_vendor_share', 0)

    enhancer_cols = st.columns(3)
    with enhancer_cols[0]:
        st.metric(
            "Budget Consumption",
            f"{budget_rate:.0%}",
            delta=(focus_category or 'n/a').replace('_', ' ').title(),
            border=True
        )
    with enhancer_cols[1]:
        concentration_label = 'High' if vendor_hhi >= 0.25 else 'Medium' if vendor_hhi >= 0.15 else 'Low'
        st.metric(
            "Vendor HHI",
            f"{vendor_hhi:.2f}",
            delta=f"{concentration_label} concentration",
            border=True
        )
    with enhancer_cols[2]:
        st.metric(
            "Top Vendor Share",
            f"{top_vendor_share:.0%}",
            delta=top_vendor,
            border=True
        )
    
    # Charts Section
    st.subheader("📊 Spend Trend & Forecast")
    chart_cols = st.columns(2)
    
    with chart_cols[0]:
        # Anomaly scores by category
        anomalies = result['spend_intelligence']['anomaly_scores']
        if anomalies:
            df_anomalies = pd.DataFrame(
                list(anomalies.items()),
                columns=['Category', 'Anomaly Score']
            )
            
            fig = px.bar(
                df_anomalies,
                x='Category',
                y='Anomaly Score',
                color='Anomaly Score',
                color_continuous_scale='RdYlGn_r',
                height=350,
                title='Spending Anomaly Scores by Category'
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    with chart_cols[1]:
        # Cashflow forecast
        forecast_values = result['cashflow_forecast']['forecast_values']
        if forecast_values:
            df_forecast = pd.DataFrame({
                'Day': range(1, len(forecast_values) + 1),
                'Daily Burn': forecast_values
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_forecast['Day'],
                y=df_forecast['Daily Burn'],
                mode='lines+markers',
                name='Projected Daily Burn',
                line=dict(color='#ff6600', width=2),
                fill='tozeroy'
            ))
            fig.update_layout(
                title='30-Day Cashflow Forecast',
                xaxis_title='Day',
                yaxis_title='Daily Burn ($)',
                height=350,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)


def screen_2_agent_reasoning(result):
    """Screen 2: Detailed Agent Reasoning."""
    st.header("🤖 Agent Reasoning", divider="blue")
    
    # Decision comparisons
    st.subheader("Decision Comparison Matrix")
    
    comparisons = result['decision_analysis']['comparisons']
    df_comparisons = pd.DataFrame([
        {
            'Action': comp['action'].replace('_', ' ').title(),
            'Level': comp.get('level_display', comp.get('level', 'N/A')),
            'Risk Before': f"{comp.get('risk_before', 0):.2f}",
            'Risk After': f"{comp.get('risk_after', 0):.2f}",
            'Risk Reduction': f"{comp.get('risk_reduction', 0):.2f}",
            'Business Cost': f"{comp.get('business_cost', 0):.2f}",
            'Feasibility': f"{comp.get('feasibility', 0):.2f}",
            'Reversibility': f"{comp.get('reversibility', 0):.2f}",
            'Score': f"{comp.get('score', 0):.3f}"
        }
        for comp in comparisons
    ])
    
    # Highlight best action
    best_action = result['decision_analysis']['best_action'].replace('_', ' ').title()
    
    st.dataframe(
        df_comparisons,
        use_container_width=True,
        hide_index=True
    )
    
    # Recommendation box
    decision = result['decision_analysis']
    color = get_risk_color('low') if decision['confidence'] > 0.7 else get_risk_color('medium')
    level_display = decision.get('level_display')
    if level_display is None:
        level_value = decision.get('level')
        level_display = level_value if level_value is not None else 'N/A'
    
    st.markdown(f"""
    <div style="background-color: {color}20; border-left: 4px solid {color}; padding: 15px; border-radius: 8px; margin-top: 20px;">
    <h3>✅ Recommended Action</h3>
    <h2 style="color: {color};">{best_action}</h2>
    <p><strong>Level:</strong> {level_display}</p>
    <p><strong>Decision Margin:</strong> {decision['confidence']:.0%}</p>
    <p><strong>Reasoning:</strong> {decision['reasoning']}</p>
    <p><strong>Note:</strong> Decision margin shows how far the top-ranked option is ahead of the runner-up, not model certainty.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Scenario-Specific Action Set")
    available_actions = decision.get('available_actions', [])
    if available_actions:
        actions_df = pd.DataFrame([
            {
                'Action': item['action'].replace('_', ' ').title(),
                'Available Levels': ", ".join(item['levels']),
            }
            for item in available_actions
        ])
        st.dataframe(
            actions_df,
            use_container_width=True,
            hide_index=True
        )
    
    # Agent Details
    st.subheader("Agent Analysis Details")
    
    agent_cols = st.columns(2)
    
    with agent_cols[0]:
        st.write("**Spend Intelligence Agent**")
        st.write(f"- Issue: {result['spend_intelligence']['issue']}")
        st.write(f"- Category: {result['spend_intelligence']['category']}")
        st.write(f"- Severity: {result['spend_intelligence']['severity'].upper()}")
        st.write(f"- Confidence: {result['spend_intelligence']['confidence']:.0%}")
        st.write(f"- Budget Consumption: {result['spend_intelligence'].get('headline_budget_consumption', 0):.0%}")
        st.write(
            f"- Vendor HHI: {result['spend_intelligence'].get('headline_vendor_hhi', 0):.2f} "
            f"({result['spend_intelligence'].get('headline_top_vendor', 'n/a')}, "
            f"{result['spend_intelligence'].get('headline_top_vendor_share', 0):.0%} share)"
        )
    
    with agent_cols[1]:
        st.write("**Cashflow Forecast Agent**")
        st.write(f"- Risk Level: {result['cashflow_forecast']['risk_level'].upper()}")
        st.write(f"- Days to Risk: {result['cashflow_forecast']['days_to_risk']}")
        st.write(f"- Risk Score: {result['cashflow_forecast']['risk_score']:.2f}")


def screen_3_cfo_briefing(result):
    """Screen 3: CFO Executive Briefing."""
    st.header("📋 CFO Executive Briefing", divider="green")
    
    briefing = result['executive_briefing']['narrative']
    briefing_html = briefing.replace("\n", "<br>")
    
    # Large, readable briefing text
    st.markdown(f"""
    <div class="briefing-card">
    {briefing_html}
    </div>
    """, unsafe_allow_html=True)
    
    # Recommended action summary
    st.subheader("📌 Action Items")
    
    decision = result['decision_analysis']
    best_action = decision['best_action'].replace('_', ' ').title()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Recommended Action", best_action, border=True)
    
    with col2:
        st.metric("Decision Margin", f"{decision['confidence']:.0%}", border=True)
    
    with col3:
        confidence_level = "High" if decision['confidence'] > 0.7 else "Medium" if decision['confidence'] > 0.4 else "Low"
        st.metric("Decision Clarity", confidence_level, border=True)

    st.subheader("Business State Summary")
    state_of_business = result.get('state_of_business', 'profit')
    state_descriptions = {
        'survival': "The model assumes defensive cash preservation, tighter spend controls, and higher urgency around liquidity protection.",
        'profit': "The model assumes disciplined growth, stronger unit economics, and prioritization of operating efficiency over aggressive expansion.",
        'growth': "The model assumes expansion mode, higher investment tolerance, and a willingness to trade near-term cash efficiency for scale.",
    }
    capital_efficiency = result.get('fpa_analysis', {}).get('kpis', {}).get('capital_efficiency_status', 'moderate')
    company_age = result.get('company_age_years', result.get('planning_assumptions', {}).get('company_age_years', 5))
    st.info(
        f"State of business: **{state_of_business.replace('_', ' ').title()}**. "
        f"{state_descriptions.get(state_of_business, 'Current business state is applied to the operating model.')} "
        f"Capital efficiency is currently **{str(capital_efficiency).title()}** and company age is **{company_age} years**."
    )

    st.subheader("Monte Carlo Liquidity Simulation")
    monte_carlo = result['cashflow_forecast'].get('monte_carlo', {})
    peer_benchmark = result['cashflow_forecast'].get('peer_benchmark', {})
    peer_monte_carlo = peer_benchmark.get('monte_carlo', {})
    action_simulation = decision.get('recommended_action_simulation', {})
    action_monte_carlo = action_simulation.get('monte_carlo', {})

    if monte_carlo.get('days'):
        fig = go.Figure()
        chart_values = []

        for idx, path in enumerate(monte_carlo.get('sample_paths', [])):
            chart_values.extend(path)
            fig.add_trace(go.Scatter(
                x=monte_carlo['days'],
                y=path,
                mode='lines',
                line=dict(color='rgba(100, 116, 139, 0.16)', width=1),
                name='Sample Path' if idx == 0 else None,
                showlegend=(idx == 0),
                hoverinfo='skip'
            ))

        chart_values.extend(monte_carlo.get('p10_cash', []))
        chart_values.extend(monte_carlo.get('p50_cash', []))
        chart_values.extend(monte_carlo.get('p90_cash', []))

        fig.add_trace(go.Scatter(
            x=monte_carlo['days'],
            y=monte_carlo['p90_cash'],
            mode='lines',
            line=dict(color='rgba(22, 163, 74, 0)'),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=monte_carlo['days'],
            y=monte_carlo['p10_cash'],
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(251, 191, 36, 0.20)',
            line=dict(color='rgba(245, 158, 11, 0)'),
            name='P10-P90 Range',
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=monte_carlo['days'],
            y=monte_carlo['p50_cash'],
            mode='lines',
            name='Baseline Median Path',
            line=dict(color='#dc2626', width=3)
        ))

        if peer_monte_carlo.get('days'):
            chart_values.extend(peer_monte_carlo.get('p10_cash', []))
            chart_values.extend(peer_monte_carlo.get('p50_cash', []))
            chart_values.extend(peer_monte_carlo.get('p90_cash', []))

            fig.add_trace(go.Scatter(
                x=peer_monte_carlo['days'],
                y=peer_monte_carlo['p90_cash'],
                mode='lines',
                line=dict(color='rgba(37, 99, 235, 0)'),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=peer_monte_carlo['days'],
                y=peer_monte_carlo['p10_cash'],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(59, 130, 246, 0.12)',
                line=dict(color='rgba(37, 99, 235, 0)'),
                name='Peer Cohort Range',
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=peer_monte_carlo['days'],
                y=peer_monte_carlo['p50_cash'],
                mode='lines',
                name='Peer Cohort Median',
                line=dict(color='#2563eb', width=2, dash='dash')
            ))

        if action_monte_carlo.get('days'):
            chart_values.extend(action_monte_carlo.get('p10_cash', []))
            chart_values.extend(action_monte_carlo.get('p50_cash', []))
            chart_values.extend(action_monte_carlo.get('p90_cash', []))

            fig.add_trace(go.Scatter(
                x=action_monte_carlo['days'],
                y=action_monte_carlo['p90_cash'],
                mode='lines',
                line=dict(color='rgba(14, 165, 233, 0)'),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=action_monte_carlo['days'],
                y=action_monte_carlo['p10_cash'],
                mode='lines',
                fill='tonexty',
                fillcolor='rgba(56, 189, 248, 0.18)',
                line=dict(color='rgba(14, 165, 233, 0)'),
                name='Recommended Action Range',
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=action_monte_carlo['days'],
                y=action_monte_carlo['p50_cash'],
                mode='lines',
                name='Recommended Action Median',
                line=dict(color='#0369a1', width=3, dash='dot')
            ))

        max_abs_cash = max([abs(value) for value in chart_values], default=0)
        y_axis_limit = max(1000, max_abs_cash * 1.1)

        fig.add_hrect(y0=0, y1=y_axis_limit, fillcolor='rgba(34, 197, 94, 0.06)', line_width=0)
        fig.add_hrect(y0=-y_axis_limit, y1=0, fillcolor='rgba(239, 68, 68, 0.06)', line_width=0)
        fig.add_hline(y=0, line_dash='dash', line_color='#111827')
        fig.update_layout(
            title='30-Day Cash Balance Scenarios: Baseline vs Recommended Action',
            xaxis_title='Day',
            yaxis_title='Cash Balance ($)',
            height=420,
            hovermode='x unified',
            yaxis=dict(range=[-y_axis_limit, y_axis_limit], zeroline=False)
        )
        st.plotly_chart(fig, use_container_width=True)

        sim_cols = st.columns(3)
        warning_horizon_days = monte_carlo.get('warning_horizon_days', 14)
        with sim_cols[0]:
            st.metric(f"{warning_horizon_days}d Shortfall Probability", f"{monte_carlo['breach_probability']:.0%}", border=True)
        with sim_cols[1]:
            st.metric("Median End Cash", f"${monte_carlo['median_end_cash']:,.0f}", border=True)
        with sim_cols[2]:
            st.metric("Full-Horizon Breach", f"{monte_carlo.get('full_horizon_breach_probability', monte_carlo['breach_probability']):.0%}", border=True)

        if peer_monte_carlo:
            peer_cols = st.columns(3)
            with peer_cols[0]:
                st.metric(
                    "Peer Median End Cash",
                    f"${peer_monte_carlo['median_end_cash']:,.0f}",
                    delta=f"${(peer_monte_carlo['median_end_cash'] - monte_carlo['median_end_cash']):,.0f} vs you",
                    border=True
                )
            with peer_cols[1]:
                st.metric(
                    "Peer Cohort Position",
                    f"{peer_benchmark.get('percentile_rank', 0):.0%}",
                    delta=peer_benchmark.get('relative_position', 'peer view'),
                    border=True
                )
            with peer_cols[2]:
                st.metric(
                    "Peer Label",
                    peer_benchmark.get('label', 'Peer cohort'),
                    border=True
                )

        if action_monte_carlo:
            action_cols = st.columns(3)
            with action_cols[0]:
                st.metric(
                    f"Action {warning_horizon_days}d Shortfall",
                    f"{action_monte_carlo['breach_probability']:.0%}",
                    delta=f"{(action_monte_carlo['breach_probability'] - monte_carlo['breach_probability']):+.0%}",
                    border=True
                )
            with action_cols[1]:
                st.metric(
                    "Action Median End Cash",
                    f"${action_monte_carlo['median_end_cash']:,.0f}",
                    delta=f"${(action_monte_carlo['median_end_cash'] - monte_carlo['median_end_cash']):,.0f}",
                    border=True
                )
            with action_cols[2]:
                action_label = f"{best_action} @ {decision.get('level_display', decision.get('level', 'N/A'))}"
                st.metric("Scenario", action_label, border=True)

        breach_curve = monte_carlo.get('breach_probability_curve', [])
        if breach_curve:
            st.subheader("Shortfall Risk by Day")
            breach_chart = go.Figure()
            breach_chart.add_trace(go.Scatter(
                x=monte_carlo['days'],
                y=breach_curve,
                mode='lines+markers',
                name='Baseline Breach Probability',
                line=dict(color='#dc2626', width=3),
                marker=dict(size=6)
            ))
            action_breach_curve = action_monte_carlo.get('breach_probability_curve', [])
            if action_breach_curve:
                breach_chart.add_trace(go.Scatter(
                    x=action_monte_carlo['days'],
                    y=action_breach_curve,
                    mode='lines+markers',
                    name='Recommended Action Breach Probability',
                    line=dict(color='#0369a1', width=3, dash='dot'),
                    marker=dict(size=6)
                ))
            if peer_monte_carlo.get('breach_probability_curve'):
                breach_chart.add_trace(go.Scatter(
                    x=peer_monte_carlo['days'],
                    y=peer_monte_carlo['breach_probability_curve'],
                    mode='lines',
                    name='Peer Cohort Breach Probability',
                    line=dict(color='#2563eb', width=2, dash='dash')
                ))
            breach_chart.update_layout(
                title='Cumulative Probability of Cash Breach by Day',
                xaxis_title='Day',
                yaxis_title='Probability',
                yaxis=dict(range=[0, 1.05], tickformat='.0%'),
                height=320,
                hovermode='x unified'
            )
            st.plotly_chart(breach_chart, use_container_width=True)
    
    # Session metadata
    st.divider()
    st.markdown("**Session Information**")
    assumptions = result.get('planning_assumptions', {})
    st.write(f"- Session ID: `{result['session_id']}`")
    st.write(f"- Timestamp: {result['timestamp']}")
    st.write(f"- Sector: {result.get('sector', 'N/A').replace('_', ' ').title()}")
    st.write(f"- Business Scale: {result.get('business_scale', 'N/A').replace('_', ' ').title()}")
    st.write(f"- Country: {result.get('country', 'N/A').replace('_', ' ').title()}")
    st.write(f"- Company Market Cap: ${result.get('company_market_capital', result.get('country_market_capital', 0)):,}M")
    st.write(f"- Funding Round: {result.get('funding_round', 'N/A').replace('_', ' ').title()}")
    st.write(f"- State of Business: {result.get('state_of_business', 'profit').replace('_', ' ').title()}")
    st.write(f"- Company Age: {result.get('company_age_years', assumptions.get('company_age_years', 5))} years")
    st.write(f"- Data Source: {result.get('data_source', 'synthetic').replace('_', ' ').title()} ({result.get('data_source_status', 'connected')})")
    st.write(f"- Macro Environment: {result.get('macro_environment', 'N/A').replace('_', ' ').title()}")
    st.write(f"- Close Pressure: {result.get('close_pressure', 'N/A').replace('_', ' ').title()}")
    st.write(f"- Automation Maturity: {result.get('automation_maturity', 'N/A').replace('_', ' ').title()}")
    st.write(
        f"- Advanced Assumptions: horizon {assumptions.get('forecast_horizon_days', 30)}d | "
        f"burn shock {assumptions.get('burn_shock_pct', 0):+.0%} | "
        f"collections delay {assumptions.get('collections_delay_days', 0)}d | "
        f"revenue outlook {assumptions.get('revenue_outlook_pct', 0):+.0%} | "
        f"hiring growth {assumptions.get('hiring_growth_pct', 0):+.0%} | "
        f"WC efficiency {assumptions.get('working_capital_efficiency', 0):.0%} | "
        f"capital efficiency {assumptions.get('capital_efficiency_score', 50):.0f}/100 | "
        f"MC sims {assumptions.get('monte_carlo_sims', 250)}"
    )
    st.write(f"- Analysis Horizon: {result['analysis_horizon']} days")


def screen_4_fpa_workbench(result):
    """Screen 4: FP&A planning, variance, and scenario modeling."""
    st.header("📐 FP&A Workbench", divider="orange")

    fpa = result.get('fpa_analysis', {})
    if not fpa:
        st.warning("No FP&A analysis available for this run.")
        return

    st.markdown(f"**{fpa['headline']}**")
    st.info(fpa.get('planning_narration', ''))

    kpis = fpa.get('kpis', {})
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Plan Attainment", f"{kpis.get('plan_attainment', 0):.0%}", border=True)
    with kpi_cols[1]:
        st.metric("Total Variance", f"${kpis.get('total_variance', 0):,.0f}", border=True)
    with kpi_cols[2]:
        st.metric("Runway Days", kpis.get('runway_days', 0), border=True)
    with kpi_cols[3]:
        st.metric("Action Value", f"${kpis.get('recommended_end_cash_delta', 0):,.0f}", border=True)

    perf_cols = st.columns(4)
    with perf_cols[0]:
        st.metric("Budget Utilization", f"{kpis.get('budget_utilization', 0):.0%}", border=True)
    with perf_cols[1]:
        st.metric(
            "Current Burn",
            f"${kpis.get('current_burn', 0):,.0f}",
            delta=f"{kpis.get('burn_change_pct', 0):+.0%} vs prior run-rate",
            border=True
        )
    with perf_cols[2]:
        driver = str(fpa.get('top_variance_driver', 'n/a')).replace('_', ' ').title()
        st.metric("Top Variance Driver", driver, border=True)
    with perf_cols[3]:
        st.metric(
            "Capital Efficiency",
            f"{kpis.get('capital_efficiency_index', 0):.2f}x",
            delta=str(kpis.get('capital_efficiency_status', 'moderate')).title(),
            border=True
        )

    variance_table = fpa.get('variance_table', [])
    if variance_table:
        st.subheader("Budget vs Actual Variance")
        variance_df = pd.DataFrame([
            {
                'Category': row['category'].title(),
                'Budget': row['budget'],
                'Actual': row['actual'],
                'Variance': row['variance'],
                'Variance %': row['variance_pct'],
                'Status': row['status'].title(),
            }
            for row in variance_table
        ])

        chart = px.bar(
            variance_df,
            x='Category',
            y='Variance',
            color='Variance',
            color_continuous_scale='RdYlGn_r',
            title='Month-to-Date Budget Variance by Category'
        )
        chart.update_layout(height=360)
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(
            variance_df.style.format({
                'Budget': '${:,.0f}',
                'Actual': '${:,.0f}',
                'Variance': '${:,.0f}',
                'Variance %': '{:.1%}',
            }),
            use_container_width=True,
            hide_index=True
        )

    scenarios = fpa.get('scenarios', [])
    if scenarios:
        st.subheader("Scenario Modeling")
        scenario_df = pd.DataFrame([
            {
                'Scenario': scenario['name'],
                'Description': scenario['description'],
                'Avg Daily Burn': scenario['avg_daily_burn'],
                '30d End Cash': scenario['end_cash'],
                'Shortfall Probability': scenario['shortfall_probability'],
            }
            for scenario in scenarios
        ])
        st.dataframe(
            scenario_df.style.format({
                'Avg Daily Burn': '${:,.0f}',
                '30d End Cash': '${:,.0f}',
                'Shortfall Probability': '{:.0%}',
            }),
            use_container_width=True,
            hide_index=True
        )

        scenario_chart = go.Figure()
        scenario_chart.add_trace(go.Bar(
            x=scenario_df['Scenario'],
            y=scenario_df['30d End Cash'],
            name='30d End Cash',
            marker_color=['#9ca3af', '#0369a1', '#dc2626']
        ))
        scenario_chart.update_layout(
            title='Scenario Comparison: 30-Day Ending Cash',
            yaxis_title='Cash ($)',
            height=350
        )
        st.plotly_chart(scenario_chart, use_container_width=True)

    sensitivity_analysis = fpa.get('sensitivity_analysis', [])
    if sensitivity_analysis:
        st.subheader("Sensitivity Analysis")
        sensitivity_df = pd.DataFrame(sensitivity_analysis)
        sensitivity_chart = go.Figure()
        sensitivity_chart.add_trace(go.Scatter(
            x=sensitivity_df['scenario'],
            y=sensitivity_df['end_cash'],
            mode='lines+markers',
            line=dict(color='#7c3aed', width=3),
            marker=dict(size=9),
            name='Ending Cash'
        ))
        sensitivity_chart.update_layout(
            title='Ending Cash Sensitivity to Burn Rate Changes',
            xaxis_title='Sensitivity Scenario',
            yaxis_title='30d End Cash ($)',
            height=320
        )
        st.plotly_chart(sensitivity_chart, use_container_width=True)
        st.dataframe(
            sensitivity_df.style.format({
                'burn_multiplier': '{:.0%}',
                'end_cash': '${:,.0f}',
            }),
            use_container_width=True,
            hide_index=True
        )

    driver_sensitivity = fpa.get('driver_sensitivity', [])
    if driver_sensitivity:
        st.subheader("Driver Sensitivity and Elasticity")
        driver_df = pd.DataFrame(driver_sensitivity)

        tornado_df = driver_df.sort_values('delta_end_cash', key=lambda s: s.abs(), ascending=True)
        tornado_chart = go.Figure()
        tornado_chart.add_trace(go.Bar(
            x=tornado_df['delta_end_cash'],
            y=tornado_df['driver'],
            orientation='h',
            marker_color=['#dc2626' if value < 0 else '#16a34a' for value in tornado_df['delta_end_cash']],
            text=tornado_df['shock'],
            textposition='outside',
            name='End Cash Delta'
        ))
        tornado_chart.add_vline(x=0, line_dash='dash', line_color='#111827')
        tornado_chart.update_layout(
            title='Tornado View: End-Cash Sensitivity by Planning Driver',
            xaxis_title='Delta vs Baseline End Cash ($)',
            yaxis_title='Driver',
            height=340,
            showlegend=False
        )
        st.plotly_chart(tornado_chart, use_container_width=True)
        st.dataframe(
            driver_df.style.format({
                'baseline_end_cash': '${:,.0f}',
                'stressed_end_cash': '${:,.0f}',
                'delta_end_cash': '${:,.0f}',
                'elasticity': '{:.3f}',
            }),
            use_container_width=True,
            hide_index=True
        )

    stress_testing = fpa.get('stress_testing', [])
    if stress_testing:
        st.subheader("Stress Testing (ARIMA)")
        stress_df = pd.DataFrame(stress_testing)
        stress_chart = make_subplots(specs=[[{"secondary_y": True}]])
        stress_chart.add_trace(
            go.Bar(
                x=stress_df['scenario'],
                y=stress_df['end_cash'],
                marker_color=['#0f766e', '#f59e0b', '#dc2626'],
                name='End Cash'
            ),
            secondary_y=False,
        )
        stress_chart.add_trace(
            go.Scatter(
                x=stress_df['scenario'],
                y=stress_df['shortfall_probability'],
                mode='lines+markers+text',
                text=[f"{value:.0%}" for value in stress_df['shortfall_probability']],
                textposition='top center',
                line=dict(color='#1d4ed8', width=3),
                marker=dict(size=9),
                name='Shortfall Probability'
            ),
            secondary_y=True,
        )
        stress_chart.add_trace(
            go.Scatter(
                x=stress_df['scenario'],
                y=stress_df['days_to_risk'],
                mode='markers+text',
                text=[f"{int(value)}d" for value in stress_df['days_to_risk']],
                textposition='bottom center',
                marker=dict(color='#7c3aed', size=12, symbol='diamond'),
                name='Days to Risk'
            ),
            secondary_y=False,
        )
        stress_chart.update_layout(
            title='ARIMA-Based Treasury Stress Test',
            height=360,
            hovermode='x unified'
        )
        stress_chart.update_yaxes(title_text='Ending Cash ($)', secondary_y=False)
        stress_chart.update_yaxes(title_text='Shortfall Probability', range=[0, 1.05], secondary_y=True)
        st.plotly_chart(stress_chart, use_container_width=True)
        st.dataframe(
            stress_df.style.format({
                'avg_daily_burn': '${:,.0f}',
                'end_cash': '${:,.0f}',
                'shortfall_probability': '{:.0%}',
            }),
            use_container_width=True,
            hide_index=True
        )


def screen_5_solution_overview():
    """Screen 5: Solution overview, architecture, and expected impact."""
    st.header("🧭 Overview / Architecture / Impact", divider="violet")

    st.subheader("Concept Note")
    st.markdown("""
    **CFO-OS** is an AI-native finance operating layer built to support CFOs, FP&A leaders, and controllership teams.
    It combines spend intelligence, forecasting, planning automation, and finance controls into one
    decision environment. The module uses Zaggle transaction exports as the operational signal layer, with
    connector-ready architecture for live ingestion, then applies inference models, agentic workflows, and
    generative narration to accelerate finance decisions.
    """)

    concept_cols = st.columns(2)
    with concept_cols[0]:
        st.markdown("""
        **Core Themes**
        - Spend Intelligence powered by Zaggle transaction exports
        - Cash flow forecasting and optimization using agentic and inference models
        - FP&A automation with variance explanations and planning narrations
        - Compliance and close acceleration through anomaly detection and auto-reconciliations
        """)
    with concept_cols[1]:
        st.markdown("""
        **Prototype Deliverables**
        - Concept note and working CFO-OS module prototype
        - Architecture covering agentic, generative, and inference AI layers
        - CFO-oriented business impact view for finance teams and leadership
        """)

    st.subheader("Architecture")
    arch_cols = st.columns(3)
    with arch_cols[0]:
        st.markdown("""
        **Inference AI**
        - anomaly detection on transaction streams
        - cashflow forecasting and burn modeling
        - Monte Carlo liquidity simulation
        - variance and KPI computation
        """)
    with arch_cols[1]:
        st.markdown("""
        **Agentic AI**
        - spend intelligence agent
        - forecast and optimization agent
        - decision simulation engine
        - FP&A and compliance orchestration
        """)
    with arch_cols[2]:
        st.markdown("""
        **Generative AI**
        - executive briefing generation
        - variance explanations
        - planning narration
        - finance-user-friendly action summaries
        """)

    st.markdown("""
    ```text
    Zaggle Transaction Exports -> Feature Engineering -> Inference Models -> Agentic Orchestrator
                             -> FP&A / Compliance Workflows -> Generative Narration -> CFO UI
    ```
    """)

    st.subheader("Expected Business Impact")
    impact_cols = st.columns(3)
    with impact_cols[0]:
        st.markdown("""
        **For CFOs**
        - faster visibility into spend anomalies and liquidity risk
        - scenario-backed actions instead of static reporting
        - stronger confidence in near-term cash decisions
        """)
    with impact_cols[1]:
        st.markdown("""
        **For FP&A Teams**
        - automated variance commentary
        - faster forecast refresh cycles
        - reduced spreadsheet-heavy scenario work
        """)
    with impact_cols[2]:
        st.markdown("""
        **For Controllership**
        - earlier exception detection
        - support for auto-reconciliation flows
        - shorter close cycles with prioritized review
        """)

    st.subheader("Advanced Capability Roadmap")
    st.caption("These modules improve the product direction and architecture, but they are roadmap items unless explicitly implemented elsewhere in the app.")

    roadmap_cols = st.columns(2)
    with roadmap_cols[0]:
        st.markdown("""
        **Group I — FP&A**
        - driver-based forecasting with DAG propagation
        - BvA variance with price-volume-mix decomposition and narration
        - KPI benchmarking against peer sets
        - cohort survival and LTV modeling using BG/NBD and Gamma-Gamma

        **Group II — Risk & Scenarios**
        - multi-dimensional sensitivity with tornado and spider charts
        - elasticity coefficients across key planning drivers
        - correlated Monte Carlo with Cholesky structure
        - forward and reverse stress testing
        - scenario decision trees and corporate VaR / CVaR / EaR / CFaR

        **Group III — Treasury & Cash**
        - 13-week direct-method rolling cash forecast
        - genetic-algorithm cash optimization
        - working-capital liberation modeling from CCC to cash
        - capital structure and WACC optimization
        - FX and commodity hedge program management
        """)
    with roadmap_cols[1]:
        st.markdown("""
        **Group IV — ML & Intelligence**
        - Isolation Forest plus autoencoder anomaly detection
        - dynamic budget consumption and HHI vendor concentration
        - LSTM and ensemble ML cash forecasting
        - ML-augmented revenue forecasting with churn prediction

        **Group V — Strategy & Valuation**
        - DCF, LBO, and comps valuation with football-field outputs
        - ROIC, EVA, and real-options capital allocation
        - full M&A accretion-dilution with synergy modeling

        **Group VI — Close & Compliance**
        - auto-reconciliation plus journal-entry risk scoring
        - tax provision automation with ETR bridge and Pillar Two impact modeling
        - a master CFO Decision Synthesis Engine that aggregates upstream engines into a prioritized decision brief with confidence-scored reasoning chains
        """)


def screen_6_compliance_close(result):
    """Screen 6: Compliance and close acceleration workflow."""
    st.header("🧾 Compliance & Close", divider="gray")

    compliance = result.get('compliance_analysis', {})
    if not compliance:
        st.warning("No compliance analysis available for this run.")
        return

    st.markdown(f"**{compliance['headline']}**")

    kpis = compliance.get('kpis', {})
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Auto-Match Rate", f"{kpis.get('auto_match_rate', 0):.0%}", border=True)
    with kpi_cols[1]:
        st.metric("Review Queue", kpis.get('review_queue', 0), border=True)
    with kpi_cols[2]:
        st.metric("Escalations", kpis.get('escalations', 0), border=True)
    with kpi_cols[3]:
        st.metric("Close Risk", str(kpis.get('close_risk', 'low')).title(), border=True)

    exception_cols = st.columns(2)
    with exception_cols[0]:
        st.subheader("Flagged Transactions")
        exceptions = compliance.get('exceptions', [])
        if exceptions:
            exception_df = pd.DataFrame([
                {
                    'Date': row['date'],
                    'Vendor': row['vendor'],
                    'Category': row['category'].title(),
                    'Amount': row['amount'],
                    'Flags': row['flags'].title(),
                }
                for row in exceptions
            ])
            st.dataframe(
                exception_df.style.format({'Amount': '${:,.0f}'}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No flagged transactions identified in this run.")

    with exception_cols[1]:
        st.subheader("Reconciliation Queue")
        reconciliations = compliance.get('reconciliations', [])
        if reconciliations:
            recon_df = pd.DataFrame([
                {
                    'Date': row['date'],
                    'Vendor': row['vendor'],
                    'Category': row['category'].title(),
                    'Amount': row['amount'],
                    'Status': row['status'].title(),
                }
                for row in reconciliations
            ])
            st.dataframe(
                recon_df.style.format({'Amount': '${:,.0f}'}),
                use_container_width=True,
                hide_index=True
            )

            status_counts = recon_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.pie(
                status_counts,
                names='Status',
                values='Count',
                color='Status',
                color_discrete_map={
                    'Matched': '#16a34a',
                    'Review': '#f59e0b',
                    'Escalate': '#dc2626',
                },
                title='Reconciliation Status Mix'
            )
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reconciliation items available.")


def screen_7_strategic_planning(result):
    """Screen 7: Strategic planning workspace for advanced platform levers."""
    st.header("🗺️ Strategic Planning", divider="rainbow")

    assumptions = result.get('planning_assumptions', {})
    fpa = result.get('fpa_analysis', {})
    cashflow = result.get('cashflow_forecast', {})
    decision = result.get('decision_analysis', {})
    compliance = result.get('compliance_analysis', {})

    st.markdown(
        "Use this view to connect strategic assumptions with treasury, FP&A, and finance-operations outcomes."
    )

    driver_cols = st.columns(6)
    with driver_cols[0]:
        st.metric("Revenue Outlook", f"{assumptions.get('revenue_outlook_pct', 0):+.0%}", border=True)
    with driver_cols[1]:
        st.metric("Hiring Growth", f"{assumptions.get('hiring_growth_pct', 0):+.0%}", border=True)
    with driver_cols[2]:
        st.metric("WC Efficiency", f"{assumptions.get('working_capital_efficiency', 0):.0%}", border=True)
    with driver_cols[3]:
        st.metric("Capital Efficiency", f"{assumptions.get('capital_efficiency_score', 50):.0f}/100", border=True)
    with driver_cols[4]:
        st.metric("Business State", str(result.get('state_of_business', 'profit')).title(), border=True)
    with driver_cols[5]:
        st.metric("Automation", str(result.get('automation_maturity', 'medium')).title(), border=True)

    scenario_cards = st.columns(4)
    with scenario_cards[0]:
        st.metric("Forecast Horizon", f"{assumptions.get('forecast_horizon_days', 30)} days", border=True)
    with scenario_cards[1]:
        st.metric("Runway Outcome", f"{cashflow.get('days_to_risk', 0)} days", border=True)
    with scenario_cards[2]:
        st.metric("Recommended Lever", decision.get('best_action', 'n/a').replace('_', ' ').title(), border=True)
    with scenario_cards[3]:
        st.metric("Company Age", f"{result.get('company_age_years', assumptions.get('company_age_years', 5))} years", border=True)

    st.subheader("Platform Features Enabled")
    platform_features = fpa.get('platform_features', [])
    if platform_features:
        feature_df = pd.DataFrame({"Feature": platform_features})
        st.dataframe(feature_df, use_container_width=True, hide_index=True)

    st.subheader("Strategic Driver Impact")
    impact_rows = [
        {
            "Driver": "Revenue Outlook",
            "Current Setting": f"{assumptions.get('revenue_outlook_pct', 0):+.0%}",
            "Primary Effect": "Improves or weakens net burn through topline momentum",
        },
        {
            "Driver": "Hiring Growth",
            "Current Setting": f"{assumptions.get('hiring_growth_pct', 0):+.0%}",
            "Primary Effect": "Changes payroll expansion and operating leverage",
        },
        {
            "Driver": "Working Capital Efficiency",
            "Current Setting": f"{assumptions.get('working_capital_efficiency', 0):.0%}",
            "Primary Effect": "Improves cash conversion and reduces liquidity drag",
        },
        {
            "Driver": "Capital Efficiency",
            "Current Setting": f"{assumptions.get('capital_efficiency_score', 50):.0f}/100",
            "Primary Effect": "Changes burn discipline, capital productivity, and runway resilience",
        },
        {
            "Driver": "Company Age",
            "Current Setting": f"{result.get('company_age_years', assumptions.get('company_age_years', 5))} years",
            "Primary Effect": "Changes operating maturity, volatility, and action feasibility",
        },
        {
            "Driver": "State of Business",
            "Current Setting": str(result.get('state_of_business', 'profit')).title(),
            "Primary Effect": "Shifts the company between survival, profit discipline, and growth-oriented operating modes",
        },
        {
            "Driver": "Automation Maturity",
            "Current Setting": str(result.get('automation_maturity', 'medium')).title(),
            "Primary Effect": "Raises auto-match rate and reduces close friction",
        },
    ]
    st.dataframe(pd.DataFrame(impact_rows), use_container_width=True, hide_index=True)

    st.subheader("Planning Outcome Snapshot")
    outcome_chart = go.Figure()
    outcome_chart.add_trace(go.Bar(
        x=["Projected End Cash", "Action Value", "Review Queue", "Escalations"],
        y=[
            cashflow.get('projected_ending_cash', 0),
            fpa.get('kpis', {}).get('recommended_end_cash_delta', 0),
            compliance.get('kpis', {}).get('review_queue', 0),
            compliance.get('kpis', {}).get('escalations', 0),
        ],
        marker_color=['#0f766e', '#0369a1', '#f59e0b', '#dc2626']
    ))
    outcome_chart.update_layout(
        title='Strategic Planning Outcomes',
        height=340,
        yaxis_title='Value'
    )
    st.plotly_chart(outcome_chart, use_container_width=True)

    st.info(
        f"Planning narration: {fpa.get('planning_narration', 'No planning commentary available.')} "
        f"Compliance posture remains {compliance.get('kpis', {}).get('close_risk', 'low')} risk "
        f"with {compliance.get('kpis', {}).get('auto_match_rate', 0):.0%} auto-match coverage."
    )


def main():
    """Main app structure."""
    st.title("🏦 AI CFO Control Panel")
    
    # Sidebar
    st.sidebar.title("Settings")
    data_source = st.sidebar.selectbox(
        "Data Source",
        ["synthetic", "zaggle"],
        index=0,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    zaggle_export_path = None
    if data_source == "zaggle":
        zaggle_export_path = st.sidebar.text_input(
            "Zaggle Export Path",
            value="",
            help="Optional local CSV or JSON export path. If unavailable, the app will fall back to synthetic data."
        ).strip() or None
    sector = st.sidebar.selectbox(
        "Sector",
        ["saas", "retail", "healthcare", "manufacturing", "fintech", "logistics", "hospitality", "education"],
        index=0,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    business_scale = st.sidebar.selectbox(
        "Business Scale",
        ["small_business", "startup", "mid_market", "enterprise", "large_enterprise"],
        index=2,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    country = st.sidebar.selectbox(
        "Country",
        ["united_states", "india", "singapore", "united_kingdom", "uae", "germany"],
        index=0,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    company_market_capital = st.sidebar.slider(
        "Company Market Cap ($M)",
        50,
        2000,
        500,
        step=50
    )
    funding_round = st.sidebar.selectbox(
        "Funding Round",
        ["bootstrapped", "seed", "series_a", "series_b", "series_c", "public"],
        index=2,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    state_of_business = st.sidebar.selectbox(
        "State of Business",
        ["survival", "profit", "growth"],
        index=1,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    macro_environment = st.sidebar.selectbox(
        "Macro Environment",
        ["stable", "inflationary", "recessionary"],
        index=0,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    close_pressure = st.sidebar.selectbox(
        "Close Pressure",
        ["low", "medium", "high", "quarter_end"],
        index=1,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    automation_maturity = st.sidebar.selectbox(
        "Automation Maturity",
        ["low", "medium", "high"],
        index=1,
        format_func=lambda value: value.replace('_', ' ').title()
    )
    with st.sidebar.expander("Advanced Assumptions"):
        forecast_horizon_days = st.slider("Forecast Horizon (days)", 30, 120, 30, step=15)
        burn_shock_pct = st.slider("Burn Shock (%)", -20, 30, 0, step=5) / 100
        collections_delay_days = st.slider("Collections Delay (days)", 0, 30, 0, step=5)
        monte_carlo_sims = st.slider("Monte Carlo Sims", 100, 1000, 250, step=50)
        revenue_outlook_pct = st.slider("Revenue Outlook (%)", -20, 20, 0, step=5) / 100
        hiring_growth_pct = st.slider("Hiring Growth (%)", -10, 20, 0, step=5) / 100
        working_capital_efficiency = st.slider("Working Capital Efficiency (%)", 0, 20, 0, step=5) / 100
        capital_efficiency_score = st.slider("Capital Efficiency Score", 0, 100, 50, step=5)
        company_age_years = st.slider("Company Age (years)", 1, 30, 5, step=1)
    current_cash = st.sidebar.slider("Current Cash Balance", 50000, 1000000, 700000, step=10000)
    planning_assumptions = {
        "forecast_horizon_days": forecast_horizon_days,
        "burn_shock_pct": burn_shock_pct,
        "collections_delay_days": collections_delay_days,
        "monte_carlo_sims": monte_carlo_sims,
        "revenue_outlook_pct": revenue_outlook_pct,
        "hiring_growth_pct": hiring_growth_pct,
        "working_capital_efficiency": working_capital_efficiency,
        "capital_efficiency_score": capital_efficiency_score,
    }
    current_inputs = {
        "current_cash": current_cash,
        "sector": sector,
        "business_scale": business_scale,
        "country": country,
        "company_market_capital": company_market_capital,
        "funding_round": funding_round,
        "state_of_business": state_of_business,
        "company_age_years": company_age_years,
        "macro_environment": macro_environment,
        "close_pressure": close_pressure,
        "automation_maturity": automation_maturity,
        "data_source": data_source,
        "zaggle_export_path": zaggle_export_path,
        "planning_assumptions": planning_assumptions,
    }
    
    if st.sidebar.button("▶ Run Analysis", key="run_button", type="primary"):
        orchestrator = build_orchestrator(
            current_cash=current_cash,
            sector=sector,
            business_scale=business_scale,
            country=country,
            company_market_capital=company_market_capital,
            funding_round=funding_round,
            state_of_business=state_of_business,
            company_age_years=company_age_years,
            macro_environment=macro_environment,
            close_pressure=close_pressure,
            planning_assumptions=planning_assumptions,
            automation_maturity=automation_maturity,
            data_source=data_source,
            zaggle_export_path=zaggle_export_path,
        )
        result = orchestrator.run_analysis(days=90)
        st.session_state.result = result
        st.session_state.current_screen = "dashboard"
    
    # Screen navigation
    if "result" not in st.session_state:
        st.info("👈 Click **Run Analysis** to begin the AI CFO analysis pipeline.")
        st.markdown("""
        ### About This System
        
        The **AI-Native CFO Operating System** is a production-grade financial decision engine with:
        
        - **Spend Intelligence Agent**: Detects spending anomalies using machine learning
        - **Cashflow Forecast Agent**: Projects liquidity risks and runway
        - **Decision Agent**: Simulates multiple actions and recommends optimal path
        - **Narrative Agent**: Generates executive-level briefings
        - **FP&A Workbench**: Tracks plan variance, budget performance, and scenario outcomes
        - **Compliance & Close**: Flags exceptions and supports close-readiness review
        - **Strategic Planning**: Links planning assumptions to finance outcomes and recommended actions
        - **Overview / Architecture / Impact**: Summarizes the CFO-OS concept and expected value
        
        Choose a sector, business scale, macro environment, and current cash balance, then click **Run Analysis** to see the system in action.
        """)
        return
    
    previous_result = st.session_state.result
    previous_inputs = {
        "current_cash": previous_result.get("current_cash"),
        "sector": previous_result.get("sector"),
        "business_scale": previous_result.get("business_scale"),
        "country": previous_result.get("country"),
        "company_market_capital": previous_result.get("company_market_capital", previous_result.get("country_market_capital")),
        "funding_round": previous_result.get("funding_round"),
        "state_of_business": previous_result.get("state_of_business"),
        "company_age_years": previous_result.get("company_age_years"),
        "macro_environment": previous_result.get("macro_environment"),
        "close_pressure": previous_result.get("close_pressure"),
        "automation_maturity": previous_result.get("automation_maturity"),
        "data_source": previous_result.get("data_source"),
        "zaggle_export_path": previous_result.get("zaggle_export_path"),
        "planning_assumptions": previous_result.get("planning_assumptions"),
    }
    if previous_inputs != current_inputs:
        orchestrator = build_orchestrator(
            current_cash=current_cash,
            sector=sector,
            business_scale=business_scale,
            country=country,
            company_market_capital=company_market_capital,
            funding_round=funding_round,
            state_of_business=state_of_business,
            company_age_years=company_age_years,
            macro_environment=macro_environment,
            close_pressure=close_pressure,
            planning_assumptions=planning_assumptions,
            automation_maturity=automation_maturity,
            data_source=data_source,
            zaggle_export_path=zaggle_export_path,
        )
        st.session_state.result = orchestrator.run_analysis(days=90)

    result = st.session_state.result
    
    # Screen tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🚨 Alert Dashboard",
        "🤖 Agent Reasoning",
        "📋 CFO Briefing",
        "📐 FP&A Workbench",
        "🧭 Overview",
        "🧾 Compliance & Close",
        "🗺️ Strategic Planning"
    ])
    
    with tab1:
        screen_1_alert_dashboard(result)
    
    with tab2:
        screen_2_agent_reasoning(result)
    
    with tab3:
        screen_3_cfo_briefing(result)

    with tab4:
        screen_4_fpa_workbench(result)

    with tab5:
        screen_5_solution_overview()

    with tab6:
        screen_6_compliance_close(result)

    with tab7:
        screen_7_strategic_planning(result)
    
    # Footer
    st.divider()
    st.markdown("*AI-Native CFO Operating System v1.0 | Production-grade financial intelligence*")


if __name__ == "__main__":
    main()
