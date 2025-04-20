from difflib import SequenceMatcher
import json
import re
import string
import logging
from typing import List, Dict
from collections import Counter
import numpy as np
import nltk
from nltk.corpus import stopwords

# Download NLTK data if not already done
nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))
PUNCTUATION = set(string.punctuation)

# Logging setup
logging.basicConfig(filename='matching.log', level=logging.INFO)

def clean_text(text: str) -> str:
    """Removes punctuation, lowercases, and removes stopwords"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML-like tags
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.lower().split()
    return ' '.join([word for word in words if word not in STOPWORDS])


def extract_query_from_persona(entity: Dict) -> str:
    """Extracts and cleans query from user corpus with name variants"""
    name = entity.get("name", "").lower()
    intro = entity.get("intro") or ""
    company = entity.get("company_industry") or ""
    
    full_query = " ".join([name, intro, company])
    return clean_text(full_query)
from typing import Dict, Any

def extract_query_from_profile(profile: Dict[str, Any]) -> str:
    """Extracts and cleans query from output profile"""
    parts = [
        profile.get("name") or "",
        profile.get("one_liner_about") or "",
        profile.get("full_about") or "",
    ]

    print(profile.get("name"))

    for exp in profile.get("experience") or []:
        if isinstance(exp, dict):
            parts.append(exp.get("role") or "")
            parts.append(exp.get("company") or "")

    for edu in profile.get("education") or []:
        if isinstance(edu, dict):
            parts.append(edu.get("institution") or "")
            parts.append(edu.get("degree") or "")

    return clean_text(" ".join(filter(None, parts)))

def softmax(x):
    """Compute softmax values for a list of scores."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def get_ngrams(tokens: List[str], n: int) -> set:
    """Generate n-grams (bigrams, trigrams, etc.)"""
    return set([' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)])

def calculate_unigram_scores(persona_query: str, profiles: List[Dict], persona_name: str) -> List[Dict]:
    """Compute n-gram overlap (uni+bi+tri) and softmax scores with name boost"""
    persona_tokens = persona_query.split()
    persona_unigrams = set(persona_tokens)
    persona_bigrams = get_ngrams(persona_tokens, 2)
    persona_trigrams = get_ngrams(persona_tokens, 3)

    scores = []

    for profile in profiles:
        profile_query = extract_query_from_profile(profile)
        profile_tokens = profile_query.split()

        profile_unigrams = set(profile_tokens)
        profile_bigrams = get_ngrams(profile_tokens, 2)
        profile_trigrams = get_ngrams(profile_tokens, 3)

        uni_overlap = len(persona_unigrams & profile_unigrams)
        bi_overlap = len(persona_bigrams & profile_bigrams)
        tri_overlap = len(persona_trigrams & profile_trigrams)

        total_overlap = uni_overlap + bi_overlap + tri_overlap
        # Get image similarity from profile
        image_similarity = profile.get("image_similarity", 0)
        
        # Apply boosts based on image similarity
        if image_similarity > 0.9:
            total_overlap += 3
        elif image_similarity > 0.7:
            total_overlap += 2

        # Boost if names are similar
        profile_name = profile.get("name", "")
        name_similarity = SequenceMatcher(None, persona_name or "", profile_name or "").ratio()
        boost = 1 if name_similarity > 0.7 else 0

        similarity_score = SequenceMatcher(None, persona_query, profile_query).ratio()

        scores.append({
            "index": profile.get("index"),
            "profile_url": profile.get("profile_url"),
            "query": profile_query,
            "unigram_overlap": uni_overlap,
            "bigram_overlap": bi_overlap,
            "trigram_overlap": tri_overlap,
            "total_overlap": total_overlap + boost,
            "name_similarity": name_similarity,
            "sequence_matcher_score": similarity_score,
            "image_similarity": image_similarity
        })

    # Sort by total_overlap (desc), then name_similarity (desc), then sequence_matcher_score (desc)
    scores = sorted(scores, key=lambda x: (
        -x["image_similarity"],
        -x["total_overlap"],
        -x["name_similarity"],
        -x["sequence_matcher_score"]
    ))

    # Apply softmax to total overlap scores
    raw_scores = [entry["total_overlap"] for entry in scores]
    softmax_scores = softmax(np.array(raw_scores))

    for i, score in enumerate(softmax_scores):
        scores[i]["score"] = float(score)

    return scores

def process_all_personas():
    """Main function: loads JSONs, generates queries, matches profiles"""
    with open('dataset/test.json') as f:
        personas = json.load(f)

    with open('temp/all_linkedin_profiles_similarity.json') as f:
        all_profiles = json.load(f)

    final_results = []
    for persona in personas:
        persona_query = extract_query_from_persona(persona)
        persona_name = persona.get("name", "")
        # print(persona_name)
        relevant_profiles = [p for p in all_profiles]
        # if not relevant_profiles:
        #     continue

        ranked_profiles = calculate_unigram_scores(persona_query, relevant_profiles, persona_name)
        print(ranked_profiles)
        final_results.append({
            "persona": persona_name,
            "persona_query": persona_query,
            "ranked_profiles": ranked_profiles
        })
        

    with open('temp/final_rankings.json', 'w') as f:
        json.dump(final_results, f, indent=2)

    return final_results

# Run it
if __name__ == "__main__":
    results = process_all_personas()
    print("✅ Processing complete. Results saved to temp/final_rankings.json")