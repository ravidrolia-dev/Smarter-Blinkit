from services.recipe_agent import normalize_ingredient

test_cases = [
    ("2 tomatoes, finely chopped", "tomato"),
    ("1 tablespoon salt", "salt"),
    ("3 cloves garlic", "garlic"),
    ("500g chicken breast, sliced", "chicken breast"),
    ("fresh coriander leaves, chopped", "coriander leaf"),
    ("onions, chopped", "onion"),
    ("potatoes, boiled and mashed", "potato"),
    ("2 cups milk", "milk"),
    ("Kasuri Methi", "kasuri methi")
]

print("--- Normalization Test ---")
for raw, expected in test_cases:
    normalized = normalize_ingredient(raw)
    status = "✅" if normalized == expected else "❌"
    print(f"{status} '{raw}' -> '{normalized}' (Expected: '{expected}')")
