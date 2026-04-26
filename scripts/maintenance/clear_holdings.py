"""
Utility script to clear all holdings from a test user's portfolio.
Useful for development/testing to reset portfolio state.
"""

import json
from pathlib import Path


def clear_holdings(username: str = "testuser"):
    """Clear all holdings from specified user's portfolio."""
    data_dir = Path(__file__).parent / "data"
    users_file = data_dir / "users.json"

    if not users_file.exists():
        print(f"Users file not found: {users_file}")
        return

    # Load users data (new structure: dict of users, not array)
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)

    # Find user in dict
    if username not in users:
        print(f"User '{username}' not found")
        return

    user = users[username]
    holdings_count = len(user.get("holdings", []))

    # Clear holdings
    user["holdings"] = []

    print(f"Cleared {holdings_count} holdings from user '{username}'")

    # Save updated data
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

    print(f"Saved to {users_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "testuser"

    print(f"Clearing holdings for user: {username}")
    clear_holdings(username)
