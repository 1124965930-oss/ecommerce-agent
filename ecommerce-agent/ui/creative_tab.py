"""Creative Tab — content generation gallery, product images, A/B variants."""

import streamlit as st
import pandas as pd
import os


def render(orch):
    orch.initialize()

    st.subheader("AI Content & Creative Studio")

    # Product selector
    products = orch.db.fetch_all("SELECT id, title, market FROM products")
    product_options = {p["title"]: p["id"] for p in products}
    selected = st.selectbox("Select Product", list(product_options.keys()))
    pid = product_options[selected]

    product = orch.db.fetch_one("SELECT * FROM products WHERE id=?", (pid,))

    # --- Generation Controls ---
    st.markdown("### Generate New Content")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        content_types = st.multiselect(
            "Content Types",
            ["listing_copy", "a_plus", "social_post", "ad_copy", "detail_image"],
            default=["listing_copy", "ad_copy"],
            format_func=lambda x: {
                "listing_copy": "Listing Copy", "a_plus": "A+ Content",
                "social_post": "Social Post", "ad_copy": "Ad Copy",
                "detail_image": "Product Image",
            }.get(x, x),
        )
    with c2:
        tone = st.select_slider(
            "Tone", options=["professional", "persuasive", "casual", "urgent", "luxury"]
        )
    with c3:
        trigger = st.selectbox(
            "Trigger", ["scheduled", "price_drop", "trend_detected", "sentiment_alert"]
        )

    if st.button("Generate Content", type="primary"):
        with st.spinner("Generating content..."):
            for ct in content_types:
                if ct == "detail_image":
                    orch.creative.run(pid, trigger, tone)
                else:
                    orch.creative.run(pid, trigger, tone)
            st.success(f"Generated {len(content_types)} content items")
            st.rerun()

    st.markdown("---")

    # --- Content Gallery ---
    st.subheader("Generated Content Gallery")

    filter_type = st.selectbox(
        "Filter by type",
        ["All", "listing_copy", "a_plus", "social_post", "ad_copy", "detail_image"],
        format_func=lambda x: "All Types" if x == "All" else {
            "listing_copy": "Listing Copy", "a_plus": "A+ Content",
            "social_post": "Social Post", "ad_copy": "Ad Copy",
            "detail_image": "Product Image",
        }.get(x, x),
    )

    where = "WHERE product_id=?"
    params = [pid]
    if filter_type != "All":
        where += " AND content_type=?"
        params.append(filter_type)

    contents = orch.db.fetch_all(
        f"SELECT * FROM generated_content {where} ORDER BY created_at DESC LIMIT 12",
        tuple(params),
    )

    if contents:
        for i, c in enumerate(contents):
            with st.expander(
                f"{c['content_type'].replace('_', ' ').title()} | "
                f"{c.get('variant_name', 'v1')} | {c['created_at']}"
            ):
                if c["content_type"] == "detail_image" and c["image_path"]:
                    if os.path.exists(c["image_path"]):
                        st.image(c["image_path"], width=500)
                    else:
                        st.caption(f"Image: {c['image_path']}")
                elif c["content_text"]:
                    st.markdown(c["content_text"])

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.selectbox("Status", ["draft", "published", "archived"],
                                 index=["draft", "published", "archived"].index(c.get("status", "draft")),
                                 key=f"status_{c['id']}")
                with col_b:
                    if st.button("Regenerate", key=f"regen_{c['id']}"):
                        orch.creative.run(pid, trigger, tone)
                        st.rerun()
    else:
        st.info("No content generated yet. Select types and click 'Generate Content'.")
