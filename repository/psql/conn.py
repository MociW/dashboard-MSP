import psycopg2
import yaml
from yaml.loader import SafeLoader


def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = yaml.load(config_file, Loader=SafeLoader)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


class DatabaseConnection:
    def __init__(self, db_credentials):
        self.db_credentials = db_credentials
        self.connection = None

    def __enter__(self):
        # Handle different possible keys for database name
        db_name = self.db_credentials.get("database") or self.db_credentials.get("db_name")

        if not db_name:
            raise KeyError("Database name not found. Please provide either 'database' or 'db_name' in config.")

        self.connection = psycopg2.connect(
            host=self.db_credentials["host"],
            database=db_name,  # Use the found database name
            user=self.db_credentials["user"],
            password=self.db_credentials["password"],
        )
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if exc_type is not None:
                self.connection.rollback()
            else:
                self.connection.commit()
            self.connection.close()
