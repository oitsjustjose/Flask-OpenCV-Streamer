"""Handles logins from a file, and encryption of said file"""
import os
import sys

from cryptography.fernet import Fernet


class LoginManager:
    def __init__(self, path_to_login_file, keyname):
        self.path = path_to_login_file
        self.keyname = keyname
        self.key = self.load_key()
        self.fernet = Fernet(self.key)
        self.logins = self.load_logins()

    def __getstate_(self):
        """An override for loading this object's state from pickle"""
        ret = {
            "path": self.path,
            "keyname": self.keyname
        }
        return ret

    def __setstate__(self, dict_in):
        """An override for pickling this object's state"""
        self.path = dict_in["path"]
        self.keyname = dict_in["keyname"]
        self.key = self.load_key()
        self.fernet = Fernet(self.key)
        self.logins = self.load_logins()

    def load_logins(self):
        """Loads logins from a file, returning them as a dict"""
        logins = {}
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                lines = file.readlines()
                for line in lines:
                    decrypted_line = self.fernet.decrypt(bytes(line.encode()))
                    decrypted_line = decrypted_line.decode()
                    username, password = decrypted_line.replace(
                        " ", "").replace("\n", "").replace("\t", "").split(",")
                    logins[username] = password
        return logins

    def write_logins(self):
        """Writes the logins to an encryptedfile"""
        if os.path.exists(self.path):
            os.remove(self.path)
        with open(self.path, "w") as file:
            for username in self.logins:
                file.write(self.encrypt_line(username)+"\n")

    def add_login(self, username, password):
        """Adds a new username and password, writing changes afterward"""
        if username in list(self.logins.keys()):
            print("Login pair not added; login {} already exists".format(username))
        else:
            self.logins[username] = password
            self.write_logins()

    def remove_login(self, username):
        """Removes a username and password, writing changes afterward"""
        if not username in list(self.logins.keys()):
            print("Login not found - no deletion was made")
        else:
            del self.logins[username]
            self.write_logins()

    def encrypt_line(self, username):
        """Encrypts a username/password line for the txt file and converts to str"""
        ret = "{}, {}".format(username, self.logins[username]).encode()
        ret = bytes(ret)
        ret = self.fernet.encrypt(ret)
        return str(ret.decode('utf-8'))

    def load_key(self):
        """Loads the key from a hidden location"""
        token = ""
        if os.path.exists(self.keyname):
            with open(self.keyname, "r") as file:
                lines = file.readlines()
                for line in lines:
                    token = line.replace("\n", "")
                    break
        else:
            token = Fernet.generate_key()
            with open(self.keyname, "w+") as file:
                file.write(token.decode('utf-8'))
        return bytes(token.encode())


# If we run this as an app it's to add/remove a new account
if __name__ == "__main__":
    ARGS = sys.argv[1:]
    if len(ARGS) == 4:
        if ARGS[1].lower() == "add":
            LM = LoginManager(ARGS[0])
            LM.add_login(ARGS[2], ARGS[3])
            print("Successfully added new login!")
            exit()
    elif len(ARGS) == 3:
        if ARGS[1].lower() == "rm":
            LM = LoginManager(ARGS[0])
            LM.remove_login(ARGS[2])
            print("Sucessfully removed login!")
            exit()
    print("Incorrect usage. Usage:")
    print("python login_mgr.py <path_to_login_file> add <username> <password>")
    print("OR")
    print("python login_mgr.py <path_to_login_file> rm <username>")
