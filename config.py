"""
Configuration file for NL2SQL Assistant
Edit these settings to match your PostgreSQL setup
"""

import json
from pathlib import Path

class Config:
    """Application configuration"""

    DEFAULT_CONFIG = {
        'database': {
            'dbname': 'nl2sql_db',
            'user': 'postgres',
            'password': 'postgres',  # Change this to your PostgreSQL password
            'host': 'localhost',
            'port': 5432
        },
        'models': {
            'llm': 'google/flan-t5-base',  # Lightweight model for NL2SQL
            'embeddings': 'sentence-transformers/all-MiniLM-L6-v2',
            'whisper': 'base'  # Options: tiny, base, small, medium, large
        },
        'voice': {
            'recording_duration': 5,  # seconds
            'tts_rate': 150,  # words per minute
            'tts_volume': 0.9
        },
        'ui': {
            'theme': 'light',
            'window_width': 1000,
            'window_height': 700
        }
    }

    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file or use defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    return {**self.DEFAULT_CONFIG, **loaded}
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, *keys):
        """Get nested config value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, {})
            else:
                return None
        return value

    def set(self, value, *keys):
        """Set nested config value"""
        if len(keys) == 1:
            self.config[keys[0]] = value
        else:
            current = self.config
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = value
        self.save_config()

# Create default config instance
config = Config()

# Database configuration (for easy import)
DB_CONFIG = config.get('database')

