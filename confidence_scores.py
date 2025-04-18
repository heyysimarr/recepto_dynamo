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
            break

    # 1. Semantic Similarity (35%)
    profile_text = profile.get("query", "")
    embeddings = model.encode([persona_query, profile_text])
    text_sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    # 2. Name Similarity (25%)
    name_sim = profile.get("name_similarity", 0)
    
    # 3. N-gram Bonus (10%)
    ngram_bonus = 1.0 if (profile.get("bigram_overlap", 0) > 0 or 
                         profile.get("trigram_overlap", 0) > 0) else 0
    
    # Weighted Sum
    ci_score = (
        0.35 * text_sim +
        0.30 * image_sim +
        0.25 * name_sim +
        0.10 * ngram_bonus
    )
    
    return round(ci_score * 100, 2)  # Convert to percentage

def generate_ci_scores(input_json: str, output_csv: str):
    """Generate CSV with URL and CI Score for top matches"""
    with open(input_json) as f:
        final_results = json.load(f)
    
    with open('output.json') as f:  # Needed for image scores
        all_profiles = json.load(f)
    
    results = []
    for persona in final_results:
        if not persona.get("ranked_profiles"):
            continue
        
        top_match = persona["ranked_profiles"][0]
        persona_query = persona["persona_query"]
        
        ci_score = calculate_ci_score(persona_query, top_match, all_profiles)
        
        results.append({
            "url": top_match["profile_url"],
            "CI score": ci_score
        })
    
    # Write to CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["url", "CI score"])
        writer.writeheader()
        writer.writerows(results)

# Run the processing
generate_ci_scores('temp/final_rankings.json', 'temp/confidence_scores.csv')
print("✅ CI scores generated in temp/confidence_scores.csv")