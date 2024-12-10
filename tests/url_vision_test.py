# src/url_vision_test.py
from services.vision_service import VisionService
import json


def test_url_vision():
    vision_service = VisionService()
    test_url = "https://www.tasteofhome.com/wp-content/uploads/2018/01/Homemade-Pizza_EXPS_FT23_376_EC_120123_3.jpg"

    print("Testing Vision AI with URL...")
    results = vision_service.analyze_image_from_url(test_url)

    if results:
        print("\nAnalysis Results:")
        print(json.dumps(results, indent=2))
    else:
        print("No results found or error occurred")


if __name__ == "__main__":
    test_url_vision()