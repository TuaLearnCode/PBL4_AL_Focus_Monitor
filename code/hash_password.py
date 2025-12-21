import bcrypt

plain = "admin"
hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
print(hashed.decode())
