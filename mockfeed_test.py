import requests
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/person-count/"

print(f"Starting API test script. Polling {API_URL}")
print("Press CTRL+C to stop.")

while True:
    try:
        # Make a request to our Django API
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Get the count from the JSON response
        data = response.json()
        count = data.get("person_count", "N/A")

        # Get the current time for the log
        timestamp = datetime.now().strftime("%I:%M:%S %p")

        print(f"[{timestamp}] Request successful. Person count: {count}")

    except requests.exceptions.RequestException as e:
        print(f"Could not connect to the server: {e}")
    except KeyError:
        print("Received invalid data from server.")

    # Wait for 3 seconds before the next request
    time.sleep(3)