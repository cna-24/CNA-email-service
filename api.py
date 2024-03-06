from flask import Flask, request, jsonify
import requests
import jwt
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import SENDGRID_API_KEY, JWT_SECRET_KEY

app = Flask(__name__)

#####

# Route for processing an order and sending email
@app.route('/process-order/<cartId>', methods=['POST'])
def process_order(cartId):
    # Extract JWT token from request headers
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing!'}), 401

    try:
        jwt_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401

    express_api_url = f'https://cna-order-service.azurewebsites.net/cart/{cartId}'
    try:
        response = requests.get(express_api_url)
        response.raise_for_status()
        cart_data = response.json()
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve cart data: {str(e)}'}), 500

    email_address = cart_data.get('email')
    subject = 'Your Order Details'
    body = f'Your order with ID {cartId} has been processed. Details: {cart_data}'

    # Send email using SendGrid
    sendgrid_url = 'https://api.sendgrid.com/v3/mail/send'
    headers = {
        'Authorization': 'Bearer ' + SENDGRID_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        #'personalizations': [{'to': [{'email': email_address}], 'subject': subject}],
        'personalizations': [{'to': [{'email': 'sebbasisak2@gmail.com'}], 'subject': subject}],
        'from': {'email': 'isak.sebbas@arcada.fi'},
        'content': [{'type': 'text/plain', 'value': body}]
    }
    try:
        response = requests.post(sendgrid_url, json=payload, headers=headers)
        response.raise_for_status()
        sendgrid_response = response.json()
    except Exception as e:
        return jsonify({'error': f'Kunde inte skicka e-postmeddelandet:: {str(e)}'}), 500

    # Return success response
    return jsonify({'message': 'Beställning gått igenom och sändning av meddelandet lyckades.'}), 200

if __name__ == '__main__':
    app.run(debug=True)


# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
    
'''
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='from_email@example.com',
    to_emails='to@example.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
try:
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)
    
'''