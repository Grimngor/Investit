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

    # Load users data
    with open(users_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Find user
    user_found = False
    for user in data.get("users", []):
        if user.get("username") == username:
            user_found = True
            holdings_count = len(user.get("portfolio", {}).get("holdings", []))

            # Clear holdings
            if "portfolio" not in user:
                user["portfolio"] = {}
            user["portfolio"]["holdings"] = []

            print(f"Cleared {holdings_count} holdings from user '{username}'")
            break

    if not user_found:
        print(f"User '{username}' not found")
        return

    # Save updated data
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {users_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "testuser"

    print(f"Clearing holdings for user: {username}")
    clear_holdings(username)
