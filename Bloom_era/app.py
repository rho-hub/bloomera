from flask import Flask, render_template, request, jsonify, session
from pymongo import MongoClient
from bson.objectid import ObjectId  # Added for ObjectId handling
import requests
from datetime import datetime
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "your-secret-key-here"

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["bloomera_db"]
orders_collection = db["orders"]
customers_collection = db["customers"]
products_collection = db["products"]

# M-Pesa Credentials
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL") or "https://yourdomain.com/callback"

def get_mpesa_access_token():
    """Get M-Pesa API access token"""
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = base64.b64encode(f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"M-Pesa token error: {str(e)}")
        return None

@app.route("/")
def home():
    return render_template("base.html")

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "GET":
        return render_template("checkout.html")
    
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        # Basic validation
        if not data.get("phone") or not data.get("email"):
            return jsonify({"success": False, "message": "Phone and email are required"}), 400

        # Create order document
        order = {
            "customer_email": data["email"],
            "customer_phone": data["phone"],
            "items": data.get("cart", []),
            "total_amount": sum(item["price"] * item["quantity"] for item in data.get("cart", [])),
            "status": "pending",
            "created_at": datetime.now(),
            "payment_method": data.get("payment_method", "unknown")
        }

        # Insert into MongoDB
        result = orders_collection.insert_one(order)
        order_id = str(result.inserted_id)

        # Process payment
        payment_method = data.get("payment_method")
        
        if payment_method == "mpesa":
            # Validate phone format
            phone = data["phone"]
            if not phone.startswith("254") or len(phone) != 12:
                return jsonify({
                    "success": False,
                    "message": "Invalid phone format. Use 2547XXXXXXXX"
                }), 400

            # Initiate M-Pesa payment
            access_token = get_mpesa_access_token()
            if not access_token:
                return jsonify({
                    "success": False,
                    "message": "Failed to get M-Pesa access token"
                }), 500

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()
            
            payload = {
                "BusinessShortCode": MPESA_SHORTCODE,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": order["total_amount"],
                "PartyA": phone,
                "PartyB": MPESA_SHORTCODE,
                "PhoneNumber": phone,
                "CallBackURL": MPESA_CALLBACK_URL,
                "AccountReference": f"ORDER{order_id}",
                "TransactionDesc": "Flower purchase"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(
                    "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                return jsonify({
                    "success": True,
                    "message": "M-Pesa payment initiated. Check your phone.",
                    "order_id": order_id
                })
            except requests.exceptions.RequestException as e:
                return jsonify({
                    "success": False,
                    "message": f"M-Pesa API error: {str(e)}"
                }), 500

        elif payment_method == "card":
            return jsonify({
                "success": True,
                "message": "Order placed (card payment simulated)",
                "order_id": order_id
            })

        else:
            return jsonify({
                "success": False,
                "message": "Invalid payment method"
            }), 400

    except Exception as e:
        print(f"Checkout error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred during checkout"
        }), 500

@app.route("/payment/callback", methods=["POST"])
def payment_callback():
    """Handle M-Pesa payment callback"""
    try:
        data = request.json
        if data.get("ResultCode") == 0:  # Success
            account_ref = data.get("AccountReference", "")
            order_id = account_ref.replace("ORDER", "")
            
            orders_collection.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"status": "paid"}}
            )
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})
    except Exception as e:
        print(f"Callback error: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)