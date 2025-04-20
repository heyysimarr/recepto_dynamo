import json
import csv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_ci_score(persona_query: str, profile: dict, all_profiles: list) -> float:
    """
    Calculate CI Score with weights:
    - 35% Text similarity (semantic)
    - 30% Image similarity
    - 25% Name similarity
    - 10% N-gram bonus
    """
    # Get image similarity from original profile data
    image_sim = 0
    for original_profile in all_profiles:
        if original_profile.get("profile_url") == profile.get("profile_url"):
            image_sim = original_profile.get("image_similarity", 0)
            print(f"✅ Image similarity found for {profile.get('profile_url')}: {image_sim}")
            break
    else:
        print(f"⚠️  Image similarity NOT FOUND for {profile.get('profile_url')} — defaulting to 0")

    # 1. Semantic Similarity (35%)
    profile_text = profile.get("query", "")
    embeddings = model.encode([persona_query, profile_text])
    text_sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    print(f"🔍 Text similarity: {text_sim:.4f}")

    # 2. Name Similarity (25%)
    name_sim = profile.get("name_similarity", 0)
    print(f"🔍 Name similarity: {name_sim:.4f}")

    # 3. N-gram Bonus (10%)
    ngram_bonus = 1.0 if (profile.get("bigram_overlap", 0) > 0 or 
                         profile.get("trigram_overlap", 0) > 0) else 0
    print(f"🔍 N-gram bonus: {ngram_bonus}")

    # Weighted Sum
    ci_score = (
        0.35 * text_sim +
        0.30 * image_sim +
        0.25 * name_sim +
        0.10 * ngram_bonus
    )
    final_score = round(ci_score * 100, 2)
    print(f"✅ CI score for {profile.get('profile_url')}: {final_score:.2f}\n")

    return final_score  # Convert to percentage

# def generate_ci_scores(input_json: str, output_csv: str):
#     """Generate CSV with URL and CI Score for top matches"""
#     print(f"📂 Loading ranked profiles from {input_json}")
#     with open(input_json) as f:
#         final_results = json.load(f)
    
#     print(f"📂 Loading image similarity data from dataset/test.json")
#     with open('dataset/test.json') as f:  # Needed for image scores
#         all_profiles = json.load(f)
    
#     results = []
#     for persona in final_results:
#         print(persona)
#         if not persona.get("ranked_profiles"):
#             print("⚠️  Skipping persona with no ranked profiles")
#             continue
        
#         top_match = persona["ranked_profiles"][0]
#         persona_query = persona["persona_query"]

#         print(f"\n🔎 Processing persona query: {persona_query}")
#         ci_score = calculate_ci_score(persona_query, top_match, all_profiles)

#         results.append({
#             "url": top_match["profile_url"],
#             "CI score": ci_score
#         })
    
#     # Write to CSV
#     print(f"\n💾 Writing results to {output_csv}")
#     with open(output_csv, 'w', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=["url", "CI score"])
#         writer.writeheader()
#         writer.writerows(results)

# # Run the processing
# generate_ci_scores('temp/final_rankings.json', 'temp/confidence_scores.csv')
# print("\n✅ CI scores generated in temp/confidence_scores.csv")

def generate_ci_scores(input_json: str, output_csv: str):
    """Generate CSV with URL and CI Score for all ranked matches"""
    print(f"📂 Loading ranked profiles from {input_json}")
    with open(input_json) as f:
        final_results = json.load(f)
    
    print(f"📂 Loading image similarity data from dataset/test.json")
    with open('dataset/test.json') as f:  # Needed for image scores
        all_profiles = json.load(f)
    
    results = []
    for persona in final_results:
        if not persona.get("ranked_profiles"):
            print("⚠️  Skipping persona with no ranked profiles")
            continue
        
        persona_query = persona["persona_query"]
        print(f"\n🔎 Processing persona query: {persona_query}")

        for i, profile in enumerate(persona["ranked_profiles"]):
            ci_score = calculate_ci_score(persona_query, profile, all_profiles)

            results.append({
                "persona_query": persona_query[:50],  # truncated for readability
                "rank": i + 1,
                "url": profile.get("profile_url"),
                "CI score": ci_score
            })
    # Write to CSV
    print(f"\n💾 Writing results to {output_csv}")
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["persona_query", "rank", "url", "CI score"])
        writer.writeheader()
        writer.writerows(results)

# Run the processing
generate_ci_scores('temp/final_rankings.json', 'temp/confidence_scores.csv')
print("\n✅ CI scores generated in temp/confidence_scores.csv")
