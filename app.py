import json
from datetime import datetime as dt
from flask import Flask, request
import db

DB = db.DatabaseDriver()

def success_response(message, code = 200):
    return json.dumps(message), code

def error_response(message, code = 404):
    return json.dumps(message), code

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello world!"


# your routes here
@app.route("/api/users/")
def get_all_users():
    """Get all users

    Returns:
        a jason of all users in the database
    """
    users = {"users": DB.get_users()}
    return success_response(users)


@app.route("/api/users/", methods= ["POST"])
def create_user():
    """create a new user

    Returns:
        a json of the new user created
    """
    body = json.loads(request.data)
    print(body)
    name = body.get('name')
    if name is None:
        return error_response({"error": "Provide a name!"})
    username = body.get('username')
    if username is None:
        return error_response({"error": "Provide a username!"})
    balance = body.get('balance', 0)
    user_id = DB.create_user(name, username, balance)
    user = DB.get_specific_user(user_id)
    user['transactions'] = []
    
    return success_response(user, 201)


@app.route("/api/users/<int:id>/")
def get_specific_user(id):
    """get a specific user

    Args:
        id (int): the id of the user whose information is to be retrieved

    Returns:
        a json of the specific user by id
    """
    user = DB.get_specific_user(id)
    if user is None:
        return error_response({"error": "User not found!"})
    return success_response(user, 200)


@app.route("/api/users/<int:id>/", methods = ["DELETE"])
def delete_user(id):
    """delete a user form the databse

    Args:
        id (int): the id of the user to be deleted

    Returns:
        json: a json of the user that has been deleted
    """
    user = DB.get_specific_user(id)
    if user is None:
        return error_response({"error": "User not found!"})
    else:
        DB.delete_user(id)
        return success_response(user, 200)
    

@app.route("/api/transactions/", methods = ["POST"])
def create_transaction():
    body = json.loads(request.data)
    print(body)
    sender_id = body.get('sender_id')
    receiver_id = body.get('receiver_id')
    amount = body.get('amount')
    message = body.get('message')
    status = body.get('accepted')
    timestamp = str(dt.now())
    sender = DB.get_specific_user(sender_id)
    if sender is not None:
        sender_balance = DB.get_sender_balance(sender_id)
        if amount is not None:
            if sender_balance < amount:
                return error_response({"error": "Insufficient balance"}, 403)
            receiver = DB.get_specific_user(receiver_id)
            if receiver is not None:
                if status == True:
                    DB.send_amount(sender_id, receiver_id, amount)
                response = {
                    "id": DB.create_transaction(timestamp, sender_id, receiver_id, amount, message, status),
                    "timestamp": timestamp,
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "amount": amount,
                    "message": message,
                    "accepted": status
                }
                    
                return success_response(response, 201)
            else:
                return error_response({"error": "Receiver not found!"}, 404)
        else:
            return error_response({"error": "Provide amount to send!"}, 404)
    return error_response({"error": "Sender not found!"}, 404)


@app.route("/api/transactions/<int:transaction_id>/" , methods=["POST"])
def update_transaction(transaction_id):
    body = json.loads(request.data)
    print(body)
    status = body.get("accepted")
    print(status)
    timestamp = str(dt.now())
    transaction = DB.get_specific_transaction(transaction_id)
    if transaction is None:
        return error_response({"error": "Transaction not found!"}, 404)
    result = DB.update_transaction(transaction_id, bool(status), timestamp)
    if result is None:
        return error_response(transaction, 403)
    transaction = DB.get_specific_transaction(transaction_id)
    if result == False:
        return error_response(transaction, 200)
    elif result == "failed":
        return error_response({"error": "Insufficient balance"}, 201)
    elif result == True:
        return success_response(transaction, 200)

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
