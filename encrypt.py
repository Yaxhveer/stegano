import os
import zlib
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def encrypt_data(data, public_key):
    # Generate a random session key
    session_key = os.urandom(32)  # 32 bytes for 256-bit key
    
    # Derive a symmetric key from the session key
    salt = os.urandom(16)  # 16 bytes for 128-bit salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,  # Increased iterations for added security
        backend=default_backend()
    )
    key = kdf.derive(session_key)
    
    # Encrypt the data with AES
    iv = os.urandom(16)  # 16 bytes for 128-bit IV
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    # Encrypt the session key with RSA
    encrypted_session_key = public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return encrypted_session_key, salt, iv, encrypted_data

def encrypt_preprocess(file_bytes, filename, public_key):
    
    # Compress the file
    compressed_data = zlib.compress(file_bytes)

    # Encrypt the compressed data
    encrypted_session_key, salt, iv, encrypted_data = encrypt_data(compressed_data, public_key)
    
    # Get the filename to store
    filename_size = len(filename)

    # Concatenate the encrypted session key, salt, iv, and encrypted data and return it
    return (filename_size.to_bytes(4, 'big') + filename +
                      encrypted_session_key + salt + iv + encrypted_data)

