from flask import Flask, request, jsonify
import jwt
import requests
from config import SENDGRID_API_KEY, JWT_SECRET_KEY, TOKEN

app = Flask(__name__)

def get_user_email(user_id, token):
    """
    Retrieves the user's email from the User Service API.
    """
    user_api_url = f'https://cna-user-api.duckdns.org/user/{user_id}'
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(user_api_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        return user_data.get('email')
    except Exception as e:
        print(f'Error retrieving user email: {e}')
        return None

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
    user_id = jwt_payload.get('id')
    email_address = get_user_email(user_id, token)

    if email_address is None:
        return jsonify({'error': 'Failed to retrieve user email'}), 500

    sendgrid_response = send_order_confirmation_email(email_address, order_data)
    if sendgrid_response is None:
        return jsonify({'error': 'Failed to send order confirmation email'}), 500

    return jsonify({'message': 'Order processed successfully, email sent.', 'sendgrid_response': sendgrid_response}), 200

if __name__ == '__main__':
    app.run(debug=True)
