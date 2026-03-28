"""
28-Day Fat Loss + Muscle Gain Meal Plan Data

7-day rotating plan (repeat 4x), vegetarian, high-protein (80-100g/day).
"""

DAILY_TARGETS = {
    "protein_g": "80–100",
    "focus": "Whole foods, fiber, stable blood sugar",
    "diet": "Vegetarian",
}

MEALS = {
    1: {
        "day_label": "Day 1",
        "breakfast": {
            "name": "Egg White Veggie Scramble + Avocado",
            "ingredients": [
                "6 egg whites",
                "1/2 avocado",
                "1/2 cup bell peppers, diced",
                "1/2 cup spinach",
                "1/4 cup onion, diced",
                "1 tsp olive oil",
                "salt and pepper to taste",
            ],
            "protein_g": 26,
        },
        "lunch": {
            "name": "Lentil + Quinoa Salad with Cucumber & Feta",
            "ingredients": [
                "1/2 cup cooked lentils",
                "1/2 cup cooked quinoa",
                "1/2 cucumber, diced",
                "1/4 cup feta cheese, crumbled",
                "1/4 cup cherry tomatoes, halved",
                "1 tbsp olive oil",
                "1 tbsp lemon juice",
                "fresh herbs (parsley, mint)",
            ],
            "protein_g": 22,
        },
        "dinner": {
            "name": "Tofu Stir-Fry with Broccoli & Bell Peppers",
            "ingredients": [
                "200g extra-firm tofu, cubed",
                "1 cup broccoli florets",
                "1/2 cup bell peppers, sliced",
                "2 cloves garlic, minced",
                "1 tbsp soy sauce (low sodium)",
                "1 tsp sesame oil",
                "1 tsp ginger, grated",
                "1 tsp olive oil",
            ],
            "protein_g": 28,
        },
    },
    2: {
        "day_label": "Day 2",
        "breakfast": {
            "name": "Protein Smoothie",
            "ingredients": [
                "1 scoop protein powder (plant-based or whey)",
                "1 tbsp chia seeds",
                "1/2 cup mixed berries",
                "1 cup unsweetened almond milk",
                "1/2 banana",
            ],
            "protein_g": 30,
        },
        "lunch": {
            "name": "Chickpea Salad",
            "ingredients": [
                "1 cup canned chickpeas, drained",
                "1 tbsp olive oil",
                "1 tbsp lemon juice",
                "fresh herbs (parsley, cilantro)",
                "1/4 cup red onion, diced",
                "1/4 cup cucumber, diced",
                "salt and pepper to taste",
            ],
            "protein_g": 15,
        },
        "dinner": {
            "name": "Paneer + Veggie Sauté",
            "ingredients": [
                "150g paneer, cubed",
                "1 cup mixed vegetables (zucchini, bell pepper, onion)",
                "1 tsp olive oil",
                "1/2 tsp turmeric",
                "1/2 tsp cumin",
                "1/2 tsp garam masala",
                "salt to taste",
            ],
            "protein_g": 32,
        },
    },
    3: {
        "day_label": "Day 3",
        "breakfast": {
            "name": "Greek Yogurt + Nuts + Seeds",
            "ingredients": [
                "1 cup plain Greek yogurt",
                "2 tbsp mixed nuts (almonds, walnuts)",
                "1 tbsp pumpkin seeds",
                "1 tbsp flax seeds",
            ],
            "protein_g": 24,
        },
        "lunch": {
            "name": "Dal + Sautéed Veggies",
            "ingredients": [
                "1/2 cup yellow or red lentils (dry)",
                "1 cup water or vegetable broth",
                "1/2 cup spinach",
                "1/4 cup onion, diced",
                "1 clove garlic, minced",
                "1/2 tsp turmeric",
                "1/2 tsp cumin",
                "1 tsp olive oil",
                "salt to taste",
            ],
            "protein_g": 20,
        },
        "dinner": {
            "name": "Tofu + Cauliflower Rice Bowl",
            "ingredients": [
                "200g extra-firm tofu, cubed",
                "2 cups cauliflower rice",
                "1/2 cup edamame",
                "1 tbsp soy sauce (low sodium)",
                "1 tsp sesame oil",
                "1/4 avocado",
                "sesame seeds for garnish",
            ],
            "protein_g": 34,
        },
    },
    4: {
        "day_label": "Day 4",
        "breakfast": {
            "name": "Egg White Omelette (Spinach, Mushrooms, Feta)",
            "ingredients": [
                "6 egg whites",
                "1/2 cup spinach",
                "1/4 cup mushrooms, sliced",
                "2 tbsp feta cheese, crumbled",
                "1 tsp olive oil",
                "salt and pepper to taste",
            ],
            "protein_g": 28,
        },
        "lunch": {
            "name": "Quinoa + Roasted Veggies",
            "ingredients": [
                "3/4 cup cooked quinoa",
                "1/2 cup roasted zucchini",
                "1/2 cup roasted bell peppers",
                "1/4 cup roasted red onion",
                "1 tbsp olive oil",
                "1 tbsp balsamic vinegar",
                "salt and pepper to taste",
            ],
            "protein_g": 12,
        },
        "dinner": {
            "name": "Zucchini Noodles + Pesto + Tofu",
            "ingredients": [
                "200g extra-firm tofu, cubed",
                "2 medium zucchini, spiralized",
                "2 tbsp basil pesto",
                "1/4 cup cherry tomatoes, halved",
                "1 tbsp pine nuts",
                "1 tsp olive oil",
            ],
            "protein_g": 30,
        },
    },
    5: {
        "day_label": "Day 5",
        "breakfast": {
            "name": "Green Protein Smoothie",
            "ingredients": [
                "1 scoop protein powder",
                "1 cup spinach",
                "1 tbsp flax seeds",
                "1 cup unsweetened almond milk",
                "1/2 banana",
                "1/2 cup ice",
            ],
            "protein_g": 28,
        },
        "lunch": {
            "name": "Black Bean + Avocado Bowl",
            "ingredients": [
                "3/4 cup black beans, cooked",
                "1/2 avocado, sliced",
                "1/4 cup corn kernels",
                "1/4 cup cherry tomatoes, halved",
                "2 tbsp salsa",
                "1 tbsp lime juice",
                "fresh cilantro",
                "salt to taste",
            ],
            "protein_g": 18,
        },
        "dinner": {
            "name": "Light Veggie Curry + Tofu",
            "ingredients": [
                "200g extra-firm tofu, cubed",
                "1/2 cup coconut milk (light)",
                "1 cup mixed vegetables (cauliflower, peas, carrots)",
                "1/2 onion, diced",
                "2 cloves garlic, minced",
                "1 tsp curry powder",
                "1/2 tsp turmeric",
                "1 tsp olive oil",
                "salt to taste",
            ],
            "protein_g": 30,
        },
    },
    6: {
        "day_label": "Day 6",
        "breakfast": {
            "name": "Cottage Cheese + Fruit + Seeds",
            "ingredients": [
                "1 cup low-fat cottage cheese",
                "1/2 cup mixed berries",
                "1 tbsp pumpkin seeds",
                "1 tbsp sunflower seeds",
            ],
            "protein_g": 28,
        },
        "lunch": {
            "name": "Lentil Soup + Side Salad",
            "ingredients": [
                "1/2 cup red lentils (dry)",
                "1 cup vegetable broth",
                "1/2 cup diced carrots",
                "1/4 cup diced celery",
                "1/4 cup onion, diced",
                "1 clove garlic, minced",
                "1/2 tsp cumin",
                "2 cups mixed greens (side salad)",
                "1 tbsp olive oil",
                "1 tbsp vinegar (for salad)",
            ],
            "protein_g": 20,
        },
        "dinner": {
            "name": "Grilled Paneer + Veggies",
            "ingredients": [
                "150g paneer, sliced",
                "1 cup mixed vegetables (bell pepper, zucchini, onion)",
                "1 tbsp olive oil",
                "1/2 tsp paprika",
                "1/2 tsp garlic powder",
                "salt and pepper to taste",
            ],
            "protein_g": 32,
        },
    },
    7: {
        "day_label": "Day 7",
        "breakfast": {
            "name": "Egg White Scramble + Peppers & Onions",
            "ingredients": [
                "6 egg whites",
                "1/2 cup bell peppers, diced",
                "1/4 cup onion, diced",
                "1 tsp olive oil",
                "salt and pepper to taste",
            ],
            "protein_g": 24,
        },
        "lunch": {
            "name": "Hummus + Veggie Bowl with Chickpeas",
            "ingredients": [
                "3 tbsp hummus",
                "1/2 cup chickpeas, cooked",
                "1/2 cup cucumber, sliced",
                "1/2 cup cherry tomatoes",
                "1/4 cup shredded carrots",
                "2 cups mixed greens",
                "1 tbsp olive oil",
                "1 tbsp lemon juice",
            ],
            "protein_g": 18,
        },
        "dinner": {
            "name": "Tofu Buddha Bowl (Quinoa + Greens)",
            "ingredients": [
                "200g extra-firm tofu, cubed",
                "1/2 cup cooked quinoa",
                "1 cup mixed greens",
                "1/4 avocado, sliced",
                "1/4 cup shredded carrots",
                "1/4 cup edamame",
                "1 tbsp soy sauce (low sodium)",
                "1 tsp sesame oil",
                "sesame seeds for garnish",
            ],
            "protein_g": 34,
        },
    },
}

SNACKS = [
    {"name": "Greek yogurt (plain)", "protein_g": 15},
    {"name": "Protein shake", "protein_g": 25},
    {"name": "Roasted chickpeas (1/3 cup)", "protein_g": 7},
    {"name": "Mixed nuts (small handful, ~1oz)", "protein_g": 6},
]

WORKOUT_SCHEDULE = {
    "Monday": "Strength A (Lower Body + Core) + Walk",
    "Tuesday": "Walk + Light Yoga/Meditation",
    "Wednesday": "Strength B (Upper Body Push/Pull) + Walk",
    "Thursday": "Walk + Mobility",
    "Friday": "Strength C (Full Body) + Walk",
    "Saturday": "Long Walk / Active Fun",
    "Sunday": "Rest + Reset",
}

FAT_LOSS_RULES = [
    "Protein first every meal",
    "No naked carbs (always pair with protein/fat)",
    "Lift heavy — progressive overload",
    "Walk daily — 8-10k steps (non-negotiable)",
    "Don't undereat — avoid the binge cycle",
]
