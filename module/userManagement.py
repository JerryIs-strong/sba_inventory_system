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
        con = sqlite3.connect("data/user.db")
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name VARCHAR(255) NOT NULL UNIQUE, 
                user_password VARCHAR(255) NOT NULL,
                user_group VARCHAR(255) NOT NULL
            )
        ''')
        con.commit()
        con.close()

    def getUserGroup(self, user_name):
        con = sqlite3.connect("data/user.db")
        cur = con.cursor()
        cur.execute('SELECT user_group FROM users WHERE user_name = ?', (user_name,))
        user_group = cur.fetchone()[0]
        con.commit()
        con.close()
        return user_group

    def createUser(self, user_name, password, user_group):
        con = sqlite3.connect("data/user.db")
        cur = con.cursor()
        try:
            cur.execute('INSERT INTO users (user_name, user_password, user_group) VALUES (?, ?, ?)', (user_name, self.hash_password(password), user_group))
            con.commit()
            return "OK"
        except sqlite3.InterfaceError:
            return "Error: Username already exists."
        finally:
            con.close()

    def getUserList(self):
        con = sqlite3.connect("data/user.db")
        cur = con.cursor()
        cur.execute('SELECT user_name FROM users')
        user_list = cur.fetchall()
        con.commit()
        con.close()
        return [username[0] for username in user_list]
        
    def deleteUser(self, user_name):
        con = sqlite3.connect("data/user.db")
        cur = con.cursor()
        cur.execute('DELETE FROM users WHERE user_name = ?', (user_name,))
        con.commit()
        con.close()
    
    def verifyUser(self, user_name, user_password):
        con = sqlite3.connect("data/user.db")
        cur = con.cursor()
        cur.execute('SELECT user_password FROM users WHERE user_name = ?', (user_name,))
        user = cur.fetchone()
        con.commit()
        con.close()    
        
        if user is None:
            return False

        if bcrypt.checkpw(user_password.encode('utf-8'), user[0]):
            return True
        else:
            return False

    def updateUser(self, type, old_user_info, new_user_info, addition_user_info = None):
        try:
            con = sqlite3.connect("data/user.db")
            cur = con.cursor()
            
            if type == "user_name":
                cur.execute('UPDATE users SET user_name = ? WHERE user_name = ?', (new_user_info, old_user_info))
            elif type == "user_password":
                cur.execute('UPDATE users SET user_password = ? WHERE user_name = ? AND user_password = ?', (self.hash_password(new_user_info), old_user_info, addition_user_info))
            else:
                return "[Error]: Invalid type value"
            
            con.commit()
            return "[Info]: Successful update user name/password"
        
        except sqlite3.Error as e:
            return f"[Error]: Database error - {str(e)}"
        
        finally:
            con.close()

