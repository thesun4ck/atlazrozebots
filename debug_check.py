import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from database.db import get_bouquets, get_favorites

async def main():
    print("Checking database...")
    try:
        bouquets = await get_bouquets()
        print(f"Bouquets found: {len(bouquets)}")
        for b in bouquets:
            print(f" - {b['name']} ({b['id']})")
            if 'image_path' in b:
                if os.path.exists(b['image_path']):
                    print(f"   Image OK: {b['image_path']}")
                else:
                    print(f"   Image MISSING: {b['image_path']}")
    except Exception as e:
        print(f"Error getting bouquets: {e}")

    print("\nChecking imports...")
    try:
        from handlers import client
        print("Handlers imported successfully.")
    except Exception as e:
        print(f"Error importing handlers: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
