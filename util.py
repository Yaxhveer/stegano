import os
from PIL import Image
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def compute_seed_from_image_dimensions(img):
    width, height = img.size
    return width + height

def load_public_key(key_path):
    with open(key_path, 'rb') as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    return public_key

def load_private_key(key_path, passphrase):
    # passphrase = getpass("Enter the private key passphrase: ")
    with open(key_path, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase.encode(),
            backend=default_backend()
        )
    return private_key