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

OUTPUT=$(python3 meal_planning_agent.py today)
echo "$OUTPUT"

# On Sunday, also show next week's grocery list
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    GROCERY=$(python3 meal_planning_agent.py grocery)
    echo ""
    echo "=========================================="
    echo "  WEEKLY GROCERY LIST (prep for the week!)"
    echo "=========================================="
    echo ""
    echo "$GROCERY"
    OUTPUT="$OUTPUT"$'\n\n'"$GROCERY"
fi

# --- Send notification ---
# Uncomment ONE of the options below:

# Option A: macOS desktop notification
# osascript -e "display notification \"Check meal_plan.log for details\" with title \"Today's Meal Plan Ready\""

# Option B: Linux desktop notification
# notify-send "Today's Meal Plan Ready" "Check meal_plan.log for details"

# Option C: Email (requires mail/sendmail configured)
# echo "$OUTPUT" | mail -s "Meal Plan — $(date '+%A %B %d')" you@email.com
