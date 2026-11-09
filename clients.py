import sqlite3
from hashlib import sha256, sha3_512
from fastapi import FastAPI
import os
import jwt
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "my_database.db")

def hash_string(string: str):
    return sha256(string.encode('utf-8')).hexdigest()

def write_user(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                access_token TEXT,
                refresh_token TEXT
            )
        ''')

        hash_password = sha256(password.encode('utf-8')).hexdigest()
        hash_password = sha3_512(hash_password.encode('utf-8')).hexdigest()
        if not check_user(username):
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password))
            return True
        return False

def check_user(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        for row in cursor:
            if username == row[0]:
                return True
        return False

def get_user(username):
    with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            for row in cursor:
                if username == row[1]:
                    return row
            return 'No such user'

def validate_user(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        hash_password = sha256(password.encode('utf-8')).hexdigest()
        hash_password = sha3_512(hash_password.encode('utf-8')).hexdigest()

        cursor.execute('SELECT username, password FROM users WHERE username = ?', (username,))
        for row in cursor:
            if username == row[0] and hash_password == row[1]:
                return True
        return False

def update_user(username, new_password):
    if check_user(username):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE users
            SET password = ?
            WHERE username = ?
            ''', (new_password, username))
        return True
    return False

def delete_user(username):
    if check_user(username):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM users
            WHERE username = ?
            ''', (username,))
        return True
    return False

def write_cookie(access, refresh, username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users
        SET access_token = ?, refresh_token = ?
        WHERE username = ?
        ''', (access, refresh, username))

def get_tokens(username, access_token, refresh_token):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT access_token, refresh_token FROM users
        WHERE username = ?
        ''', (username,))
        a = list(cursor)
        try:
            if a[0][0] == hash_string(access_token) and a[0][1] == hash_string(refresh_token):
                return 'SDFGHJK'
            else:
                return "asdfgh"
        except Exception as e:
            for row in traceback.TracebackException.from_exception(e).format():
                return False