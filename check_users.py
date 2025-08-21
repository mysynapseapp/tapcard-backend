#!/usr/bin/env python3
import sqlite3

def check_users():
    try:
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE username LIKE 'testuser_%'")
        users = cursor.fetchall()
        print('Registered users:')
        for user in users:
            print(f'Username: {user[0]}, Email: {user[1]}')
        conn.close()
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_users()
