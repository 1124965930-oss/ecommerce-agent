"""Recon Tab — competitor monitoring and strategy insights."""

import streamlit as st
import pandas as pd


def render(orch):
    orch.initialize()

    st.subheader("Competitor Intelligence")

    # Product selector
    products = orch.db.fetch_all("SELECT id, asin, title, our_price FROM products")
    product_options = {f"{p['title']} (${p['our_price']:.2f})": p["id"] for p in products}
    selected = st.selectbox("Select Product", list(product_options.keys()))
    pid = product_options[selected]

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Scrape Competitors Now", type="primary"):
            with st.spinner("Scraping competitor data..."):
                result = orch.run_recon([pid])
                st.success(f"Done — {result['new_listings']} listings, {result['insights_generated']} insights")
    with col2:
        if st.button("Run Full Recon (All Products)"):
            with st.spinner("Running reconnaissance..."):
                result = orch.run_recon()
                st.success(f"Scanned {result['products_scanned']} products, "
                           f"generated {result['insights_generated']} insights")

    st.markdown("---")

    # Competitor comparison
    st.subheader("Competitor Price Comparison")
    comps = orch.db.fetch_all(
        "SELECT competitor_name, price, rating, review_count, stock_status, scraped_at "
        "FROM competitor_listings WHERE product_id=? ORDER BY scraped_at DESC LIMIT 4",
        (pid,),
    )

    product = orch.db.fetch_one("SELECT our_price FROM products WHERE id=?", (pid,))

    if comps:
        df = pd.DataFrame(comps)
        df.columns = ["Competitor", "Price", "Rating", "Reviews", "Stock", "Last Scraped"]

        def color_price(val):
            if product and product["our_price"]:
                gap = (val - product["our_price"]) / product["our_price"]
                if gap < -0.05:
                    return "background-color: rgba(239, 68, 68, 0.2)"
                elif gap > 0.05:
                    return "background-color: rgba(34, 197, 94, 0.2)"
            return ""

        styled = df.style.map(color_price, subset=["Price"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Price bar chart
        import plotly.graph_objects as go
        names = [c["Competitor"] for c in comps] + ["Our Price"]
        prices = [c["Price"] for c in comps] + [product["our_price"]]
        colors = ["#60a5fa"] * len(comps) + ["#f59e0b"]

        fig = go.Figure(data=[
            go.Bar(x=names, y=prices, marker_color=colors, text=[f"${p:.2f}" for p in prices],
                   textposition="outside")
        ])
        fig.update_layout(margin=dict(t=10, b=0), height=350,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No competitor data yet. Click 'Scrape Competitors Now'.")

    st.markdown("---")

    # Strategy Insights
    st.subheader("Strategy Insights")
    insights = orch.db.fetch_all(
        "SELECT * FROM strategy_insights WHERE product_id=? AND actionable=1 "
        "ORDER BY severity DESC, created_at DESC",
        (pid,),
    )
    if insights:
        for ins in insights:
            sev_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
            color = sev_color.get(ins["severity"], "#888")
            with st.expander(f"{ins['severity'].upper()} | {ins['title']}"):
                st.markdown(f"**Type:** {ins['insight_type']}")
                st.markdown(f"**Description:** {ins['description']}")
                st.markdown(f"**Created:** {ins['created_at']}")
                if st.button("Mark as Acted", key=f"act_{ins['id']}"):
                    orch.db.execute(
                        "UPDATE strategy_insights SET acted_upon=1 WHERE id=?",
                        (ins["id"],),
                    )
                    st.rerun()
    else:
        st.info("No active insights for this product.")
