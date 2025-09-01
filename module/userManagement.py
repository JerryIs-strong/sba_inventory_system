import sqlite3
import bcrypt

class UserManager:
    def __init__(self):
        self.init_DB()

    def hash_password(self, password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed

    def init_DB(self):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_name VARCHAR(255) PRIMARY KEY NOT NULL UNIQUE, 
                    user_password VARCHAR(255) NOT NULL,
                    user_group VARCHAR(255) NOT NULL
                )
            ''')
            con.commit()

    def getUserGroup(self, user_name):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('SELECT user_group FROM users WHERE user_name = ?', (user_name,))
            user_group = cur.fetchone()[0]
            con.commit()
            return user_group

    def createUser(self, user_name, password, user_group):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('INSERT INTO users (user_name, user_password, user_group) VALUES (?, ?, ?)', (user_name, self.hash_password(password), user_group))
            con.commit()

    def getUserList(self):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('SELECT user_name FROM users')
            user_list = cur.fetchall()
            con.commit()
            result = []

            for user in user_list:
                result.append([user[0], self.getUserGroup(user[0])])
            return result
        
    def deleteUser(self, user_name):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('DELETE FROM users WHERE user_name = ?', (user_name,))
            con.commit()
    
    def logIn(self, user_name, user_password):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('SELECT user_password FROM users WHERE user_name = ?', (user_name,))
            user = cur.fetchone()
            con.commit()  
            
            if user is None:
                return False

            if bcrypt.checkpw(user_password.encode('utf-8'), user[0]):
                return True
            else:
                return False

    def updateUser(self, type, old_user_info, new_user_info):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            
            if type == "user_name":
                cur.execute('UPDATE users SET user_name = ? WHERE user_name = ?', (new_user_info, old_user_info))
            elif type == "user_password":
                cur.execute('UPDATE users SET user_password = ? WHERE user_name = ?', (self.hash_password(new_user_info), old_user_info))
            
            con.commit()
            return True
        
    def passwordVerify(self, password):
        symbol = "!@#$%^&*()-=+<>/,.?:;"
        low_letter = "abcdefghijklmnopqrstuvwxyz"
        upp_letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        num = "0123456789"

        has_symbol = any(char in symbol for char in password)
        has_lower = any(char in low_letter for char in password)
        has_upper = any(char in upp_letter for char in password)
        has_number = any(char in num for char in password)

        if has_symbol and has_lower and has_upper and has_number and len(password) >= 8 and len(password) <= 32:
            return True
        else:
            return False
            
    def userNameVerify(self, user_name):
        with sqlite3.connect('data/user.db') as con:
            cur = con.cursor()
            cur.execute('SELECT COUNT(*) FROM users WHERE user_name = ?', (user_name,))
            exists = cur.fetchone()[0]

            if exists:
                return False
            else:
                return True

