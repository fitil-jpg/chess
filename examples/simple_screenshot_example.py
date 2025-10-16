"""
Простий приклад використання автоматичного ScreenshotHelper.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.screenshot_helper_auto import take_fullscreen, take_region_screenshot, list_screenshots


def main():
    """Простий приклад використання."""
    print("Простий приклад використання ScreenshotHelper")
    print("=" * 50)
    
    # Скріншот всього екрану
    screenshot_path = take_fullscreen("simple_test", "demo_screenshot")
    print(f"Скріншот збережено: {screenshot_path}")
    
    # Скріншот області
    screenshot_path = take_region_screenshot(
        "simple_test", 
        "demo_region", 
        x=100, y=100, width=400, height=300
    )
    print(f"Скріншот області збережено: {screenshot_path}")
    
    # Показуємо всі скріншоти
    screenshots = list_screenshots()
    print(f"\nВсього скріншотів: {len(screenshots)}")
    for screenshot in screenshots[-3:]:  # Показуємо останні 3
        print(f"  - {screenshot}")


if __name__ == "__main__":
    main()