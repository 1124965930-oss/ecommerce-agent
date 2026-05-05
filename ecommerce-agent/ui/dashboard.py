"""Dashboard router — sidebar navigation and tab selection."""

import streamlit as st
from ui.overview_tab import render as render_overview
from ui.recon_tab import render as render_recon
from ui.sentiment_tab import render as render_sentiment
from ui.creative_tab import render as render_creative
from ui.pricing_tab import render as render_pricing


def render_sidebar(orch) -> str:
    st.sidebar.title("Marketing AI Hub")
    st.sidebar.caption("Multi-Agent E-Commerce")

    tabs = {
        "Overview": "📊",
        "Recon": "🔍",
        "Sentiment": "💬",
        "Creative": "🎨",
        "Pricing": "💰",
    }

    page = st.sidebar.radio(
        "Navigation",
        list(tabs.keys()),
        format_func=lambda x: f"{tabs[x]} {x}",
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")

    # Agent status indicators
    st.sidebar.markdown("**Agent Status**")
    for agent_name in ["recon", "sentiment", "creative", "pricing"]:
        last_run = orch.db.fetch_one(
            "SELECT status, created_at FROM agent_runs WHERE agent_name=? "
            "ORDER BY created_at DESC LIMIT 1",
            (agent_name,),
        )
        if last_run:
            icon = "🟢" if last_run["status"] == "completed" else "🔴"
            st.sidebar.caption(f"{icon} {agent_name.title()}: {last_run['created_at'][:16]}")
        else:
            st.sidebar.caption(f"⚪ {agent_name.title()}: Not run yet")

    st.sidebar.markdown("---")

    if st.sidebar.button("Run All Agents", type="primary", use_container_width=True):
        with st.spinner("Running full pipeline..."):
            results = orch.run_all()
            st.sidebar.success(
                f"Done in {results['total_duration_ms']}ms\n\n"
                f"Recon: {results['recon']['products_scanned']} products\n"
                f"Sentiment: {results['sentiment']['reviews_processed']} reviews\n"
                f"Pricing: {results['pricing']['decisions']} decisions\n"
                f"Creative: {len(results['creative'])} generated"
            )

    return page


def render(orch):
    page = render_sidebar(orch)

    st.title(page)
    st.markdown("---")

    if page == "Overview":
        render_overview(orch)
    elif page == "Recon":
        render_recon(orch)
    elif page == "Sentiment":
        render_sentiment(orch)
    elif page == "Creative":
        render_creative(orch)
    elif page == "Pricing":
        render_pricing(orch)
