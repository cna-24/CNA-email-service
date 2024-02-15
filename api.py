# api.py

from flask import Flask, request, jsonify
import requests
import jwt
from config import SENDGRID_API_KEY, JWT_SECRET_KEY

app = Flask(__name__)

# Define the endpoint to receive data and send email
@app.route('/send_email', methods=['POST'])
def send_email():
    # Get JWT token from request headers
    token = request.headers.get('Authorization')

    # Verify JWT token
    if not token:
        return jsonify({'error': 'Token is missing!'}), 401

    try:
        # Decode JWT token and verify
        jwt_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401

    # Get data from request
    data = request.get_json()

    # Extract email data
    email_address = data.get('email_address')
    subject = data.get('subject')
    body = data.get('body')

    # Call function to send email
    sendgrid_response = send_email_with_sendgrid(email_address, subject, body)

    return jsonify(sendgrid_response)

# Function to send email using SendGrid service
def send_email_with_sendgrid(email_address, subject, body):
    sendgrid_url = 'https://api.sendgrid.com/v3/mail/send'

    headers = {
        'Authorization': 'Bearer ' + SENDGRID_API_KEY,
        'Content-Type': 'application/json'
    }

    payload = {
        'personalizations': [{
            'to': [{'email': email_address}],
            'subject': subject
        }],
        'from': {'email': 'your@email.com'},
        'content': [{'type': 'text/plain', 'value': body}]
    }

    response = requests.post(sendgrid_url, json=payload, headers=headers)

    return response.json()

if __name__ == '__main__':
    app.run(debug=True)
