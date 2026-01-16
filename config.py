import json
from pathlib import Path

class Config:

    DEFAULT_CONFIG = {
        'database': {
            'dbname': 'nl2sql_db',
            'user': 'postgres',
            'password': 'postgres',
            'host': 'localhost',
            'port': 5432
        },
        'models': {
            'llm': 'qwen2.5-coder:7b-instruct-q4_K_M',
            'whisper': 'large-v3'
        },
        'voice': {
            'recording_duration': 5
        },
        'ui': {
            'theme': 'dark',
            'window_width': 1300,
            'window_height': 850
        }
    }

    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.config = self.load_config()

    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    return {**self.DEFAULT_CONFIG, **loaded}
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, *keys):
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, {})
            else:
                return None
        return value

    def set(self, value, *keys):
        if len(keys) == 1:
            self.config[keys[0]] = value
        else:
            current = self.config
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = value
        self.save_config()

config = Config()

DB_CONFIG = config.get('database')
