import json

lazer_data = {}

def load_user_lazer_data():
    """Load user data from a JSON file into memory."""
    global lazer_data
    try:
        with open("lazer_data.json", "r") as file:
            lazer_data.update(json.load(file))
    except FileNotFoundError:
        pass

def save_user_lazer_data():
    """Save the in-memory user data to a JSON file."""
    with open("lazer_data.json", "w") as file:
        json.dump(lazer_data, file)

def set_user_lazer(discord_user_id, value):
    """Set a value for a given user ID."""
    lazer_data[discord_user_id] = value
    save_user_lazer_data()

def get_user_lazer(discord_user_id):
    """Get the value associated with a given user ID."""
    return lazer_data.get(discord_user_id)