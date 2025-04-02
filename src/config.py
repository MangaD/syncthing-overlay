import configparser

CONFIG_FILE = "config.ini"

def load_api_key():
    """Load the API key from the config file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config.get("syncthing", "api_key", fallback=None)

def save_api_key(api_key):
    """Save the API key to the config file."""
    config = configparser.ConfigParser()
    config["syncthing"] = {"api_key": api_key}
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)
