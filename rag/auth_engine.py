import os
import json
import hashlib
import secrets
import hmac

class AuthEngine:
    def __init__(self, db_path="data/users.json"):
        self.db_path = db_path
        # Ensure the data directory and users file exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_users(self) -> dict:
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_users(self, users: dict):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    def register(self, username: str, password: str) -> tuple[bool, str]:
        username = username.strip().lower()
        if not username or not password:
            return False, "Username and password cannot be empty."

        users = self._load_users()
        if username in users:
            return False, "User already exists. Please login."

        # 🔥 UPGRADE 1: Generate a secure, random "salt" specific to this user
        salt = secrets.token_hex(16)
        
        # 🔥 UPGRADE 2: Key Stretching using PBKDF2 (100,000 iterations)
        # This makes it mathematically too slow for hackers to brute-force or use Rainbow Tables.
        key = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        ).hex()

        users[username] = {
            "salt": salt,            # We must save the salt alongside the hash!
            "password_hash": key,
            "created_at": os.popen('date /t').read().strip() if os.name == 'nt' else "Now"
        }
        self._save_users(users)
        return True, "Registration successful!"

    def login(self, username: str, password: str) -> tuple[bool, str]:
        username = username.strip().lower()
        users = self._load_users()

        if username not in users:
            return False, "Username not found."

        # 1. Retrieve the user's specific salt and stored hash
        stored_salt = users[username]["salt"]
        stored_hash = users[username]["password_hash"]

        # 2. Hash the incoming password attempt using their stored salt
        test_key = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            stored_salt.encode('utf-8'), 
            100000
        ).hex()

        # 🔥 UPGRADE 3: Use hmac.compare_digest instead of "=="
        # This prevents "Timing Attacks" where hackers measure the milliseconds 
        # it takes to fail a password check to guess the characters.
        if hmac.compare_digest(stored_hash, test_key):
            return True, f"Welcome back, {username.capitalize()}!"
        else:
            return False, "Incorrect password."