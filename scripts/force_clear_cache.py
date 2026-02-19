#!/usr/bin/env python3
"""Force clear TODAY cache"""

from app.routes_telegram import TODAY_CACHE

print("=" * 60)
print("Clearing TODAY_CACHE")
print("=" * 60)

# Access internal store
if hasattr(TODAY_CACHE, "_store"):
    print(f"Cache size before: {len(TODAY_CACHE._store)} items")

    # Show some cached keys
    if TODAY_CACHE._store:
        print("\nSample cached keys:")
        for i, key in enumerate(list(TODAY_CACHE._store.keys())[:5]):
            print(f"  {i+1}. {key}")

    # Clear the cache
    TODAY_CACHE._store.clear()

    print(f"\nCache size after: {len(TODAY_CACHE._store)} items")
    print("\n✅ Cache cleared successfully!")
else:
    print("❌ Cannot access cache _store")

print("=" * 60)
print("\n📱 Test users can now request /today in Telegram")
print("   to get fresh digest with correct Russian encoding.")
print("=" * 60)
