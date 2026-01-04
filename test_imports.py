#!/usr/bin/env python
"""Test all project imports"""

import sys

sys.path.insert(0, ".")

print("Testing imports...")
try:
    from apps.api.main import app

    print("  API main: OK")
except Exception as e:
    print(f"  API main: FAIL - {e}")

try:
    from apps.api.router import auth, guilds, modules, guilds_v2

    print("  API routers: OK")
except Exception as e:
    print(f"  API routers: FAIL - {e}")

try:
    from apps.api.auth import get_me

    print("  API auth: OK")
except Exception as e:
    print(f"  API auth: FAIL - {e}")

try:
    from apps.bot.main import LithiumBot

    print("  Bot: OK")
except Exception as e:
    print(f"  Bot: FAIL - {e}")

try:
    from lithium_core.models import User, OAuthSession

    print("  Models: OK")
except Exception as e:
    print(f"  Models: FAIL - {e}")

print("\nDone!")
