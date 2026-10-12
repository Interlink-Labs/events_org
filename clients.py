import sqlite3
from hashlib import sha256, sha3_512
#username = input()
#password = input()

def write_user(username, password):
    with sqlite3.connect('my_database.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        hash_password = sha256(password.encode('utf-8')).hexdigest()
        hash_password = sha3_512(hash_password.encode('utf-8')).hexdigest()
        if not check_user(username):
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password))
            return 'Пользователь записан'

def check_user(username):
    with sqlite3.connect('my_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        for row in cursor:
            if username == row[0]:
                return True
        return False

def get_user(username):
    with sqlite3.connect('my_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, password FROM users WHERE username = ?', (username,))
        for row in cursor:
            if username == row[0]:
                return f'username: {row[0]}, password: {row[1]}'
        return 'No such user'

def validate_user(username, password):
    with sqlite3.connect('my_database.db') as conn:
        cursor = conn.cursor()

        hash_password = sha256(password.encode('utf-8')).hexdigest()
        hash_password = sha3_512(hash_password.encode('utf-8')).hexdigest()

        cursor.execute('SELECT username, password FROM users WHERE username = ?', (username,))
        for row in cursor:
            if username == row[0] and hash_password == row[1]:
                return True
        return False
#print(get_user('cat_kuzay'))
print(validate_user('tomoko_obkuroki', 'gbvyuh'))