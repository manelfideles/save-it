import base64
import getpass
import hashlib
import secrets

import pandas as pd


def format_expenses_df(
    data: pd.DataFrame,
    cols: list[str] = ["type", "id", "title", "category", "amount", "date"],
) -> pd.DataFrame:
    formatted_data = data[cols]
    formatted_data["date"] = pd.to_datetime(formatted_data["date"], format="%Y-%m-%d")
    formatted_data["formatted_amount"] = formatted_data["amount"].apply(
        lambda x: f"€{x:.2f}"
    )
    return formatted_data


def generate_jwt_secret():
    # Generate a 32-byte (256-bit) random secret
    random_bytes = secrets.token_bytes(32)
    # Convert to base64 for easier handling
    secret = base64.b64encode(random_bytes).decode("utf-8")
    print("\nYour JWT secret is:")
    print(secret)
    print("\nAdd this secret to your docker-compose.yml file as JWT_SECRET")


def generate_password_hash():
    password = getpass.getpass("Enter your password: ")
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    print("\nYour password hash is:")
    print(password_hash)
    print("\nAdd this hash to your docker-compose.yml file as ADMIN_PASSWORD_HASH")


if __name__ == "__main__":
    generate_password_hash()
    generate_jwt_secret()
