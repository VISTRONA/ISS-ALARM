import os
import requests
import smtplib
import email.message as email_message
from datetime import datetime

# --- CONFIGURATION (via Environment Variables) ---
USER_LAT = float(os.environ.get("USER_LATITUDE", 18.5204))
USER_LNG = float(os.environ.get("USER_LONGITUDE", 73.8567))

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# Expects a comma-separated string: "email1@example.com, email2@example.com"
RECIPIENT_RAW = os.environ.get("RECIPIENT_EMAIL", "")
RECIPIENT_LIST = [email.strip() for email in RECIPIENT_RAW.split(",") if email]

# --- CONSTANTS ---
# +/- 400*sin(5) / 1 unit lat/long approx
LAT_MIN = USER_LAT - 0.313799
LAT_MAX = USER_LAT + 0.313799
LNG_MIN = USER_LNG - 0.330281
LNG_MAX = USER_LNG + 0.330281


def is_iss_overhead():
    """Checks if the ISS is currently within the user's coordinate range."""
    response = requests.get("http://api.open-notify.org/iss-now.json")
    response.raise_for_status()
    data = response.json()

    iss_lat = float(data["iss_position"]["latitude"])
    iss_lng = float(data["iss_position"]["longitude"])

    return LAT_MIN <= iss_lat <= LAT_MAX and LNG_MIN <= iss_lng <= LNG_MAX


def is_night_time():
    """Checks if it is currently dark at the user's location."""
    sun_params = {
        "lat": USER_LAT,
        "lng": USER_LNG,
        "formatted": 0,
    }
    response = requests.get("https://api.sunrisesunset.io/json", params=sun_params)
    response.raise_for_status()
    data = response.json()

    # Extracting hour and minute from ISO 8601 strings
    # Example format: "2024-05-22T05:45:12+00:00"
    sunrise_str = data["results"]["sunrise"].split("T")[1]
    sunset_str = data["results"]["sunset"].split("T")[1]

    sunrise_time = (int(sunrise_str.split(":")[0]), int(sunrise_str.split(":")[1]))
    sunset_time = (int(sunset_str.split(":")[0]), int(sunset_str.split(":")[1]))

    now = datetime.now()
    current_time = (now.hour, now.minute)

    return current_time <= sunrise_time or current_time >= sunset_time


def send_emails():
    """Logs into SMTP and sends a personalized email to every recipient."""
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for recipient in RECIPIENT_LIST:
                msg = email_message.EmailMessage()
                msg['Subject'] = "ISS is in your area! Look Up! 🚀"
                msg['From'] = SENDER_EMAIL
                msg["To"] = recipient
                msg.set_content(
                    f"Hey! The International Space Station is passing over your area right now. It's dark enough to see it—go take a look!")

                server.send_message(msg)
                print(f"Successfully notified: {recipient}")
    except Exception as e:
        print(f"SMTP Error: {e}")


# --- EXECUTION LOGIC ---
if __name__ == "__main__":
    if is_night_time():
        print("It's currently night time. Checking ISS position...")
        if is_iss_overhead():
            print("ISS is overhead! Sending notifications...")
            send_emails()
        else:
            print("ISS is not in range.")
    else:
        print("It's currently daytime. ISS wouldn't be visible anyway.")