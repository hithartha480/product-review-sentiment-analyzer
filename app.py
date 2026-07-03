import streamlit as st
import pandas as pd
import altair as alt
from sentiment_pipeline import analyze_reviews_from_dataframe

st.set_page_config(
    page_title="Product Review Sentiment & Aspect Analyzer",
    page_icon="📊",
    layout="wide"
)
def style_table(df, highlight_col=None):
    styler = df.style.set_properties(**{
        "background-color": "#0b1220",
        "color": "#e5e7eb",
        "border-color": "rgba(148, 163, 184, 0.12)"
    })

    styler = styler.set_table_styles([
        {
            "selector": "th",
            "props": [
                ("background-color", "#111827"),
                ("color", "#cbd5e1"),
                ("font-weight", "600"),
                ("border", "1px solid rgba(148, 163, 184, 0.12)")
            ]
        },
        {
            "selector": "td",
            "props": [
                ("border", "1px solid rgba(148, 163, 184, 0.08)")
            ]
        }
    ])

    if highlight_col and highlight_col in df.columns:
        styler = styler.background_gradient(
            subset=[highlight_col],
            cmap="Blues"
        )

    return styler

st.markdown("""
<style>
.block-container {
    max-width: 1160px;
    padding-top: 1.2rem;
    padding-bottom: 1.4rem;
}

.hero-card {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 18px;
    padding: 22px 24px 18px 24px;
    margin-bottom: 0.9rem;
    display: block;
}

.hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.3rem;
    display: block;
}

.hero-subtitle {
    font-size: 0.96rem;
    color: #cbd5e1;
    line-height: 1.65;
    max-width: 760px;
    display: block;
}

.upload-note {
    color: #94a3b8;
    font-size: 0.88rem;
    margin-top: 0.2rem;
    margin-bottom: 0.75rem;
}

.section-title {
    font-size: 1.08rem;
    font-weight: 650;
    margin-top: 0.2rem;
    margin-bottom: 0.55rem;
}

div[data-testid="stMetric"] {
    background: #0b1220;
    border: 1px solid rgba(148, 163, 184, 0.10);
    padding: 14px;
    border-radius: 14px;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.82rem;
}

div[data-testid="stMetricValue"] {
    font-size: 1.75rem;
}

.insight-box {
    background: #0b1220;
    border: 1px solid rgba(59, 130, 246, 0.16);
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 8px;
    color: #dbeafe;
}

.insight-card {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(11, 18, 32, 0.98));
    border: 1px solid rgba(59, 130, 246, 0.14);
    border-radius: 16px;
    padding: 14px 16px;
    min-height: 108px;
}

.insight-label {
    font-size: 0.78rem;
    color: #93C5FD;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}

.insight-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.45;
}

.insight-subtext {
    margin-top: 6px;
    color: #94A3B8;
    font-size: 0.86rem;
    line-height: 1.45;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.14);
    padding-bottom: 4px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 10px 10px 0 0;
    padding: 10px 16px 9px 16px;
    color: #cbd5e1;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: rgba(30, 41, 59, 0.92);
    color: #f8fafc !important;
    border: 1px solid rgba(59, 130, 246, 0.28);
    box-shadow: inset 0 -2px 0 #3b82f6;
}

.stTabs [data-baseweb="tab"] p {
    font-size: 0.95rem;
}

hr {
    margin-top: 0.9rem !important;
    margin-bottom: 0.9rem !important;
}

.stSelectbox, .stTextInput, .stFileUploader {
    margin-bottom: 0.35rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-card">
    <div class="hero-title">Product Review Sentiment & Aspect Analyzer</div>
    <div class="hero-subtitle">
        Analyze customer reviews to identify sentiment trends, grouped complaint themes,
        product-level patterns, and practical business insights from textual feedback.
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload review dataset", type=["csv"])
st.markdown(
    '<div class="upload-note">Upload a CSV file containing product_name, review, and rating columns.</div>',
    unsafe_allow_html=True
)

if uploaded_file is None:
    st.info("Upload a review dataset to begin sentiment and aspect analysis.")
else:
    raw_df = pd.read_csv(uploaded_file)
    required_columns = {"product_name", "review", "rating"}

    if not required_columns.issubset(raw_df.columns):
        st.error("CSV must contain these columns: product_name, review, rating")
    else:
        results = analyze_reviews_from_dataframe(raw_df)
        analyzed_df = results["analyzed_df"]
        product_summary_df = results["product_summary"]
        business_insights = results.get("business_insights", [])
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            product_options = ["All"] + sorted(analyzed_df["product_name"].dropna().unique().tolist())
            selected_product = st.selectbox("Product", product_options)
        with filter_col2:
            sentiment_filter = st.selectbox("Sentiment", ["All", "positive", "neutral", "negative"])
        filtered_df = analyzed_df.copy()
        if selected_product != "All":
            filtered_df = filtered_df[filtered_df["product_name"] == selected_product]
        if sentiment_filter != "All":
            filtered_df = filtered_df[filtered_df["sentiment"] == sentiment_filter]
        filtered_sentiment_counts = filtered_df["sentiment"].value_counts()
        total_reviews = len(filtered_df)
        positive_count = int(filtered_sentiment_counts.get("positive", 0))
        negative_count = int(filtered_sentiment_counts.get("negative", 0))
        neutral_count = int(filtered_sentiment_counts.get("neutral", 0))
        avg_rating = round(filtered_df["rating"].mean(), 2) if total_reviews > 0 else 0
        avg_confidence = round(filtered_df["confidence"].mean(), 3) if total_reviews > 0 else 0
        st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Total Reviews", total_reviews)
        with m2:
            st.metric("Positive", positive_count)
        with m3:
            st.metric("Negative", negative_count)
        with m4:
            st.metric("Neutral", neutral_count)
        with m5:
            st.metric("Avg Rating", avg_rating)
        st.caption(f"Average confidence score: {avg_confidence}")
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Sentiment Overview", "Aspect Insights", "Business Insights", "Review Explorer"]
        )
        with tab1:
            col1, col2 = st.columns([1.2, 1])
            with col1:
                st.markdown('<div class="section-title">Sentiment Distribution</div>', unsafe_allow_html=True)
                chart_df = filtered_df["sentiment"].value_counts().reset_index()
                chart_df.columns = ["Sentiment", "Count"]
                if not chart_df.empty:
                    sentiment_order = ["positive", "neutral", "negative"]
                    chart = (
                        alt.Chart(chart_df)
                        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                        .encode(
                            x=alt.X(
                                "Sentiment:N",
                                sort=sentiment_order,
                                axis=alt.Axis(title=None, labelColor="#CBD5E1", labelFontSize=13)
                            ),
                            y=alt.Y(
                                "Count:Q",
                                axis=alt.Axis(
                                    title=None,
                                    gridColor="#1F2937",
                                    labelColor="#CBD5E1",
                                    labelFontSize=12
                                )
                            ),
                            color=alt.Color(
                                "Sentiment:N",
                                scale=alt.Scale(
                                    domain=["positive", "neutral", "negative"],
                                    range=["#22C55E", "#F59E0B", "#EF4444"]
                                ),
                                legend=None
                            ),
                            tooltip=["Sentiment", "Count"]
                        )
                        .properties(height=320)
                        .configure_view(strokeWidth=0)
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No chart data available for the current selection.")
            with col2:
                st.markdown('<div class="section-title">Sentiment Breakdown</div>', unsafe_allow_html=True)
                breakdown_df = filtered_df["sentiment"].value_counts().reset_index()
                breakdown_df.columns = ["Sentiment", "Count"]
                if not breakdown_df.empty:
                    st.table(style_table(breakdown_df, highlight_col="Count"))
                else:
                    st.info("No sentiment breakdown available.")
            st.markdown('<div class="section-title">Product-wise Summary</div>', unsafe_allow_html=True)
            display_product_summary = product_summary_df.copy()
            if selected_product != "All":
                display_product_summary = display_product_summary[
                    display_product_summary["product_name"] == selected_product
                ]
            if sentiment_filter != "All":
                display_product_summary = display_product_summary[
                    display_product_summary["sentiment"] == sentiment_filter
                ]
            if not display_product_summary.empty:
                total_products = display_product_summary["product_name"].nunique()
                top_positive_product = (
                    display_product_summary[display_product_summary["sentiment"] == "positive"]
                    .sort_values(by="Count", ascending=False)
                )
                top_negative_product = (
                    display_product_summary[display_product_summary["sentiment"] == "negative"]
                    .sort_values(by="Count", ascending=False)
                )
                top_positive_name = top_positive_product.iloc[0]["product_name"] if not top_positive_product.empty else "N/A"
                top_positive_value = int(top_positive_product.iloc[0]["Count"]) if not top_positive_product.empty else 0
                top_negative_name = top_negative_product.iloc[0]["product_name"] if not top_negative_product.empty else "N/A"
                top_negative_value = int(top_negative_product.iloc[0]["Count"]) if not top_negative_product.empty else 0
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Products Shown", total_products)
                with c2:
                    st.metric("Highest Positive Mentions", top_positive_name, delta=top_positive_value)
                with c3:
                    st.metric("Highest Negative Mentions", top_negative_name, delta=top_negative_value)
                summary_chart = (
                    alt.Chart(display_product_summary)
                    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                    .encode(
                        x=alt.X(
                            "product_name:N",
                            title=None,
                            axis=alt.Axis(labelAngle=0, labelColor="#CBD5E1", labelFontSize=12)
                        ),
                        xOffset=alt.XOffset("sentiment:N"),
                        y=alt.Y(
                            "Count:Q",
                            title=None,
                            axis=alt.Axis(gridColor="#1F2937", labelColor="#CBD5E1", labelFontSize=12)
                        ),
                        color=alt.Color(
                            "sentiment:N",
                            scale=alt.Scale(
                                domain=["positive", "neutral", "negative"],
                                range=["#22C55E", "#F59E0B", "#EF4444"]
                            ),
                            legend=alt.Legend(
                                orient="top",
                                title=None,
                                labelColor="#CBD5E1"
                            )
                        ),
                        tooltip=["product_name", "sentiment", "Count"]
                    )
                    .properties(height=340)
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(summary_chart, use_container_width=True)
            else:
                st.info("No product-wise summary available for the current selection.")
        with tab2:
            filtered_positive_aspects = []
            filtered_negative_aspects = []
            for _, row in filtered_df.iterrows():
                for aspect in row["aspect_groups"]:
                    if row["sentiment"] == "positive":
                        filtered_positive_aspects.append(aspect)
                    elif row["sentiment"] == "negative":
                        filtered_negative_aspects.append(aspect)
            pos_df = pd.DataFrame(pd.Series(filtered_positive_aspects).value_counts()).reset_index()
            if not pos_df.empty:
                pos_df.columns = ["Aspect", "Count"]
            else:
                pos_df = pd.DataFrame(columns=["Aspect", "Count"])
            neg_df = pd.DataFrame(pd.Series(filtered_negative_aspects).value_counts()).reset_index()
            if not neg_df.empty:
                neg_df.columns = ["Aspect", "Count"]
            else:
                neg_df = pd.DataFrame(columns=["Aspect", "Count"])
            col3, col4 = st.columns(2)
            with col3:
                st.markdown('<div class="section-title">Positive Aspects</div>', unsafe_allow_html=True)
                if not pos_df.empty:
                    st.table(style_table(pos_df, highlight_col="Count"))
                else:
                    st.info("No positive aspects found for the current selection.")
            with col4:
                st.markdown('<div class="section-title">Negative Aspects</div>', unsafe_allow_html=True)
                if not neg_df.empty:
                    st.table(style_table(neg_df, highlight_col="Count"))
                else:
                    st.info("No negative aspects found for the current selection.")
        with tab3:
            st.markdown('<div class="section-title">Generated Business Insights</div>', unsafe_allow_html=True)
            pos_aspects = results.get("positive_aspects", pd.DataFrame(columns=["Aspect", "Count"]))
            neg_aspects = results.get("negative_aspects", pd.DataFrame(columns=["Aspect", "Count"]))
            top_strength = pos_aspects.iloc[0]["Aspect"] if not pos_aspects.empty else "Not enough data"
            top_strength_count = int(pos_aspects.iloc[0]["Count"]) if not pos_aspects.empty else 0
            top_concern = neg_aspects.iloc[0]["Aspect"] if not neg_aspects.empty else "Not enough data"
            top_concern_count = int(neg_aspects.iloc[0]["Count"]) if not neg_aspects.empty else 0
            most_positive_product_df = (
                product_summary_df[product_summary_df["sentiment"] == "positive"]
                .sort_values(by="Count", ascending=False)
            )
            most_negative_product_df = (
                product_summary_df[product_summary_df["sentiment"] == "negative"]
                .sort_values(by="Count", ascending=False)
            )
            most_positive_product = (
                most_positive_product_df.iloc[0]["product_name"]
                if not most_positive_product_df.empty else "Not enough data"
            )
            most_positive_value = (
                int(most_positive_product_df.iloc[0]["Count"])
                if not most_positive_product_df.empty else 0
            )
            most_negative_product = (
                most_negative_product_df.iloc[0]["product_name"]
                if not most_negative_product_df.empty else "Not enough data"
            )
            most_negative_value = (
                int(most_negative_product_df.iloc[0]["Count"])
                if not most_negative_product_df.empty else 0
            )
            avg_conf_display = round(filtered_df["confidence"].mean(), 3) if not filtered_df.empty else 0
            i1, i2 = st.columns(2)
            i3, i4 = st.columns(2)
            with i1:
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div class="insight-label">Top Strength</div>
                        <div class="insight-value">{top_strength}</div>
                        <div class="insight-subtext">Mentioned positively in {top_strength_count} review(s).</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with i2:
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div class="insight-label">Top Concern</div>
                        <div class="insight-value">{top_concern}</div>
                        <div class="insight-subtext">Mentioned negatively in {top_concern_count} review(s).</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with i3:
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div class="insight-label">Most Positive Product</div>
                        <div class="insight-value">{most_positive_product}</div>
                        <div class="insight-subtext">{most_positive_value} positive review(s) in the current dataset.</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with i4:
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div class="insight-label">Most Negative Product</div>
                        <div class="insight-value">{most_negative_product}</div>
                        <div class="insight-subtext">{most_negative_value} negative review(s) in the current dataset.</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Average Confidence Score", avg_conf_display)
            st.markdown("<br>", unsafe_allow_html=True)
            if business_insights:
                st.markdown('<div class="section-title">Narrative Insights</div>', unsafe_allow_html=True)
                for insight in business_insights:
                    st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
            with st.expander("Model Notes"):
                st.write(
                    "This dashboard uses a hybrid sentiment strategy that combines review text sentiment, "
                    "keyword signals, and rating information to produce sentiment labels and confidence scores."
                )
        with tab4:
            st.markdown('<div class="section-title">Review Explorer</div>', unsafe_allow_html=True)
            search_text = st.text_input("Search reviews")
            display_df = filtered_df.copy()
            if search_text.strip():
                display_df = display_df[
                    display_df["review"].str.contains(search_text, case=False, na=False)
                ]
            review_view = display_df[
                [
                    "product_name",
                    "review",
                    "rating",
                    "sentiment",
                    "confidence",
                    "aspect_groups"
                ]
            ].copy()
            st.dataframe(review_view, use_container_width=True, hide_index=True)
            csv_data = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download analyzed data",
                data=csv_data,
                file_name="analyzed_reviews.csv",
                mime="text/csv"
            )