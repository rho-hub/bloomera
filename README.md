# bloomera
A modern e-commerce platform for flower purchases, featuring M-Pesa payments (Daraja API) and MongoDB database integration.

Features

- Flower Catalog with image carousels
- Shopping Cart with local storage
- Checkout System with:
  - M-Pesa (Daraja API) integration
  - Credit card payment simulation
- Order Management with MongoDB
- Responsive Design for all devices

Installation

Prerequisites
- Python 3.9+
- MongoDB 5.0+
- M-Pesa Daraja API credentials

Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bloomera.git
   cd bloomera
2. install dependencies
   
4. Configure environment variables (create .env file):
SECRET_KEY=your_flask_secret_key
MONGO_URI=mongodb://localhost:27017/bloomera_db
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_PASSKEY=your_passkey
MPESA_SHORTCODE=your_shortcode

5. Run the application:
```bash
python app.py
