# recommendations.py
import random

def calculate_bmi(weight, height):
    return round(weight / (height/100)**2, 2)

def generate_recommendation(data):
    height = data.get("height", 0) or 0
    weight = data.get("weight", 0) or 0
    age = data.get("age")
    gender = data.get("gender")
    allergies = [a.lower() for a in (data.get("allergies") or [])]
    goal = data.get("goal") or "fitness"

    bmi = calculate_bmi(weight, height)

    # BMI Category
    if bmi <= 0:
        category = "Unknown"
    elif bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 25:
        category = "Normal"
    elif 25 <= bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    # Pools (expand anytime)
    diets = {
        "weight_loss": [
            "Oats with fruits", "Grilled chicken", "Salads", "Green tea",
            "Vegetable soup", "Boiled eggs", "Quinoa salad", "Brown rice with veggies",
            "Steamed fish", "Lentil soup", "Mixed greens & lean protein"
        ],
        "muscle_gain": [
            "Eggs", "Brown rice", "Lentils", "Protein shake",
            "Chicken breast", "Greek yogurt", "Peanut butter toast", "Tofu curry",
            "Cottage cheese", "Salmon", "Beef stir-fry"
        ],
        "fitness": [
            "Smoothies", "Vegetable soups", "Whole grains", "Nuts",
            "Fruit salad", "Avocado toast", "Steamed fish", "Mixed sprouts",
            "Oat pancakes", "Chia pudding"
        ]
    }

    workouts = {
        "weight_loss": [
            "30 min jogging", "HIIT cardio", "Planks", "Jump rope",
            "Burpees", "Mountain climbers", "Cycling", "Walking lunges"
        ],
        "muscle_gain": [
            "Weight lifting", "Push-ups", "Squats", "Deadlifts",
            "Bench press", "Pull-ups", "Shoulder press", "Leg press"
        ],
        "fitness": [
            "Yoga", "Cycling", "Stretching", "Pilates",
            "Jogging", "Swimming", "Dancing", "Bodyweight training"
        ]
    }

    # BMI-aware tweaks: if obese or overweight, bias toward weight_loss pool
    if category in ("Overweight", "Obese") and goal != "weight_loss":
        diet_pool = list({*diets.get(goal, []), *diets.get("weight_loss", [])})
        workout_pool = list({*workouts.get(goal, []), *workouts.get("weight_loss", [])})
    elif category == "Underweight" and goal != "muscle_gain":
        diet_pool = list({*diets.get(goal, []), *diets.get("muscle_gain", [])})
        workout_pool = workouts.get(goal, [])
    else:
        diet_pool = diets.get(goal, diets.get("fitness"))
        workout_pool = workouts.get(goal, workouts.get("fitness"))

    # Allergy filter (remove items containing allergy substrings)
    def filter_allergies(items):
        out = []
        for it in items:
            lower = it.lower()
            if not any(allergy in lower for allergy in allergies if allergy):
                out.append(it)
        return out

    diet_pool = filter_allergies(diet_pool)
    workout_pool = filter_allergies(workout_pool)

    # Random sample with safe fallback
    def pick_random(pool, k=3):
        if not pool:
            return []
        k = min(k, len(pool))
        return random.sample(pool, k)

    diet_plan = pick_random(diet_pool, k=4)
    workout_plan = pick_random(workout_pool, k=4)

    return {
        "bmi": bmi,
        "category": category,
        "diet_plan": diet_plan,
        "workout_plan": workout_plan
    }
