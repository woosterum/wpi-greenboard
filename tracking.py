import requests
import uuid
import json

# --- Configuration ---
# Replace with your actual credentials from the UPS Developer Portal
CLIENT_ID = "HCTsyp8JsmGuiOYCkxpZAak9ZusNbA8Me9d1k5g7rmivxpoC"
CLIENT_SECRET = "bbUGGCg1q66AuEeGV66EjhcbG6GNtOGYTb1r5vqAxssUaBsovaQIKPiTWHHpAGZV"

# Replace with a valid UPS tracking number for testing
TEST_TRACKING_NUMBER = "1ZA81H440313373222"


# --- Function to get Access Token ---
def get_ups_access_token(client_id: str, client_secret: str) -> str:
    """Authenticates to get an OAuth2 access token."""
    # Use 'https://onlinetools.ups.com' for production
    token_url = "https://wwwcie.ups.com/security/v1/oauth/token"
    payload = {"grant_type": "client_credentials"}

    try:
        response = requests.post(token_url, data=payload, auth=(client_id, client_secret))
        response.raise_for_status()
        print("✅ Successfully obtained access token!")
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting access token: {e}")
        if e.response is not None:
            print(f"Error Response: {e.response.text}")
        return None


# --- Function to get Tracking Details ---
def get_tracking_details(access_token: str, tracking_number: str) -> dict:
    """Fetches tracking details for a given UPS tracking number."""
    # Use 'https://onlinetools.ups.com' for production
    track_url = f"https://onlinetools.ups.com/api/track/v1/details/{tracking_number}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "transId": str(uuid.uuid4()),  # A unique ID for the request
        "transactionSrc": "testing"
    }

    try:
        response = requests.get(track_url, headers=headers)
        response.raise_for_status()
        print(f"✅ Successfully retrieved tracking info for {tracking_number}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching tracking details: {e}")
        if e.response is not None:
            print(f"Error Response: {e.response.text}")
        return None


# --- Main execution block ---
if __name__ == "__main__":
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE" or CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
        print("🛑 Please update the script with your CLIENT_ID and CLIENT_SECRET.")
    else:
        # 1. Get the access token
        token = get_ups_access_token(CLIENT_ID, CLIENT_SECRET)

        # 2. If token was retrieved successfully, get tracking info
        if token:
            tracking_info = get_tracking_details(token, TEST_TRACKING_NUMBER)

            if tracking_info:
                # Pretty-print the JSON response
                print("\n--- Tracking Response ---")
                print(json.dumps(tracking_info, indent=2))