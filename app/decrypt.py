import zlib
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def decrypt_data(encrypted_session_key, salt, iv, encrypted_data, private_key):
    # Decrypt the session key with RSA
    session_key = private_key.decrypt(
        encrypted_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Derive the symmetric key from the session key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,  # Increased iterations for added security
        backend=default_backend()
    )
    key = kdf.derive(session_key)
    
    # Decrypt the data with AES
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    unpadder = PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
    
    return decrypted_data


def decrypt_postprocess(extracted_bytes, encrypted_session_key_size, private_key):
    # Convert the extracted bytes to a byte array
    data_to_decode = bytes(extracted_bytes)

    # Extract the filename size and filename
    filename_size = int.from_bytes(data_to_decode[:4], 'big')
    filename = data_to_decode[4:4 + filename_size].decode()
    
    # Extract the session key, salt, iv, and encrypted data
    offset = 4 + filename_size
    encrypted_session_key = data_to_decode[offset:offset + encrypted_session_key_size]
    salt = data_to_decode[offset + encrypted_session_key_size:offset + encrypted_session_key_size + 16]
    iv = data_to_decode[offset + encrypted_session_key_size + 16:offset + encrypted_session_key_size + 32]
    encrypted_data = data_to_decode[offset + encrypted_session_key_size + 32:]
    
    # Decrypt the data
    decrypted_data = decrypt_data(encrypted_session_key, salt, iv, encrypted_data, private_key)
    
    # Decompress the decrypted data
    decompressed_data = zlib.decompress(decrypted_data)
    
    return decompressed_data, filename