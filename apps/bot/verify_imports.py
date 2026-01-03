import sys
import os
import traceback

# Add project root to path
sys.path.append(os.getcwd())

extensions = [
    'apps.bot.cogs.moderation',
    'apps.bot.cogs.automod',
    'apps.bot.cogs.utility', 
    'apps.bot.cogs.advanced_utils',
    'apps.bot.cogs.logging',
    'apps.bot.cogs.antiraid',
    'apps.bot.cogs.social_features',
    'apps.bot.cogs.leveling', 
    'apps.bot.cogs.tickets',
    'apps.bot.cogs.embed_builder',
    'apps.bot.cogs.economy',
    'apps.bot.cogs.report',
    'apps.bot.cogs.welcome',
    'apps.bot.cogs.audit_logging',
    'apps.bot.cogs.advanced_automod',
    'apps.bot.cogs.jail',
    'apps.bot.cogs.fun',
    'apps.bot.cogs.suggestions',
    'apps.bot.cogs.extended_utility',
    'apps.bot.cogs.reaction_roles',
    'apps.bot.cogs.governance.pipeline',
    'apps.bot.cogs.governance.safe_mode',
    'apps.bot.cogs.governance.tickets_v2',
    'apps.bot.cogs.access_key',
]

print("🔍 Verifying Extension Imports...")
failures = 0

for ext in extensions:
    try:
        # Try to import the module
        __import__(ext, fromlist=[''])
        print(f"✅ OK: {ext}")
    except Exception as e:
        print(f"❌ FAIL: {ext}")
        traceback.print_exc()
        failures += 1

if failures == 0:
    print("\n🎉 All extensions are importable!")
else:
    print(f"\n⚠️ Found {failures} broken extensions.")
