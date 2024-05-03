import os
import random
import numpy as np
import wave
from util import load_private_key, load_public_key, get_data_type
from encrypt import encrypt_preprocess
from decrypt import decrypt_postprocess

def load_file_encrypt(key_path, audio_path, file_to_hide):
    # Load the public key
    public_key = load_public_key(key_path)

    # Open the audio
    audio = wave.open(audio_path, mode='rb')

    # Read the file to hide
    with open(file_to_hide, 'rb') as f:
        file_bytes = f.read()

    # Get secret file name
    filename = os.path.basename(file_to_hide).encode()

    return public_key, audio, file_bytes, filename

def hide_file_in_audio_util(audio, file_bytes, filename, public_key, audioname=""):
    seed = audio.getnframes()
    prng = random.Random(seed) 

    # Read the original audio
    bytes_per_sample = audio.getsampwidth()
    frames = audio.readframes(audio.getnframes())

    dtype = get_data_type(bytes_per_sample)

    bits = np.frombuffer(frames, dtype=dtype).copy()  

    # get the binary representation of the file
    data_to_encode = encrypt_preprocess(file_bytes, filename, public_key)

    # Calculate the number of samples needed
    file_size = len(data_to_encode)
    num_samples_required = file_size * 8 // (audio.getsampwidth() * 8)
    if num_samples_required > len(bits):  
        raise ValueError("Audio is not large enough to hide the file.")

    # Generate a list of unique indices to hide the data
    sample_indices = list(range(len(bits)))
    prng.shuffle(sample_indices)  # Shuffle using the seeded PRNG

    # Embed the file size in the first 64 samples (8 bytes for file size)
    for i in range(64):
        idx = sample_indices[i]
        seventh_bit = (bits[idx] >> 1) & 0x1
        xor_bit = ((file_size >> (63 - i))) & 0x1 ^ seventh_bit
        if (bits[idx] & 0x1) != xor_bit:
            bits[idx] ^= 0x1

    # Embed each bit of the data to encode in the audio using LSB matching
    for i, byte in enumerate(data_to_encode):
        for bit in range(8):
            idx = sample_indices[64 + i * 8 + bit]
            seventh_bit = (bits[idx] >> 1) & 0x1
            xor_bit = ((byte >> (7 - bit)) & 0x1) & 0x1 ^ seventh_bit
            if (bits[idx] & 0x1) != xor_bit:
                bits[idx] ^= 0x1

    return bits
    

def hide_file_in_audio(audio_path, file_to_hide, output_audio_path, public_key_path):
    
    # Load the files
    public_key, audio, file_bytes, filename = load_file_encrypt(public_key_path, audio_path, file_to_hide)
    
    out_bytes = hide_file_in_audio_util(audio, file_bytes, filename, public_key)
    
    # Check if the file already exists and prompt the user
    if os.path.exists(output_audio_path):
        overwrite = input(f"The file '{output_audio_path}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Extraction cancelled.")
            return
    
    with wave.open(output_audio_path, 'wb') as output_audio:
        output_audio.setparams(audio.getparams())
        output_audio.writeframes(out_bytes)

    audio.close()

    print(f"File '{file_to_hide}' has been successfully hidden in '{output_audio_path}'.")


def load_file_decrypt(key_path, passphrase, audio_path):
    # Load the public key
    private_key = load_private_key(key_path, passphrase)

    # Open the audio
    audio = wave.open(audio_path, mode='rb')

    return private_key, audio


def extract_file_from_audio_util(audio, private_key):

    # Determine the size of the encrypted session key based on the private key size
    encrypted_session_key_size = private_key.key_size // 8
    
    seed = audio.getnframes()
    prng = random.Random(seed)  

    # Read the original audio
    bytes_per_sample = audio.getsampwidth()
    frames = audio.readframes(audio.getnframes())
    
    dtype = get_data_type(bytes_per_sample)

    bits = np.frombuffer(frames, dtype=dtype).copy()  

    # Extract the file size from the first 64 pixels
    file_size = 0
    for i in range(64):
        file_size = (file_size << 1) | (bits[i] & 0x1)
    
    # Calculate the number of bytes that can be extracted
    num_bytes_to_extract = file_size
    
    # Prepare a list to store the extracted bytes
    extracted_bytes = []
    
    # Generate a list of unique indices to extract the data
    pixel_indices = list(range(len(bits)))
    prng.shuffle(pixel_indices)  # Shuffle using the seeded PRNG

    # Extract the file size from the first 64 pixels
    file_size = 0
    for i in range(64):
        idx = pixel_indices[i]
        seventh_bit = (bits[idx] >> 1) & 0x1
        xor_bit = (bits[idx] & 0x1) ^ seventh_bit
        file_size = (file_size << 1) | xor_bit

    # Calculate the number of bytes that can be extracted
    num_bytes_to_extract = file_size

    # Extract the hidden bits and reconstruct the bytes using the same indices
    extracted_bytes = []
    for i in range(num_bytes_to_extract):
        byte = 0
        for bit in range(8):
            idx = pixel_indices[64 + i * 8 + bit]
            seventh_bit = (bits[idx] >> 1) & 0x1
            xor_bit = (bits[idx] & 0x1) ^ seventh_bit
            byte = (byte << 1) | xor_bit
        extracted_bytes.append(byte)
    
    # Get the filename and filedata from extracted bytes
    filedata, filename = decrypt_postprocess(extracted_bytes, encrypted_session_key_size, private_key)

    return filedata, filename
    

def extract_file_from_audio(audio_path, output_file_path, private_key_path, passphrase):
    private_key, audio = load_file_decrypt(private_key_path, passphrase, audio_path)

    filedata, filename = extract_file_from_audio_util(audio, private_key)
    
    # If no output file path is provided, use the extracted filename
    if not output_file_path:
        output_file_path = os.path.join(os.getcwd(), filename)

    # Check if the file already exists and prompt the user
    if os.path.exists(output_file_path):
        overwrite = input(f"The file '{output_file_path}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Extraction cancelled.")
            return
        
    # Write the decompressed data to the output file
    with open(output_file_path, 'wb') as f:
        f.write(filedata)

    print(f"File extracted to {output_file_path}")
