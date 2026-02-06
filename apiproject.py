import os
import requests
from dotenv import load_dotenv
from serpapi import GoogleSearch

# 1. SETUP: Load API Key
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

def get_state_food_trends(state_code):
    """Finds food trends and strips away generic words to isolate nouns."""
    params = {
        "engine": "google_trends",
        "q": "food", 
        "geo": f"US-{state_code}",
        "cat": "71", # Food & Drink Category
        "data_type": "RELATED_QUERIES",
        "api_key": SERP_API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        queries = results.get('related_queries', {}).get('rising', []) + \
                  results.get('related_queries', {}).get('top', [])

        # Generic words that ruin our database search
        garbage_words = ["food", "fast", "restaurant", "menu", "near", "me", "delivery", "places", "va", "tx"]
        
        clean_trends = []
        for item in queries:
            original_query = item['query'].lower()
            
            # Extract just the specific noun (e.g., 'Mexican food' -> 'Mexican')
            words = original_query.split()
            filtered_words = [w for w in words if w not in garbage_words]
            product_only = " ".join(filtered_words).strip()
            
            if product_only and len(product_only) > 2:
                clean_trends.append(product_only)
        
        # Remove duplicates while keeping order
        return list(dict.fromkeys(clean_trends))[:15]
    except Exception as e:
        print(f"❌ Trends Error: {e}")
        return []

def analyze_until_found(trend_list):
    if not trend_list:
        print("\n⚠️ No trends found for this state.")
        return

    print(f"🔎 Scanning for a product with COMPLETE data...")

    for food in trend_list:
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": food,
            "json": 1, "page_size": 1,
            "fields": "product_name,nutrition_grades,nova_group,ecoscore_grade"
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("products") and len(data["products"]) > 0:
                p = data["products"][0]
                
                # Fetching the fields
                grade = p.get('nutrition_grades', '').lower()
                nova = p.get('nova_group')
                eco = p.get('ecoscore_grade', '').lower()

                # THE STRICT CHECK: No blanks, no 'unknown's allowed
                if not grade or grade == "unknown" or not nova or not eco or eco == "unknown":
                    print(f"  ... skipping '{food}' (incomplete data)")
                    continue
                
                print_analysis_box(p, food)
                return 
        except:
            continue
    print("\n❌ Checked all trends, but none had a full nutrition profile today.")

def print_analysis_box(product, original_query):
    """Prints the clean report formatting."""
    name = product.get('product_name', original_query).title()
    grade = product.get('nutrition_grades', 'N/A').upper()
    nova = product.get('nova_group', 'N/A')
    eco = product.get('ecoscore_grade', 'N/A').upper()

    print("\n" + "="*40)
    print(f" REGIONAL TREND ANALYSIS ")
    print("="*40)
    print(f"Top Trending Item: {name}")
    print(f"Health Grade:      {grade} (A=Best, E=Poor)")
    print(f"Processing Level:  {nova}/4 (4=Ultra-processed)")
    print(f"Eco-Impact Score:  {eco} (A=Eco-friendly, E=Eco-unfriendly)")
    print("="*40)
    
    # Simple logic-based insight
    if str(nova) == "4":
        print("💡 ANALYSIS: This trend is highly processed. Use sparingly!")
    elif grade in ["A", "B"]:
        print("💡 ANALYSIS: This is a healthy, minimally-processed choice!")
    else:
        print("💡 ANALYSIS: Moderation is recommended for this item.")

if __name__ == "__main__":
    if not SERP_API_KEY:
        print("❌ Error: SERP_API_KEY not found in .env file.")
    else:
        state = input("Enter State (e.g., VA, TX, CA): ").upper().strip()
        trends = get_state_food_trends(state)
        analyze_until_found(trends)