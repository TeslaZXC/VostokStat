import bcrypt
try:
    password = b"admin"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    print(hashed.decode())
except Exception as e:
    print(f"Error: {e}")
