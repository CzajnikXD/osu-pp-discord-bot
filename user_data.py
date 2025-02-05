import json

user_data = {}

def load_osu_user_data():
    """Load user data from a JSON file into memory."""
    global user_data
    try:
        with open("user_data.json", "r") as file:
            user_data.update(json.load(file))
    except FileNotFoundError:
        pass

def save_osu_user_data():
    """Save the in-memory user data to a JSON file."""
    with open("user_data.json", "w") as file:
        json.dump(user_data, file)

def set_osu_user(discord_user_id, value):
    """Set a value for a given user ID."""
    user_data[discord_user_id] = value
    save_osu_user_data()

def get_osu_user(discord_user_id):
    """Get the value associated with a given user ID."""
    return user_data.get(discord_user_id)