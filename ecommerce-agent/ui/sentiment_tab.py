"""Sentiment Tab — review analysis, issue tracking, reply generation."""

import streamlit as st
import pandas as pd
from collections import Counter


def render(orch):
    orch.initialize()

    st.subheader("Review Sentiment Analysis")

    # Product selector
    products = orch.db.fetch_all("SELECT id, title FROM products")
    product_options = {p["title"]: p["id"] for p in products}
    selected = st.selectbox("Select Product", list(product_options.keys()))
    pid = product_options[selected]

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Analyze Reviews Now", type="primary"):
            with st.spinner("Analyzing sentiment..."):
                result = orch.sentiment.analyze_product_reviews(pid)
                st.success(f"Processed {result['reviews_processed']} reviews")
    with col2:
        if st.button("Run Full Sentiment (All Products)"):
            with st.spinner("Running sentiment analysis..."):
                result = orch.run_sentiment()
                st.success(f"Processed {result['reviews_processed']} reviews across "
                           f"{result['products_analyzed']} products")

    st.markdown("---")

    # Sentiment statistics
    stats = orch.db.fetch_one(
        "SELECT COUNT(*) as total, "
        "SUM(CASE WHEN sentiment_label='positive' THEN 1 ELSE 0 END) as pos, "
        "SUM(CASE WHEN sentiment_label='negative' THEN 1 ELSE 0 END) as neg, "
        "SUM(CASE WHEN sentiment_label='neutral' THEN 1 ELSE 0 END) as neu, "
        "AVG(sentiment_score) as avg_score "
        "FROM reviews WHERE product_id=? AND sentiment_label IS NOT NULL",
        (pid,),
    )

    if stats and stats["total"] > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Reviews", stats["total"])
        c2.metric("Positive", stats["pos"] or 0)
        c3.metric("Negative", stats["neg"] or 0)
        c4.metric("Avg Score", f"{(stats['avg_score'] or 0) * 100:.0f}%")

    st.markdown("---")

    # Top Issues
    st.subheader("Top Issues")
    issues = orch.sentiment.extract_top_issues(pid, top_n=10)
    if issues:
        import plotly.express as px
        df_issues = pd.DataFrame(issues, columns=["Issue", "Count"])
        fig = px.bar(df_issues, x="Count", y="Issue", orientation="h",
                     color="Count", color_continuous_scale="Reds")
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No issues extracted yet.")

    st.markdown("---")

    # Review list
    st.subheader("Recent Reviews")
    sentiment_filter = st.selectbox("Filter by sentiment", ["All", "Positive", "Negative", "Neutral"])
    where = "WHERE product_id=?"
    params = [pid]
    if sentiment_filter != "All":
        where += " AND sentiment_label=?"
        params.append(sentiment_filter.lower())

    reviews = orch.db.fetch_all(
        f"SELECT rating, title, body, sentiment_label, sentiment_score, key_issues, posted_at "
        f"FROM reviews {where} ORDER BY posted_at DESC LIMIT 20",
        tuple(params),
    )

    if reviews:
        for r in reviews[:8]:
            emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(r["sentiment_label"], "❓")
            with st.expander(f"{emoji} [{r['rating']}★] {r['title'] or 'No title'} — Score: {(r['sentiment_score'] or 0)*100:.0f}%"):
                st.markdown(f"**Review:** {r['body']}")
                if r["key_issues"]:
                    st.markdown(f"**Issues detected:** {r['key_issues']}")
                st.caption(f"Posted: {r['posted_at']}")

                if st.button("Generate Reply", key=f"reply_{r['title']}_{r['posted_at']}"):
                    reply = orch.sentiment.generate_reply(r["body"])
                    st.text_area("Suggested Reply", reply, height=100)
    else:
        st.info("No reviews found.")
