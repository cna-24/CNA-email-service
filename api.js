const express = require('express');
const cors = require('cors');
require('dotenv').config(); 
const jwt = require('jsonwebtoken');
const axios = require('axios');

const PORT = process.env.PORT || 8080;

const app = express();
app.use(cors());
app.use(express.json());
async function sendOrderConfirmationEmail(emailAddress, orderData) {
    const subject = 'Your Order Details';

    console.log(orderData)
    let body = `Your order has been processed. Details:\n`;
    let totalPrice = 0;
    // Iterate through each row in orderData.rows
    orderData.rows.forEach(row => {
        body += `${row.product}: ${row.quantity} x ${row.price}€\n`; // Assuming product name, quantity, and price are available
        totalPrice += row.quantity * row.price; // Calculate total price
    });

    body += `\nTotal Price: ${totalPrice}€\n`;
    // Add additional order details to the email body
    body += `\nOrder ID: ${orderData.id}\n`;
    body += `User ID: ${orderData.user_id}\n`;
    body += `Username: ${orderData.username}\n`;
    body += `Date: ${orderData.date}\n`;
    body += `Address: ${orderData.address}\n`;

    const sendgridUrl = 'https://api.sendgrid.com/v3/mail/send';

    const payload = {
        personalizations: [{ to: [{ email: emailAddress }], subject: subject }],
        from: { email: 'isak.sebbas@arcada.fi' },
        content: [{ type: 'text/plain', value: body }]
    };

    try {
        const response = await axios.post(sendgridUrl, payload, { headers: {
            Authorization: `Bearer ` + process.env.SENDGRID_API_KEY,
        }});
        
        // Customize the response data
        const responseData = {
            success: true,
            message: 'Confirmation sent successfully',
            data: {
                email: emailAddress,
                orderData: orderData
                
            }
        };

        //console.log('SendGrid response:', response.data); // Log the response data
        return responseData; // Return the custom response data
    } catch (error) {
        //console.error('Failed to send email:', error);
        
        // Customize the error response data
        const errorResponse = {
            success: false,
            message: 'Failed to send email',
            error: error.message // Include the error message
        };

        throw errorResponse; // Throw the error response
    }
}





app.post('/process-order', async (req, res) => {
    const authHeader = req.headers['authorization'];
    if (!authHeader) {
        return res.status(401).json({ error: 'No Authorization header found' });
    }

    const token = authHeader.split(' ')[1];
    if (!token) {
        return res.status(401).json({ error: 'Bearer token not found' });
    }

    try {
        const authUser = jwt.verify(token, process.env.TOKEN);
        console.log(authUser);

        const orderData = req.body.orderData || {};
        req.authUser = authUser;
        //console.log(req.authUser.email);
        const emailAddress = req.authUser.email;
        console.log(orderData);

        if (!emailAddress) {
            return res.status(400).json({ error: 'Email not found in JWT payload' });
        }

        // Wait for the sendOrderConfirmationEmail function to complete
        const sendgridResponse = await sendOrderConfirmationEmail(emailAddress, orderData);
        
        // If sendOrderConfirmationEmail resolves successfully, include the response in the JSON
        return res.status(200).json({ message: 'Order processed successfully.', sendgridResponse });

    } catch (error) {
        if (error instanceof jwt.TokenExpiredError) {
            return res.status(401).json({ error: 'Token has expired!' });
        }
        return res.status(401).json({ error: 'Invalid token!' });
    }
});


app.use('/', express.static(__dirname + '/public/'));
app.listen(PORT, () => {
    console.log(`Server listening on http://localhost:${PORT}`);
});