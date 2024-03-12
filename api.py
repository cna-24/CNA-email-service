from flask import Flask, request, jsonify
import jwt
import requests
from config import SENDGRID_API_KEY, JWT_SECRET_KEY, TOKEN

app = Flask(__name__)

def send_order_confirmation_email(email_address, order_data):
    """
    Sends an order confirmation email to the specified address.
    """
    subject = 'Your Order Details'
    body = f'Your order has been processed. Details: {order_data}'
    for product in order_data['products']:
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
        return sendgrid_response
    except Exception as e:
        print(f'SendGrid response: {response.text}')
        print(f'Failed to send email: {e}')
        return None

@app.route('/process-order', methods=['POST'])
def process_order():
    token_header = request.headers.get('Authorization', None)
    if not token_header:
        return jsonify({'error': 'Token is missing!'}), 401

    try:
        token_type, token = token_header.split()
        if token_type.lower() != 'bearer':
            return jsonify({'error': 'Authorization header must start with Bearer'}), 401
    except ValueError:
        return jsonify({'error': 'Bearer token malformed'}), 401

    try:
        jwt_payload = jwt.decode(token, TOKEN, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token!'}), 401

    order_data = request.json.get('orderData', {})
    # Extract email directly from the JWT payload
    email_address = jwt_payload.get('email')  # Assuming 'email' claim exists in JWT

    if email_address is None:
        return jsonify({'error': 'Email not found in JWT payload'}), 400

    sendgrid_response = send_order_confirmation_email(email_address, order_data)
    if sendgrid_response is None:
        return jsonify({'error': 'Failed to send order confirmation email'}), 500

    return jsonify({'message': 'Order processed successfully, email sent.', 'sendgrid_response': sendgrid_response}), 200

if __name__ == '__main__':
    app.run(debug=True)
