from flask import Flask, request, jsonify
import psycopg2
import random
import string
from datetime import datetime

app = Flask(__name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",           # or your Render/AWS host
        database="laptakecare",
        user="postgres",
        password="gaurav"
    )

# Generate token ID
def generate_token():
    return "LTC" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def home():
    return "LapTake Care Webhook is Running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req.get('queryResult').get('intent').get('displayName')

    if intent == 'BookRepairIntent':
        return handle_booking(req)
    elif intent == 'TrackStatusIntent':
        return handle_tracking(req)
    else:
        return jsonify({'fulfillmentText': 'Sorry, I did not understand that.'})

def handle_booking(req):
    params = req['queryResult']['parameters']
    fname = params.get('fname')
    address = params.get('address')
    phone_no = params.get('phone_no')
    device_issue = params.get('device_issue')
    repaired_status = "Pending"
    token_id = generate_token()
    date_created = datetime.now()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO repair_bookings (token_id, fname, address, phone_no, device_issue, repaired_status, date_created)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (token_id, fname, address, phone_no, device_issue, repaired_status, date_created))
    conn.commit()
    cur.close()
    conn.close()

    reply = f"✅ Thank you {fname}! Your repair booking is confirmed.\nYour Token ID is **{token_id}**.\nWe’ll contact you soon."
    return jsonify({'fulfillmentText': reply})

def handle_tracking(req):
    params = req['queryResult']['parameters']
    token_id = params.get('token_id')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT fname, device_issue, repaired_status, repair_details, charges FROM repair_bookings WHERE token_id=%s", (token_id,))
    record = cur.fetchone()
    cur.close()
    conn.close()

    if record:
        fname, device_issue, repaired_status, repair_details, charges = record
        details = repair_details if repair_details else "Still under process"
        charges_text = f"₹{charges}" if charges else "Not updated yet"
        reply = f"🔍 Repair Status for {token_id}:\n👤 Name: {fname}\n💻 Issue: {device_issue}\n📦 Status: {repaired_status}\n🧰 Work Done: {details}\n💵 Charges: {charges_text}"
    else:
        reply = f"❌ No record found for Token ID {token_id}. Please check and try again."

    return jsonify({'fulfillmentText': reply})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
