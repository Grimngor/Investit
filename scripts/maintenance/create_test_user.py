"""
Create Test User Script
Simple utility to create test users for development and testing.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.models.persistence import save_user_data, load_user_data
from app.services.auth import get_password_hash


def create_test_user(username: str, password: str):
    """Create a test user with the given credentials."""

    # Check if user already exists
    existing_user = load_user_data(username)
    if existing_user:
        print(f"❌ User '{username}' already exists!")
        return False

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create user data
    user_data = {
        "username": username,
        "hashed_password": hashed_password,
        "is_active": True,
        "holdings": [],
    }

    # Save user
    try:
        save_user_data(username, user_data)
        print(f"✅ Test user created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        return True
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        return False


def main():
    """Main function to run the script."""
    print("=" * 50)
    print("Create Test User")
    print("=" * 50)

    # Default test users
    test_users = [
        {
            "username": "test",
            "password": "test123",
        },
    ]

    # Check if specific user requested
    if len(sys.argv) > 1:
        username = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "password123"

        print(f"\nCreating custom user: {username}\n")
        create_test_user(username, password)
    else:
        # Create all default test users
        print("\nCreating default test users...\n")
        for user in test_users:
            create_test_user(**user)
            print()

    print("=" * 50)
    print("Done!")
    print("=" * 50)


if __name__ == "__main__":
    main()
