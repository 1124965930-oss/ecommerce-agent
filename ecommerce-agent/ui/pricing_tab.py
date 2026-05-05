"""Pricing Tab — dynamic pricing, ad bid optimization, margin simulation."""

import streamlit as st
import pandas as pd


def render(orch):
    orch.initialize()

    st.subheader("Dynamic Pricing & Bidding")

    # Product selector
    products = orch.db.fetch_all("SELECT * FROM products")
    product_options = {f"{p['title']} (${p['our_price']:.2f})": p["id"] for p in products}
    selected = st.selectbox("Select Product", list(product_options.keys()))
    pid = product_options[selected]

    product = orch.db.fetch_one("SELECT * FROM products WHERE id=?", (pid,))

    # Current status
    margin = (product["our_price"] - product["cost"]) / product["our_price"] * 100
    st.markdown("### Current Status")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price", f"${product['our_price']:.2f}")
    c2.metric("Cost", f"${product['cost']:.2f}")
    c3.metric("Margin", f"{margin:.1f}%")
    c4.metric("Ad Bid", f"${product['current_bid']:.2f}")
    c5.metric("Target ACOS", f"{product['target_acos']*100:.0f}%")

    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Calculate Optimal Price & Bid", type="primary"):
            with st.spinner("Analyzing market data..."):
                price_decision = orch.pricing.calculate_optimal_price(pid)
                bid_decision = orch.pricing.optimize_ad_bid(pid)

                st.markdown("### Recommendations")
                rc1, rc2 = st.columns(2)
                with rc1:
                    delta = price_decision["price"] - product["our_price"]
                    st.metric(
                        "Optimal Price",
                        f"${price_decision['price']:.2f}",
                        delta=f"${delta:+.2f}",
                    )
                    st.caption(f"Margin impact: {price_decision['margin_delta']:+.1f}%")
                with rc2:
                    bid_delta = bid_decision["bid"] - product["current_bid"]
                    st.metric(
                        "Optimal Bid",
                        f"${bid_decision['bid']:.2f}",
                        delta=f"${bid_delta:+.2f}",
                    )
                    st.caption(f"Est. ACOS: {bid_decision['acos_estimate']:.1f}%")

                # Generate reasoning
                reasoning = orch.claude.generate_decision(
                    f"Product: {product['title']} | Current Price: ${product['our_price']:.2f} | "
                    f"Cost: ${product['cost']:.2f} | "
                    f"Suggested: ${price_decision['price']:.2f} | "
                    f"Margin delta: {price_decision['margin_delta']:+.1f}% | "
                    f"Market: {product.get('market', 'US')}",
                    ["Keep current", f"Change to ${price_decision['price']:.2f}", "Monitor 24h"],
                )
                st.info(f"**AI Reasoning:** {reasoning}")

    with col2:
        # Margin simulation
        st.markdown("### Margin Simulator")
        min_p = max(product["cost"] * 1.05, product["our_price"] * 0.7)
        max_p = product["our_price"] * 1.3
        sim_price = st.slider(
            "Simulated Price",
            min_value=float(round(min_p)),
            max_value=float(round(max_p)),
            value=float(product["our_price"]),
            step=0.5,
        )
        sim_result = orch.pricing.simulate_margin_impact(pid, sim_price)
        if sim_result:
            st.metric(
                "Simulated Margin",
                f"{sim_result['new_margin_pct']:.1f}%",
                delta=f"{sim_result['margin_delta']:+.1f}%",
            )

        # Margin curve
        import plotly.graph_objects as go
        prices_range = []
        margins_range = []
        for p_test in range(int(min_p), int(max_p) + 1):
            margins_range.append((p_test - product["cost"]) / p_test * 100)
            prices_range.append(p_test)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=prices_range, y=margins_range, mode="lines",
            fill="tozeroy", line=dict(color="#f59e0b", width=2),
            name="Margin Curve",
        ))
        fig.add_vline(x=product["our_price"], line_dash="dash", line_color="#ef4444",
                      annotation_text="Current")
        fig.add_vline(x=sim_price, line_dash="dash", line_color="#22c55e",
                      annotation_text="Simulated")
        fig.update_layout(
            xaxis_title="Price ($)", yaxis_title="Margin (%)",
            margin=dict(t=0, b=0, l=0, r=0), height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Decision history
    st.subheader("Pricing Decision History")
    decisions = orch.db.fetch_all(
        "SELECT old_price, new_price, old_bid, new_bid, reasoning, margin_impact_pct, "
        "applied, created_at FROM pricing_decisions WHERE product_id=? "
        "ORDER BY created_at DESC LIMIT 10",
        (pid,),
    )
    if decisions:
        df_d = pd.DataFrame(decisions)
        df_d.columns = ["Old Price", "New Price", "Old Bid", "New Bid", "Reasoning",
                        "Margin Impact", "Applied", "Time"]
        st.dataframe(df_d, use_container_width=True, hide_index=True)
    else:
        st.info("No pricing decisions yet.")
