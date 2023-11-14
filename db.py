import os
import sqlite3
import json

# From: https://goo.gl/YzypOI
def singleton(cls):
    """prevents the initialization of multiple instances of the database
    """
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class DatabaseDriver(object):
    """
    Database driver for the Venmo app.
    Handles with reading and writing data with the database.
    """

    def __init__(self):
        self.conn = sqlite3.connect('venmo.db', check_same_thread= False)
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.create_users_table()
        self.create_transactions_table()
        
      
        
    def create_users_table(self):
        """
        Create a users table in the database
        """
        try:
            self.conn.execute("""
                              CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                username TEXT NOT NULL,
                                balance INTEGER
                            );
                            """)
        except Exception as e:
            print(e)
            
    def create_transactions_table(self):
        """
        Create a transactions table in the database
        """
        try:
            self.conn.execute("""
                              CREATE TABLE transactions (
                                  id INTEGER PRIMARY KEY,
                                  timestamp TEXT NOT NULL,
                                  sender_id INTEGER NOT NULL,
                                  receiver_id INTEGER NOT NULL,
                                  amount INTEGER NOT NULL,
                                  message TEXT NOT NULL,
                                  accepted BOOLEAN,
                                  FOREIGN KEY (sender_id) REFERENCES users(id),
                                  FOREIGN KEY (receiver_id) REFERENCES users(id)
                              );
                              """)
        except Exception as e:
            print(e)
            
            
    def get_users(self):
        """get all users in the database

        Returns:
            list: returns a list of all users in the database
        """
        cursor = self.conn.execute("SELECT * FROM users;")
        users = []
        for row in cursor:
            users.append({'id': row[0], 'name': row[1], 'username': row[2]})
        return users
    
    
    def create_user(self, name, username, balance):
        """create a new user

        Args:
            name (str): the name of the user
            username (str): the username of the user
            balance (int): the amount of money in the user's account

        Returns:
            int: the id of the newly created user
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (name, username, balance) VALUES (?, ?, ?);", (name, username, balance))
        self.conn.commit()
        return cursor.lastrowid
    
    def create_transaction(self, timestamp, sender_id, receiver_id, amount, message, accepted):
        """_summary_

        Args:
            sender_id (_type_): _description_
            receiver_id (_type_): _description_
            amount (_type_): _description_
            message (_type_): _description_
            accepted (_type_): _description_
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO transactions(timestamp, sender_id, receiver_id, amount, message, accepted) VALUES(?, ?, ?, ?, ?, ?)", (timestamp, sender_id, receiver_id, amount, message, accepted))
        self.conn.commit()
        return cursor.lastrowid
        
    def get_specific_user(self, id):
        """get a single user

        Args:
            id (int): the id of the user

        Returns:
            dictionary: the information of the user
        """
        user_cursor = self.conn.execute("SELECT * FROM users WHERE id = ?;", (id,))
        transaction_cursor = self.conn.execute("SELECT * FROM transactions WHERE sender_id = ? or receiver_id = ?;", (id, id,))
        for row in user_cursor:
            user_data = ({'id': row[0], 'name': row[1], 'username': row[2], 'balance': row[3], 'transactions':[]})
            for row in transaction_cursor:
                transaction = {'id': row[0], 'timestamp': row[1], 'sender_id': row[2], 'receiver_id': row[3], 'amount': row[4], 'message': row[5], 'accepted': row[6]}
                user_data['transactions'].append(transaction)
            return user_data
                
        return None
    
    def get_specific_transaction(self, transaction_id):
        """get a specific transaction from transactions table

        Args:
            transaction_id (int): id of transaction to get
        """
        cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?;", (transaction_id,))
        for row in cursor:
            transaction = {'id': row[0], 'timestamp': row[1], 'sender_id': row[2], 'receiver_id': row[3], 'amount': row[4], 'message': row[5], 'accepted': row[6]}
            return transaction
        return None
    
    
    def delete_user(self, id):
        """delete a user form database

        Args:
            id (int): the id of the user to be deleted
        """
        self.conn.execute("DELETE FROM transactions WHERE sender_id = ? or receiver_id = ?;", (id, id))
        self.conn.execute("DELETE FROM users WHERE id = ?;", (id,))
        self.conn.commit()
        
        
    def get_sender_balance(self, sender_id):
        """get the balance of the sender

        Args:
            sender_id (int): id of the sernder

        Returns:
            int: balance of the sender
        """
        sender = self.conn.execute("SELECT balance FROM users WHERE id = ?;", (sender_id,))
        for row in sender:
            sender_balance = row[0]
        return sender_balance
        
        
    def send_amount(self, sender_id, receiver_id, amount):
        """send money from one user to another

        Args:
            sender_id (int): id of the sender
            receiver_id (int): id of the receiver
            amount (int): amount of money to be sent
        """
        sender = self.conn.execute("SELECT balance FROM users WHERE id = ?;", (sender_id,))
        receiver = self.conn.execute("SELECT balance FROM users WHERE id = ?;", (receiver_id,))
        if sender_id == receiver_id:
            return None
        for row in sender:
            sender_balance = row[0]
        for row in receiver:
            receiver_balance = row[0]
        self.conn.execute("UPDATE users SET balance = ? WHERE id = ?;", (sender_balance - amount, sender_id))
        self.conn.commit()
        self.conn.execute("UPDATE users SET balance = ? WHERE id = ?;", (receiver_balance + amount, receiver_id))
        self.conn.commit()
        
        
    def update_transaction(self, transaction_id, accepted, timestamp):
        """change the status of a transaction

        Args:
            transaction_id (int): id of the transaction to be updated
        """
        transaction = self.get_specific_transaction(transaction_id)
        if transaction.get("accepted") is not None:
            return None
        self.conn.execute("UPDATE transactions SET timestamp = ? WHERE id = ?;", (timestamp, transaction_id))
        if accepted == True:
            sender_balance = self.get_sender_balance(transaction['sender_id'])
            if sender_balance < transaction['amount']:
                return "failed"
            self.send_amount(transaction.get("sender_id"), transaction.get("receiver_id"), transaction.get("amount"))
            self.conn.execute("UPDATE transactions SET accepted = ? WHERE id = ?;", (1, transaction_id))
            self.conn.commit()
            return True
        elif accepted == False:
            self.conn.execute("UPDATE transactions SET accepted = ? WHERE id = ?;", (0, transaction_id))
            self.conn.commit()
            return False
        
        
        
        

# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
