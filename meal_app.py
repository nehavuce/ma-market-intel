#!/usr/bin/env python3
"""
Meal Planning App — 28-Day Fat Loss + Muscle Gain

Run with:
    streamlit run meal_app.py
"""

import os
from datetime import date, timedelta

import streamlit as st

from meal_plan_data import (
    DAILY_TARGETS,
    FAT_LOSS_RULES,
    MEALS,
    SNACKS,
    WORKOUT_SCHEDULE,
)

PLAN_START_DATE = date(2026, 3, 30)
PLAN_DAYS = 28

st.set_page_config(
    page_title="Meal Planner",
    page_icon="🥗",
    layout="wide",
)


# --- Helpers ---
def get_plan_day(target_date: date) -> int:
    delta = (target_date - PLAN_START_DATE).days
    if delta < 0 or delta >= PLAN_DAYS:
        return -1
    return delta + 1


def meal_day(plan_day: int) -> int:
    return ((plan_day - 1) % 7) + 1


def week_num(plan_day: int) -> int:
    return ((plan_day - 1) // 7) + 1


def plan_date(plan_day: int) -> date:
    return PLAN_START_DATE + timedelta(days=plan_day - 1)


# --- Sidebar ---
st.sidebar.title("🥗 Meal Planner")
st.sidebar.markdown("28-Day Fat Loss + Muscle Gain")
st.sidebar.divider()

view = st.sidebar.radio("View", ["Today's Meals", "Browse Days", "Week Overview", "Grocery List", "Full Plan"])

st.sidebar.divider()
st.sidebar.markdown("**Daily Targets**")
st.sidebar.markdown(f"- Protein: **{DAILY_TARGETS['protein_g']}g**")
st.sidebar.markdown(f"- Diet: **{DAILY_TARGETS['diet']}**")
st.sidebar.markdown(f"- Focus: {DAILY_TARGETS['focus']}")

st.sidebar.divider()
st.sidebar.markdown("**Fat Loss Rules**")
for rule in FAT_LOSS_RULES:
    st.sidebar.markdown(f"- {rule}")


# --- Render a single day's meals ---
def render_day(pd_num: int):
    md = meal_day(pd_num)
    day_data = MEALS[md]
    d = plan_date(pd_num)
    weekday = d.strftime("%A")
    workout = WORKOUT_SCHEDULE.get(weekday, "Rest")
    total_protein = sum(day_data[m]["protein_g"] for m in ("breakfast", "lunch", "dinner"))

    is_today = d == date.today()
    label = f"Day {pd_num} — {weekday}, {d.strftime('%b %d')}"
    if is_today:
        label += "  ⬅️ TODAY"

    st.subheader(label)

    col_info, col_workout = st.columns([2, 1])
    with col_info:
        st.metric("Meal Protein", f"~{total_protein}g", f"Add snacks for {DAILY_TARGETS['protein_g']}g target")
    with col_workout:
        st.info(f"**Workout:** {workout}")

    cols = st.columns(3)
    for i, (meal_type, icon) in enumerate([("breakfast", "🌅"), ("lunch", "☀️"), ("dinner", "🌙")]):
        meal = day_data[meal_type]
        with cols[i]:
            st.markdown(f"### {icon} {meal_type.title()}")
            st.markdown(f"**{meal['name']}**")
            st.markdown(f"*{meal['protein_g']}g protein*")
            st.markdown("**Ingredients:**")
            for ing in meal["ingredients"]:
                st.markdown(f"- {ing}")

    with st.expander("🍿 Snack Options (pick 1-2 if needed)"):
        for snack in SNACKS:
            st.markdown(f"- {snack['name']} — {snack['protein_g']}g protein")


# --- Grocery list ---
def render_grocery(wk: int):
    from collections import defaultdict

    st.subheader(f"🛒 Grocery List — Week {wk}")
    st.caption("Same rotation each week. Quantities below are for 7 days.")

    all_ingredients = defaultdict(int)
    for md in range(1, 8):
        day_data = MEALS[md]
        for meal_type in ("breakfast", "lunch", "dinner"):
            for ing in day_data[meal_type]["ingredients"]:
                all_ingredients[ing] += 1

    categories = {
        "🥩 Proteins": ["tofu", "paneer", "protein powder", "edamame"],
        "🥚 Dairy & Eggs": ["egg", "yogurt", "feta", "cottage cheese", "cheese", "milk", "coconut milk"],
        "🌾 Grains & Legumes": ["quinoa", "lentil", "chickpea", "black bean", "rice", "dal"],
        "🥦 Vegetables": [],
        "🍋 Fruits": ["berri", "banana", "fruit", "lime", "lemon"],
        "🫙 Pantry": ["oil", "soy sauce", "vinegar", "pesto", "hummus", "salsa",
                       "pine nut", "chia", "flax", "pumpkin seed", "sunflower",
                       "nuts", "walnut", "almond"],
        "🌿 Herbs & Spices": ["herb", "parsley", "cilantro", "mint", "turmeric", "cumin",
                               "garam", "paprika", "garlic powder", "curry", "ginger",
                               "salt", "pepper", "sesame seeds"],
    }

    categorized = {cat: [] for cat in categories}

    for ing, count in sorted(all_ingredients.items()):
        ing_lower = ing.lower()
        placed = False
        for cat, keywords in categories.items():
            if cat == "🥦 Vegetables":
                continue
            if any(k in ing_lower for k in keywords):
                categorized[cat].append((ing, count))
                placed = True
                break
        if not placed:
            categorized["🥦 Vegetables"].append((ing, count))

    cols = st.columns(2)
    cat_list = list(categorized.items())
    for idx, (cat, items) in enumerate(cat_list):
        if not items:
            continue
        with cols[idx % 2]:
            st.markdown(f"**{cat}**")
            for ing, count in items:
                st.checkbox(f"{ing} *(×{count})*", key=f"g_{wk}_{ing}")

    st.divider()
    st.markdown("**Snack Supplies**")
    for snack in SNACKS:
        st.checkbox(snack["name"], key=f"snack_{wk}_{snack['name']}")


# --- Views ---
if view == "Today's Meals":
    st.title("Today's Meals")
    pd_num = get_plan_day(date.today())
    if pd_num == -1:
        end = (PLAN_START_DATE + timedelta(days=PLAN_DAYS - 1)).strftime("%b %d")
        st.warning(
            f"Today is outside the 28-day plan window.\n\n"
            f"Plan runs **{PLAN_START_DATE.strftime('%b %d')}** to **{end}**.\n\n"
            f"Use **Browse Days** to preview any day."
        )
        st.divider()
        st.markdown("**Preview: Day 1**")
        render_day(1)
    else:
        render_day(pd_num)

elif view == "Browse Days":
    st.title("Browse Days")
    selected = st.slider("Select plan day", 1, 28, 1)
    render_day(selected)

elif view == "Week Overview":
    st.title("Week Overview")
    wk = st.radio("Week", [1, 2, 3, 4], horizontal=True)
    start = (wk - 1) * 7 + 1

    for i in range(7):
        pd_num = start + i
        md = meal_day(pd_num)
        day_data = MEALS[md]
        d = plan_date(pd_num)
        weekday = d.strftime("%A")
        workout = WORKOUT_SCHEDULE.get(weekday, "Rest")
        total_protein = sum(day_data[m]["protein_g"] for m in ("breakfast", "lunch", "dinner"))

        with st.expander(
            f"**{weekday} (Day {pd_num})** — "
            f"{day_data['breakfast']['name']} / {day_data['lunch']['name']} / {day_data['dinner']['name']} "
            f"— ~{total_protein}g protein"
        ):
            render_day(pd_num)

elif view == "Grocery List":
    wk = st.radio("Week", [1, 2, 3, 4], horizontal=True, key="grocery_week")
    render_grocery(wk)

elif view == "Full Plan":
    st.title("📋 Full 28-Day Plan")

    tab_meals, tab_workouts, tab_rules = st.tabs(["Meal Calendar", "Workout Schedule", "Fat Loss Rules"])

    with tab_meals:
        for wk in range(1, 5):
            st.subheader(f"Week {wk}")
            start = (wk - 1) * 7 + 1
            week_data = []
            for i in range(7):
                pd_num = start + i
                md = meal_day(pd_num)
                day_data = MEALS[md]
                d = plan_date(pd_num)
                total_p = sum(day_data[m]["protein_g"] for m in ("breakfast", "lunch", "dinner"))
                week_data.append({
                    "Day": f"{d.strftime('%a')} (Day {pd_num})",
                    "Breakfast": day_data["breakfast"]["name"],
                    "Lunch": day_data["lunch"]["name"],
                    "Dinner": day_data["dinner"]["name"],
                    "Protein": f"~{total_p}g",
                })
            st.table(week_data)

    with tab_workouts:
        st.subheader("Weekly Workout Schedule")
        for day, workout in WORKOUT_SCHEDULE.items():
            st.markdown(f"**{day}:** {workout}")

        st.divider()
        st.subheader("Workout Details")

        st.markdown("### 💪 Workout A — Lower Body + Core")
        st.markdown("- Barbell squats — 3×8\n- Romanian deadlifts — 3×10\n- Walking lunges — 3×10 each leg\n- Plank — 3×30-45 sec")

        st.markdown("### 💪 Workout B — Upper Body Push/Pull")
        st.markdown("- Dumbbell bench press — 3×8-10\n- One-arm rows — 3×10\n- Shoulder press — 3×10\n- Tricep dips — 3×10")

        st.markdown("### 💪 Workout C — Full Body")
        st.markdown("- Deadlifts — 3×5\n- Goblet squats — 3×10\n- Hip thrusts — 3×10\n- Mountain climbers — 3×20")

        st.divider()
        st.markdown("**Daily:** Walk 8-10k steps + 10-15 min walk after meals")
        st.markdown("**Recovery:** 5-10 min meditation daily (morning or evening)")

    with tab_rules:
        st.subheader("The Fat Loss Rules")
        for i, rule in enumerate(FAT_LOSS_RULES, 1):
            st.markdown(f"**{i}.** {rule}")

        st.divider()
        st.subheader("Expected Results (28 days)")
        st.markdown("- 3-6 lbs fat loss\n- Visible tightening (especially waist)\n- Better energy + fewer sugar cravings")
