from mongo_utils import opportunities_collection
from gemini_utils import rank_opportunities, parse_rankings

# Load opportunities
opportunities = list(opportunities_collection.find({}, {"_id": 0}))

# Test profile
test_profile = {
    "name": "Test User",
    "cgpa": 8.5,
    "degree": "B.Tech",
    "grad_year": 2026,
    "skills": ["Python", "Machine Learning", "SQL"],
    "interests": ["AI", "Data Science"]
}

print(f"Found {len(opportunities)} opportunities")
print("Generating rankings...")

result = rank_opportunities(test_profile, opportunities)
print("\n" + "="*50)
print("RANKING RESULT:")
print("="*50)
print(result)

print("\n" + "="*50)
print("PARSED RANKINGS:")
print("="*50)
rankings = parse_rankings(result)
for r in rankings:
    print(f"- {r['title']}: {r['score']}% - {r['reason']}")