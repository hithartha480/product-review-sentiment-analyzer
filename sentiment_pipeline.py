import re
from collections import Counter
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import TreebankWordTokenizer

VADER_READY = False
tokenizer = TreebankWordTokenizer()

ASPECT_GROUPS = {
    "fragrance": ["fragrance", "scent", "smell", "aroma"],
    "packaging": ["packaging", "package", "box", "bottle", "cap"],
    "delivery": ["delivery", "shipping", "late", "arrived", "courier"],
    "price": ["price", "expensive", "cheap", "cost", "value", "worth"],
    "texture": ["texture", "smooth", "sticky", "nonsticky", "soft"],
    "quality": ["quality", "premium", "durable", "poor", "good", "bad"],
    "skin": ["skin", "breakouts", "hydrated", "dry", "moisturized"],
    "hair": ["hair", "hairfall", "frizzy", "smooth", "dry"]
}

POSITIVE_HINTS = {
    "amazing", "great", "nice", "fresh", "worth", "beautiful", "premium",
    "soft", "hydrated", "smooth", "works", "good", "love", "best",
    "pleasant", "affordable", "clean", "effective"
}

NEGATIVE_HINTS = {
    "bad", "poor", "terrible", "late", "leaked", "disappointing",
    "expensive", "dry", "breakouts", "high", "stopped", "fades",
    "worst", "problem", "damaged", "sticky"
}


def setup_vader():
    global VADER_READY
    if not VADER_READY:
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon")
        VADER_READY = True


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_text(text):
    return tokenizer.tokenize(text)


def keyword_score(tokens):
    pos = sum(1 for token in tokens if token in POSITIVE_HINTS)
    neg = sum(1 for token in tokens if token in NEGATIVE_HINTS)
    return pos - neg


def hybrid_sentiment(row, analyzer):
    review = row["clean_review"]
    rating = float(row["rating"])

    vader_scores = analyzer.polarity_scores(review)
    vader_compound = vader_scores["compound"]

    tokens = tokenize_text(review)
    kw_score = keyword_score(tokens)

    rating_signal = 0
    if rating >= 4:
        rating_signal = 1
    elif rating <= 2:
        rating_signal = -1

    hybrid_score = (0.55 * vader_compound) + (0.25 * kw_score / 3) + (0.20 * rating_signal)

    if hybrid_score >= 0.12:
        sentiment = "positive"
    elif hybrid_score <= -0.12:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    confidence = round(min(1.0, abs(hybrid_score) + abs(vader_compound) * 0.35), 3)

    return sentiment, round(vader_compound, 3), round(hybrid_score, 3), confidence


def extract_grouped_aspects(review):
    found_groups = set()
    tokens = set(tokenize_text(review))

    for group, keywords in ASPECT_GROUPS.items():
        for keyword in keywords:
            if keyword in review or keyword in tokens:
                found_groups.add(group)
                break

    return list(found_groups)


def build_aspect_summary(df):
    positive_aspects = []
    negative_aspects = []

    for _, row in df.iterrows():
        aspects = row["aspect_groups"]
        for aspect in aspects:
            if row["sentiment"] == "positive":
                positive_aspects.append(aspect)
            elif row["sentiment"] == "negative":
                negative_aspects.append(aspect)

    pos_counter = Counter(positive_aspects)
    neg_counter = Counter(negative_aspects)

    positive_df = (
        pd.DataFrame(pos_counter.items(), columns=["Aspect", "Count"])
        .sort_values(by="Count", ascending=False)
        .reset_index(drop=True)
        if pos_counter else pd.DataFrame(columns=["Aspect", "Count"])
    )

    negative_df = (
        pd.DataFrame(neg_counter.items(), columns=["Aspect", "Count"])
        .sort_values(by="Count", ascending=False)
        .reset_index(drop=True)
        if neg_counter else pd.DataFrame(columns=["Aspect", "Count"])
    )

    return positive_df, negative_df


def generate_business_insights(df, positive_aspects_df, negative_aspects_df):
    insights = []

    if not positive_aspects_df.empty:
        top_strength = positive_aspects_df.iloc[0]["Aspect"]
        insights.append(f"Customers most frequently praise {top_strength}.")

    if not negative_aspects_df.empty:
        top_concern = negative_aspects_df.iloc[0]["Aspect"]
        insights.append(f"The most common complaint is related to {top_concern}.")

    product_sentiment = (
        df.groupby(["product_name", "sentiment"])
        .size()
        .reset_index(name="count")
    )

    for product in df["product_name"].dropna().unique():
        product_df = product_sentiment[product_sentiment["product_name"] == product]
        if not product_df.empty:
            top_sentiment = product_df.sort_values(by="count", ascending=False).iloc[0]["sentiment"]
            insights.append(f"For {product}, the dominant sentiment is {top_sentiment}.")

    avg_conf = round(df["confidence"].mean(), 3) if not df.empty else 0
    insights.append(f"Average model confidence across analyzed reviews is {avg_conf}.")

    return insights


def analyze_reviews_from_dataframe(df):
    setup_vader()
    analyzer = SentimentIntensityAnalyzer()

    required_columns = {"product_name", "review", "rating"}
    if not required_columns.issubset(df.columns):
        raise ValueError("DataFrame must contain columns: product_name, review, rating")

    df = df.copy()
    df["product_name"] = df["product_name"].astype(str)
    df["review"] = df["review"].astype(str)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["product_name", "review", "rating"])

    df["clean_review"] = df["review"].apply(clean_text)

    sentiment_results = df.apply(lambda row: hybrid_sentiment(row, analyzer), axis=1)
    df["sentiment"] = sentiment_results.apply(lambda x: x[0])
    df["vader_score"] = sentiment_results.apply(lambda x: x[1])
    df["hybrid_score"] = sentiment_results.apply(lambda x: x[2])
    df["confidence"] = sentiment_results.apply(lambda x: x[3])

    df["aspect_groups"] = df["clean_review"].apply(extract_grouped_aspects)

    sentiment_summary = df["sentiment"].value_counts().reset_index()
    sentiment_summary.columns = ["Sentiment", "Count"]

    product_summary = (
        df.groupby(["product_name", "sentiment"])
        .size()
        .reset_index(name="Count")
        .sort_values(by=["product_name", "Count"], ascending=[True, False])
        .reset_index(drop=True)
    )

    positive_aspects_df, negative_aspects_df = build_aspect_summary(df)
    business_insights = generate_business_insights(df, positive_aspects_df, negative_aspects_df)

    return {
        "analyzed_df": df,
        "sentiment_summary": sentiment_summary,
        "product_summary": product_summary,
        "positive_aspects": positive_aspects_df,
        "negative_aspects": negative_aspects_df,
        "business_insights": business_insights
    }


def analyze_reviews(csv_file, output_file="analyzed_reviews.csv"):
    df = pd.read_csv(csv_file)
    results = analyze_reviews_from_dataframe(df)
    results["analyzed_df"].to_csv(output_file, index=False)

    print("\n=== Sentiment Summary ===")
    print(results["sentiment_summary"])

    print("\n=== Product-wise Sentiment Summary ===")
    print(results["product_summary"])

    print("\n=== Top Positive Aspects ===")
    if not results["positive_aspects"].empty:
        print(results["positive_aspects"].head(10))
    else:
        print("No positive aspects found.")

    print("\n=== Top Negative Aspects ===")
    if not results["negative_aspects"].empty:
        print(results["negative_aspects"].head(10))
    else:
        print("No negative aspects found.")

    print("\n=== Business Insights ===")
    for insight in results["business_insights"]:
        print(f"- {insight}")

    print("\n=== Sample Output ===")
    print(
        results["analyzed_df"][
            [
                "product_name", "review", "rating", "sentiment",
                "vader_score", "hybrid_score", "confidence", "aspect_groups"
            ]
        ].head()
    )

    print(f"\nAnalyzed file saved as: {output_file}")
    return results


if __name__ == "__main__":
    analyze_reviews("sample_reviews.csv")