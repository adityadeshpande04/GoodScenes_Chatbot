from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
from enum import Enum
from twilio.rest import Client

app = Flask(__name__)


@app.route('/bot', methods=['GET', 'POST'])
def bot():
    global start
    incoming_msg = request.values.get('Body', '').lower()
    phone_number=request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()
    account_sid=request.values.get('AccountSid','')
    auth_token = 'd275cebb320e1b8706c3979992c22998'

    def send_message(message):
        # Use the Twilio client to send the custom message to the user
        client = Client(account_sid, auth_token)
        message = client.messages.create(
                from_='whatsapp:+14155238886',
                body= message,
                to=phone_number,  #'whatsapp:+919322683332'
        )
        return "Message sent successfully"
    if incoming_msg == 'hi':
        response = "Do you want to live chat?"
        msg.body(response)
        start = False
    elif incoming_msg == 'yes':
        response = "Chat started. Type 'end' to end the chat."
        msg.body(response)
        start = True
    elif incoming_msg == 'end':
        response = "Chat ended. Thank you!"
        msg.body(response)
        start = False
    elif start:
        print("user msg:" + incoming_msg)
        # Store the incoming message in the database
        msg_text = input("Enter your reply: ")
        send_message(msg_text)
        


    return str(resp)



if __name__ == '__main__':
    app.debug = True
    app.run(port=4000)
