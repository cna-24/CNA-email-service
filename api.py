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

    user_id = cart_data.get('user_id')
    product_data = cart_data.get('products')

    user_api_url = f'https://cna-user-api.duckdns.org/user/{user_id}'  # Update with your actual URL
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(user_api_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        email_address = user_data.get('email')
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve user email: {str(e)}'}), 500

    subject = 'Your Order Details'
    body = f'Your order with ID {cartId} has been processed. Details: {cart_data}'
    for product in product_data:
        body += f"{product.get('name')}: {product.get('quantity')}\n"

    sendgrid_url = 'https://api.sendgrid.com/v3/mail/send'
    headers = {
        'Authorization': 'Bearer ' + SENDGRID_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'personalizations': [{'to': [{'email': email_address}], 'subject': subject}],
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

