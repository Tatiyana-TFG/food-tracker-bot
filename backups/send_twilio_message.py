from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load Twilio credentials from environment variables
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

# Check if credentials are loaded properly
if not account_sid or not auth_token:
    print("Error: Twilio credentials are missing. Please check your .env file.")
    exit()

# Create the Twilio client
client = Client(account_sid, auth_token)

# Replace these with your Twilio Sandbox details
from_number = 'whatsapp:+14155238886'  # Twilio Sandbox number
to_number = 'whatsapp:+12403166242'    # Replace with your verified WhatsApp number
message_body = 'Hello from the Food Tracker bot!'

try:
    # Send the message
    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number
    )
    print(f'Message sent successfully! Message SID: {message.sid}')
except Exception as e:
    print(f"Failed to send message: {e}")
