import bcrypt
try:
    password = b"Fhnehh123ZOV"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    print(hashed.decode())
except Exception as e:
    print(f"Error: {e}")
