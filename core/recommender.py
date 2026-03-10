# ==========================================================
# Excel.py
# Clothing Recommendation Engine
# Built for: db_products_cleaned.csv
# ==========================================================

import pandas as pd
import os
import random
import re

import os

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE   = os.path.join(BASE_DIR, "data", "db_products_cleaned.csv")
IMAGE_FOLDER = os.path.join(BASE_DIR, "assets", "clothing_images")

# ----------------------------------------------------------
# Stopwords — stripped from user query before matching
# ----------------------------------------------------------
STOPWORDS = {
    "a", "an", "the", "for", "and", "or", "to", "in", "on", "at",
    "of", "with", "is", "it", "i", "me", "my", "what", "should",
    "can", "how", "do", "wear", "wearing", "attire", "outfit",
    "clothes", "clothing", "suggest", "show", "give", "please",
    "need", "want", "looking", "like", "some", "something",
    "men", "man", "male", "women", "woman", "female", "guys", "girls",
    "mens", "womens"
}

# ----------------------------------------------------------
# Synonym map — built from actual occasion words in the CSV
# ----------------------------------------------------------
OCCASION_SYNONYMS = {
    "wedding":  ["wedding", "weddings", "sangeet", "sangeets", "mehendi",
                 "haldi", "reception", "receptions", "bridal", "destination",
                 "ceremonies", "weddingsangeet"],
    "casual":   ["casual", "casualwear", "everyday", "daily", "outings",
                 "outing", "hangouts", "relaxed", "chill", "errands",
                 "streetwear", "streetstyle", "weekend"],
    "party":    ["party", "parties", "partywear", "celebration", "celebrations",
                 "festive", "cocktail", "cocktails", "gala", "galas",
                 "evening", "evenings", "soirees", "nightout"],
    "formal":   ["formal", "formals", "office", "business", "corporate",
                 "networking", "conferences", "meetings", "workwear",
                 "semiformal", "professional", "boardroom", "pitch"],
    "beach":    ["beach", "beachside", "resort", "vacation", "vacations",
                 "summer", "cruise", "pool", "poolside", "tropical", "bali"],
    "gym":      ["gym", "fitness", "workout", "athletic", "sport",
                 "sports", "classes", "active", "outdoor", "activities"],
    "date":     ["date", "dates", "dinner", "dinners", "romantic",
                 "night", "nights", "sundowner", "sundowners", "rooftop",
                 "anniversary", "anniversaries"],
    "travel":   ["travel", "airport", "trip", "trips", "road",
                 "getaway", "getaways", "vacation", "vacations", "holiday",
                 "international", "european"],
    "festival": ["festival", "festivals", "festive", "diwali", "holi",
                 "navratri", "cultural", "traditional", "ethnic", "celebration"],
    "office":   ["office", "workwear", "business", "formal", "corporate",
                 "meetings", "networking", "conferences", "professional",
                 "boardroom", "semiformal"],
    "brunch":   ["brunch", "brunches", "lunch", "lunches", "coffee",
                 "weekend", "social", "gathering", "gatherings", "cafe"],
    "concert":  ["concert", "concerts", "music", "festival", "festivals",
                 "gigs", "indie"],
    "sport":    ["sport", "sports", "gym", "fitness", "workout",
                 "athletic", "outdoor", "activities", "classes"],
}


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def expand_query(query_words):
    expanded = set(query_words)
    for word in list(query_words):
        if word in OCCASION_SYNONYMS:
            expanded.update(OCCASION_SYNONYMS[word])
    return expanded


def score_occasions(occ_raw, query_words):
    """
    Score a row's occasions string against query keywords.
    Uses both word-level match and substring match to handle
    concatenated values like 'weddingsangeetmehendi'.
    """
    # Word-level match
    occ_clean = clean_text(occ_raw)
    occ_words = set(occ_clean.split())
    score = len(query_words & occ_words)

    # Substring match for concatenated occasion strings
    occ_lower = occ_raw.lower()
    for word in query_words:
        if len(word) >= 5 and word in occ_lower:
            score += 1

    return score


# ----------------------------------------------------------
# Main function — called from cam1.py
# ----------------------------------------------------------
def get_clothes(query, gender):

    df = pd.read_csv(DATA_FILE)

    # Normalize
    df["gender"] = df["gender"].str.strip().str.capitalize()
    df["occasions"] = df["occasions"].fillna("Unknown").astype(str)

    # Build keyword set
    raw_words = set(clean_text(query).split())
    query_words = raw_words - STOPWORDS
    query_words = expand_query(query_words)

    print(f"[Excel] Gender: {gender} | Keywords: {query_words}")

    # Gender filter
    if gender == "male":
        allowed_genders = {"Men", "Unisex"}
    elif gender == "female":
        allowed_genders = {"Women", "Unisex"}
    else:
        # unknown — include all so Unisex always appears
        allowed_genders = {"Men", "Women", "Unisex"}

    # Score every row
    candidates = []
    for _, row in df.iterrows():
        if row["gender"] not in allowed_genders:
            continue
        score = score_occasions(row["occasions"], query_words)
        if score > 0:
            candidates.append((score, row))

    candidates.sort(key=lambda x: x[0], reverse=True)
    print(f"[Excel] Matching rows: {len(candidates)}")

    # Pick top results that have images
    results = []
    for score, row in candidates:
        sku = str(row["sku"])
        category = str(row["categories"])
        product_url = str(row["product_url"])

        folder = os.path.join(IMAGE_FOLDER, sku)
        if not os.path.exists(folder):
            continue

        images = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if not images:
            continue

        results.append((random.choice(images), category, product_url))

        if len(results) >= 6:
            break

    print(f"[Excel] Results with images: {len(results)}")
    return results
