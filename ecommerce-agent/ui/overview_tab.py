"""Overview tab — high-level KPIs, recent insights, price trends."""

import streamlit as st
import pandas as pd
from config import MOCK_PRODUCTS


def render(orch):
    orch.initialize()

    # ---- KPI Cards ----
    stats = orch.get_overview_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Products", stats["products"])
    c2.metric("Avg Price Gap", f"{stats['avg_price_gap']:+.1f}%")
    c3.metric("Sentiment Score", f"{stats['sentiment_score']:.0f}%", delta=None)
    c4.metric("Pending Decisions", stats["pending_decisions"])
    c5.metric("Active Insights", stats["active_insights"])

    st.markdown("---")

    # ---- Recent Insights ----
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.subheader("Recent Strategy Insights")
        insights = orch.db.fetch_all(
            "SELECT si.title, si.severity, si.insight_type, si.description, p.title as product, "
            "si.created_at FROM strategy_insights si "
            "LEFT JOIN products p ON p.id=si.product_id "
            "ORDER BY si.created_at DESC LIMIT 8"
        )
        if insights:
            df = pd.DataFrame(insights)
            df.columns = ["Title", "Severity", "Type", "Description", "Product", "Time"]
            severity_map = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            df["S"] = df["Severity"].map(severity_map)
            st.dataframe(
                df[["S", "Title", "Type", "Product", "Time"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "S": st.column_config.TextColumn("", width="small"),
                },
            )
        else:
            st.info("No insights yet. Click 'Run All Agents' to generate insights.")

    with col_b:
        st.subheader("Sentiment Overview")
        sentiment_data = orch.db.fetch_all(
            "SELECT sentiment_label, COUNT(*) as cnt FROM reviews "
            "WHERE sentiment_label IS NOT NULL GROUP BY sentiment_label"
        )
        if sentiment_data:
            import plotly.express as px
            df_s = pd.DataFrame(sentiment_data)
            fig = px.pie(df_s, values="cnt", names="sentiment_label",
                         color="sentiment_label",
                         color_discrete_map={"positive": "#22c55e", "neutral": "#f59e0b", "negative": "#ef4444"},
                         hole=0.5)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=280,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ---- Price Trend ----
    st.subheader("Price Trend (Last 14 Days)")
    products = orch.db.fetch_all("SELECT id, title, our_price FROM products")
    price_data = []
    for p in products:
        comps = orch.db.fetch_all(
            "SELECT AVG(price) as avg_comp, DATE(scraped_at) as day "
            "FROM competitor_listings WHERE product_id=? "
            "GROUP BY DATE(scraped_at) ORDER BY day DESC LIMIT 14",
            (p["id"],),
        )
        for c in comps:
            price_data.append({
                "Product": p["title"][:25] + "...",
                "Day": c["day"],
                "Competitor Avg": c["avg_comp"],
                "Our Price": p["our_price"],
            })

    if price_data:
        import plotly.express as px
        df_price = pd.DataFrame(price_data)
        fig = px.line(df_price, x="Day", y=["Competitor Avg", "Our Price"], color="Product",
                       line_dash="Product", markers=False)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=350,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # ---- Recent Agent Runs ----
    st.subheader("Recent Agent Runs")
    runs = orch.db.fetch_all(
        "SELECT agent_name, status, input_summary, output_summary, duration_ms, created_at "
        "FROM agent_runs ORDER BY created_at DESC LIMIT 10"
    )
    if runs:
        df_runs = pd.DataFrame(runs)
        df_runs.columns = ["Agent", "Status", "Input", "Output", "Duration(ms)", "Time"]
        status_icons = {"completed": "✅", "failed": "❌", "running": "⏳"}
        df_runs["S"] = df_runs["Status"].map(status_icons)
        st.dataframe(
            df_runs[["S", "Agent", "Status", "Duration(ms)", "Time"]],
            use_container_width=True, hide_index=True,
        )
