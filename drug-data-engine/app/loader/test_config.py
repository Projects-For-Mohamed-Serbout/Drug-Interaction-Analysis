import requests

BASE_URL = "http://localhost:8000"


def test_get_medication_by_id():
    item_id = "6811f6a57d9db0f580a220f8"  # Replace with an actual ID in your DB
    url = f"{BASE_URL}/medications/{item_id}"

    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.ok:
            print("✅ Medication found:")
            print(response.json())
        else:
            print("❌ Error:", response.text)

    except requests.exceptions.RequestException as e:
        print("❌ Connection error:", e)


if __name__ == "__main__":
    test_get_medication_by_id()
