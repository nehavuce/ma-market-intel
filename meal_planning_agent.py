#!/usr/bin/env python3
"""
Recipe & Meal Planning Agent

Sends daily recipes with prep instructions and weekly grocery lists
for a 28-day vegetarian fat loss + muscle gain plan.

Usage:
    # Today's recipes
    python meal_planning_agent.py today

    # Specific day (1-28)
    python meal_planning_agent.py day 14

    # This week's grocery list (weeks 1-4)
    python meal_planning_agent.py grocery

    # Full week view
    python meal_planning_agent.py week

    # Run with Claude AI for enhanced tips (requires ANTHROPIC_API_KEY)
    python meal_planning_agent.py today --ai
    python meal_planning_agent.py grocery --ai
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

from meal_plan_data import (
    DAILY_TARGETS,
    FAT_LOSS_RULES,
    MEALS,
    SNACKS,
    WORKOUT_SCHEDULE,
)

# Plan start date — set this to your actual start date
PLAN_START_DATE = date(2026, 3, 30)  # Monday start
PLAN_DAYS = 28


def get_plan_day(target_date: date | None = None) -> int:
    """Return the plan day number (1-28) for a given date."""
    if target_date is None:
        target_date = date.today()
    delta = (target_date - PLAN_START_DATE).days
    if delta < 0 or delta >= PLAN_DAYS:
        return -1
    return delta + 1


def get_meal_day(plan_day: int) -> int:
    """Map plan day (1-28) to meal rotation day (1-7)."""
    return ((plan_day - 1) % 7) + 1


def get_week_number(plan_day: int) -> int:
    """Return week number (1-4) for a plan day."""
    return ((plan_day - 1) // 7) + 1


def get_weekday_name(plan_day: int) -> str:
    """Return the weekday name for a plan day."""
    target = PLAN_START_DATE + timedelta(days=plan_day - 1)
    return target.strftime("%A")


def format_daily_recipe(plan_day: int) -> str:
    """Format a full day's meals with recipes and tips."""
    meal_day = get_meal_day(plan_day)
    day_data = MEALS[meal_day]
    weekday = get_weekday_name(plan_day)
    week_num = get_week_number(plan_day)
    workout = WORKOUT_SCHEDULE.get(weekday, "Rest")

    total_protein = sum(
        day_data[meal]["protein_g"]
        for meal in ("breakfast", "lunch", "dinner")
    )

    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  DAY {plan_day} of 28  |  Week {week_num}  |  {weekday}")
    lines.append(f"  Meal rotation: {day_data['day_label']}")
    lines.append(f"{'=' * 60}")
    lines.append("")
    lines.append(f"  Workout: {workout}")
    lines.append(f"  Daily protein target: {DAILY_TARGETS['protein_g']}g")
    lines.append(f"  Today's meal protein: ~{total_protein}g (add snacks to hit target)")
    lines.append("")

    for meal_type, emoji in [("breakfast", "sunrise"), ("lunch", "sun"), ("dinner", "moon")]:
        meal = day_data[meal_type]
        lines.append(f"--- {meal_type.upper()} ({meal['protein_g']}g protein) ---")
        lines.append(f"  {meal['name']}")
        lines.append("")
        lines.append("  Ingredients:")
        for ing in meal["ingredients"]:
            lines.append(f"    - {ing}")
        lines.append("")

    lines.append("--- SNACK OPTIONS (pick 1-2 if needed) ---")
    for snack in SNACKS:
        lines.append(f"    - {snack['name']} ({snack['protein_g']}g protein)")
    lines.append("")

    lines.append("--- FAT LOSS REMINDERS ---")
    for rule in FAT_LOSS_RULES:
        lines.append(f"    * {rule}")
    lines.append("")

    return "\n".join(lines)


def generate_grocery_list(week_num: int) -> str:
    """Generate a consolidated grocery list for a week (days are always 1-7 rotation)."""
    ingredient_counts = defaultdict(list)

    for meal_day in range(1, 8):
        day_data = MEALS[meal_day]
        for meal_type in ("breakfast", "lunch", "dinner"):
            meal = day_data[meal_type]
            for ing in meal["ingredients"]:
                ingredient_counts[ing].append(f"{day_data['day_label']} {meal_type}")

    # Categorize ingredients
    categories = {
        "Proteins": [],
        "Dairy & Eggs": [],
        "Grains & Legumes": [],
        "Vegetables": [],
        "Fruits": [],
        "Pantry & Oils": [],
        "Herbs & Spices": [],
    }

    protein_keywords = ["tofu", "paneer", "protein powder", "edamame"]
    dairy_keywords = ["egg", "yogurt", "feta", "cottage cheese", "cheese", "milk", "almond milk"]
    grain_keywords = ["quinoa", "lentil", "chickpea", "black bean", "rice", "dal"]
    fruit_keywords = ["berri", "banana", "fruit", "lime", "lemon"]
    herb_keywords = ["herb", "parsley", "cilantro", "mint", "turmeric", "cumin",
                      "garam", "paprika", "garlic powder", "curry", "ginger",
                      "salt", "pepper", "sesame seeds"]
    pantry_keywords = ["oil", "soy sauce", "vinegar", "pesto", "hummus", "salsa",
                        "pine nut", "chia", "flax", "pumpkin seed", "sunflower",
                        "nuts", "walnut", "almond"]

    for ing, days in ingredient_counts.items():
        ing_lower = ing.lower()
        count_str = f"  - {ing}  (used {len(days)}x)"

        if any(k in ing_lower for k in protein_keywords):
            categories["Proteins"].append(count_str)
        elif any(k in ing_lower for k in dairy_keywords):
            categories["Dairy & Eggs"].append(count_str)
        elif any(k in ing_lower for k in grain_keywords):
            categories["Grains & Legumes"].append(count_str)
        elif any(k in ing_lower for k in fruit_keywords):
            categories["Fruits"].append(count_str)
        elif any(k in ing_lower for k in herb_keywords):
            categories["Herbs & Spices"].append(count_str)
        elif any(k in ing_lower for k in pantry_keywords):
            categories["Pantry & Oils"].append(count_str)
        else:
            categories["Vegetables"].append(count_str)

    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  WEEKLY GROCERY LIST  |  Week {week_num} of 4")
    lines.append(f"  (Same list each week — 7-day rotation)")
    lines.append(f"{'=' * 60}")
    lines.append("")

    for cat, items in categories.items():
        if items:
            lines.append(f"[ ] {cat.upper()}")
            for item in sorted(items):
                lines.append(item)
            lines.append("")

    lines.append("--- SNACK SUPPLIES ---")
    for snack in SNACKS:
        lines.append(f"  - {snack['name']}")
    lines.append("")

    return "\n".join(lines)


def format_week_view(week_num: int) -> str:
    """Show a compact overview of the full week's meals."""
    start_day = (week_num - 1) * 7 + 1

    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  WEEK {week_num} OVERVIEW  |  Days {start_day}-{start_day + 6}")
    lines.append(f"{'=' * 60}")
    lines.append("")

    for i in range(7):
        plan_day = start_day + i
        meal_day = get_meal_day(plan_day)
        day_data = MEALS[meal_day]
        weekday = get_weekday_name(plan_day)
        workout = WORKOUT_SCHEDULE.get(weekday, "Rest")

        total_protein = sum(
            day_data[meal]["protein_g"]
            for meal in ("breakfast", "lunch", "dinner")
        )

        lines.append(f"  {weekday} (Day {plan_day}) — ~{total_protein}g protein")
        lines.append(f"    B: {day_data['breakfast']['name']}")
        lines.append(f"    L: {day_data['lunch']['name']}")
        lines.append(f"    D: {day_data['dinner']['name']}")
        lines.append(f"    Workout: {workout}")
        lines.append("")

    return "\n".join(lines)


def get_ai_enhanced_tips(content: str, query_type: str) -> str:
    """Use Claude to add personalized tips and prep instructions."""
    try:
        import anthropic
    except ImportError:
        return "\n[Install anthropic package for AI-enhanced tips: pip install anthropic]\n"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "\n[Set ANTHROPIC_API_KEY environment variable for AI-enhanced tips]\n"

    client = anthropic.Anthropic(api_key=api_key)

    if query_type == "daily":
        system_prompt = (
            "You are a supportive nutrition coach for a vegetarian woman focused on "
            "fat loss + muscle gain. She lifts weights (125 lb deadlift) and is managing "
            "prediabetes. Keep advice practical, encouraging, and concise. "
            "Add: (1) Quick prep tips for each meal, (2) A motivational note, "
            "(3) One blood-sugar-friendly tip for the day. Keep it under 200 words."
        )
    else:
        system_prompt = (
            "You are a meal prep coach. Given this grocery list, add: "
            "(1) Batch prep suggestions to save time, (2) Storage tips, "
            "(3) Budget-friendly substitutions where possible. Keep it under 200 words."
        )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    )

    return "\n--- AI COACH TIPS ---\n" + message.content[0].text + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="28-Day Fat Loss Meal Planning Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # today
    today_parser = subparsers.add_parser("today", help="Show today's meals")
    today_parser.add_argument("--ai", action="store_true", help="Add AI-powered tips")

    # day N
    day_parser = subparsers.add_parser("day", help="Show meals for a specific plan day")
    day_parser.add_argument("number", type=int, help="Plan day number (1-28)")
    day_parser.add_argument("--ai", action="store_true", help="Add AI-powered tips")

    # grocery
    grocery_parser = subparsers.add_parser("grocery", help="Show weekly grocery list")
    grocery_parser.add_argument("--week", type=int, default=None, help="Week number (1-4)")
    grocery_parser.add_argument("--ai", action="store_true", help="Add AI-powered tips")

    # week
    week_parser = subparsers.add_parser("week", help="Show full week overview")
    week_parser.add_argument("--number", type=int, default=None, help="Week number (1-4)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "today":
        plan_day = get_plan_day()
        if plan_day == -1:
            today_str = date.today().isoformat()
            end_date = (PLAN_START_DATE + timedelta(days=PLAN_DAYS - 1)).isoformat()
            print(f"Today ({today_str}) is outside the 28-day plan window.")
            print(f"Plan runs from {PLAN_START_DATE.isoformat()} to {end_date}.")
            print(f"\nUse 'python meal_planning_agent.py day <1-28>' to view any day.")
            return
        output = format_daily_recipe(plan_day)
        print(output)
        if args.ai:
            print(get_ai_enhanced_tips(output, "daily"))

    elif args.command == "day":
        day_num = args.number
        if day_num < 1 or day_num > 28:
            print("Day must be between 1 and 28.")
            return
        output = format_daily_recipe(day_num)
        print(output)
        if args.ai:
            print(get_ai_enhanced_tips(output, "daily"))

    elif args.command == "grocery":
        week = args.week
        if week is None:
            plan_day = get_plan_day()
            week = get_week_number(plan_day) if plan_day > 0 else 1
        if week < 1 or week > 4:
            print("Week must be between 1 and 4.")
            return
        output = generate_grocery_list(week)
        print(output)
        if args.ai:
            print(get_ai_enhanced_tips(output, "grocery"))

    elif args.command == "week":
        week = args.number
        if week is None:
            plan_day = get_plan_day()
            week = get_week_number(plan_day) if plan_day > 0 else 1
        if week < 1 or week > 4:
            print("Week must be between 1 and 4.")
            return
        print(format_week_view(week))


if __name__ == "__main__":
    main()
