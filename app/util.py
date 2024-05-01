import numpy as np
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

def get_data_type(bytes_per_sample):
     # Convert frames to a numpy array
    if bytes_per_sample == 1:
        dtype = np.uint8
    elif bytes_per_sample == 2:
        dtype = np.uint16
    elif bytes_per_sample == 3:
        dtype = np.uint32
    else:
        raise ValueError("Unsupported sample width")
    
    return dtype