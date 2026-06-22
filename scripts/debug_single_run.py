from main import run
from outlook_accounts import OUTLOOK_ACCOUNTS
import time

def debug_one():
    # Use the first account.
    account = OUTLOOK_ACCOUNTS[0]
    print(f"🐞 Starting single-thread debug run: {account['email']}")
    print("👀 Watch the browser behavior...")
    
    # Run.
    try:
        run(fixed_account=account)
    except Exception as e:
        print(f"❌ Run error: {e}")

if __name__ == "__main__":
    debug_one()
