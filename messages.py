from services.tools.time_calc import days_until_new_year
from services.api.qoute import get_random_quoute

# Start -------------------
commands_description = """
1. /subscribe - enable subscription.
2. /reset - cancel subscription.

🔧 Administrative commands:
   /stats - statistics.
   /help - get a list of all commands.
"""

start = f"""Hey!

🚀 Quick start:
{commands_description}
"""

# Registration process -------------------
subscribed_successfully = """
                  🎉 Great, now you are ready to receive daily motivation!
"""

subscribed_already = "You are already subscribed to the newsletter."

reset_successfully = "Subscription successfully canceled."

# Errors -------------------
smth_went_wrong = "⚠️ Something went wrong."

unknown_command = "Sorry, I don't understand this command."

not_admin = "⚠️ You do not have permission for this command."

def get_daily_motivation_message() -> str:
   amout_of_days = days_until_new_year()

   days_form = 'days' if amout_of_days != 1 else 'day'
   verb_form = 'are' if amout_of_days != 1 else 'is'

   message = f"""
<blockquote>{get_random_quoute()}</blockquote>

There {verb_form} <code>{amout_of_days}</code> {days_form} left until the New Year.
"""
   return message