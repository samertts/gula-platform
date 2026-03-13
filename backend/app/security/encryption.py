
from cryptography.fernet import Fernet

KEY = Fernet.generate_key()

cipher = Fernet(KEY)

def encrypt(data):

    return cipher.encrypt(data.encode()).decode()

def decrypt(data):

    return cipher.decrypt(data.encode()).decode()

