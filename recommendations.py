import random

def calculate_bmi(weight, height):
    return round(weight / (height/100)**2, 2)

def generate_recommendation(data):
    height = data.get("height")
    weight = data.get("weight")
    age = data.get("age")
    gender = data.get("gender")
    allergies = data.get("allergies", [])
    goal = data.get("goal")

    bmi = calculate_bmi(weight, height)

    # BMI Category
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 25:
        category = "Normal"
    elif 25 <= bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    # Expanded diet pools
    diets = {
        "weight_loss": [
            "Oats with fruits", "Grilled chicken", "Salads", "Green tea",
            "Vegetable soup", "Boiled eggs", "Smoothies", "Brown rice with veggies"
        ],
        "muscle_gain": [
            "Eggs", "Brown rice", "Lentils", "Protein shake",
            "Chicken breast", "Greek yogurt", "Peanut butter toast", "Tofu curry"
        ],
        "fitness": [
            "Smoothies", "Vegetable soups", "Whole grains", "Nuts",
            "Fruit salad", "Avocado toast", "Steamed fish", "Mixed sprouts"
        ]
    }

    # Expanded workout pools
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

    # Select random 3–4 items per request
    diet_plan = random.sample(diets.get(goal, ["Balanced meal plan"]), k=3)
    workout_plan = random.sample(workouts.get(goal, ["Regular exercise"]), k=3)

    # Allergy filter
    diet_plan = [food for food in diet_plan if not any(allergy.lower() in food.lower() for allergy in allergies)]

    return {
        "bmi": bmi,
        "category": category,
        "diet_plan": diet_plan,
        "workout_plan": workout_plan
    }
