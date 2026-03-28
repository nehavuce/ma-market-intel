#!/usr/bin/env bash
# Daily Meal Plan Notification Script
# Runs via cron every morning — shows today's meals
# On Sundays, also prints the weekly grocery list

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday

echo "=========================================="
echo "  DAILY MEAL PLAN — $(date '+%A, %B %d %Y')"
echo "=========================================="
echo ""

python3 meal_planning_agent.py today

# On Sunday, also show next week's grocery list
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    echo ""
    echo "=========================================="
    echo "  WEEKLY GROCERY LIST (prep for the week!)"
    echo "=========================================="
    echo ""
    python3 meal_planning_agent.py grocery
fi
