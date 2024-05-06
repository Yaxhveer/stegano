import os
import random
from PIL import Image
import numpy as np
from util import compute_seed_from_image_dimensions, load_private_key, load_public_key
from encrypt import encrypt_preprocess
from decrypt import decrypt_postprocess


def load_file_encrypt(key_path, image_path, file_to_hide):
    # Load the public key
    public_key = load_public_key(key_path)

    # Read the original image
    img = Image.open(image_path)
 
    # Read the file to hide
    with open(file_to_hide, 'rb') as f:
        file_bytes = f.read()

    # Get secret file name
    filename = os.path.basename(file_to_hide).encode()

    return public_key, img, file_bytes, filename


def hide_file_in_img_util(img, imgname, file_to_hide, filename, public_key):

    # Use the sum of the image dimensions as the seed
    seed = compute_seed_from_image_dimensions(img)
    prng = random.Random(seed)  # Create a new instance of a random number generator


    # Check if the image is in a mode that can be converted to RGB or RGBA
    if img.mode not in ['RGB', 'RGBA', 'P', 'L']:
        raise ValueError("Image mode must be RGB, RGBA, P (palette-based), or L (grayscale).")

    # Convert to RGB if it's P or L mode (palette-based or grayscale)
    if img.mode == 'P' or img.mode == 'L':
        img = img.convert('RGB')

    # Convert to RGBA if not already in that format
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # This will give you the original format of the image
    host_format = img.format  
    
    # If the format is None, try to determine it from the file extension
    if host_format is None:
        file_extension = os.path.splitext(imgname)[1].lower()
        extension_to_format = {
            '.tga': 'TGA',
            '.png': 'PNG',
            '.bmp': 'BMP',
            '.tif': 'TIFF',
            '.tiff': 'TIFF',
        }
        host_format = extension_to_format.get(file_extension)

    supported_formats = {'TGA', 'TIFF', 'BMP', 'PNG'}
    if host_format not in supported_formats:
        raise ValueError(f"Unsupported image format: {host_format}")
        
    pixels = np.array(img)
    
    # get the binary representation of the file
    data_to_encode = encrypt_preprocess(file_to_hide, filename, public_key)
    
    # Calculate the number of pixels needed
    file_size = len(data_to_encode)
    num_pixels_required = file_size * 8  # 8 bits per byte
    if num_pixels_required > pixels.size // 4:  # Divide by 4 for RGBA channels
        raise ValueError("Image is not large enough to hide the file.")

    # Generate a list of unique indices to hide the data
    pixel_indices = list(range(pixels.size // 4))
    prng.shuffle(pixel_indices)  # Shuffle using the seeded PRNG

    # Embed the file size in the first 64 pixels (8 bytes for file size)
    for i in range(64):
        idx = pixel_indices[i]
        seventh_bit = ((pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0]) >> 1) & 0x1
        xor_bit = seventh_bit ^ ((file_size >> (63 - i)) & 0x1)
        if (pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0] & 0x1) != xor_bit:
            pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0] ^= 0x1

    # Embed each bit of the data to encode in the image using LSB matching
    for i, byte in enumerate(data_to_encode):
        for bit in range(8):
            idx = pixel_indices[64 + i * 8 + bit]
            seventh_bit = ((pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0]) >> 1) & 0x1
            xor_bit = seventh_bit ^ ((byte >> (7 - bit)) & 0x1)
            if (pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0] & 0x1) != xor_bit:
                pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0] ^= 0x1

    # Save the new image
    new_img = Image.fromarray(pixels, 'RGBA')

    return new_img, host_format



def hide_file_in_img(image_path, file_to_hide, output_image_path, public_key_path):
    
    # Load the files
    public_key, img, file_bytes, filename = load_file_encrypt(public_key_path, image_path, file_to_hide)
    
    # Get the name of input image
    imgname = os.path.basename(file_to_hide).encode()

    # Generate new image along with its formats name
    new_img, host_format = hide_file_in_img_util(img, imgname, file_bytes, filename, public_key)

    # Check if the file already exists and prompt the user
    if os.path.exists(output_image_path):
        overwrite = input(f"The file '{output_image_path}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Extraction cancelled.")
            return
    
    if host_format == 'PNG':
        new_img.save(output_image_path, format='PNG', optimize=True)
    elif host_format == 'BMP':
        new_img.save(output_image_path, format='BMP', optimize=True)
    elif host_format == 'TGA':
        new_img.save(output_image_path, format='TGA', optimize=True)
    elif host_format == 'TIFF':
        new_img.save(output_image_path, format='TIFF', optimize=True)
    else:
        # If the format is not one of the supported/expected formats, raise an error.
        raise ValueError(f"Unsupported image format: {host_format}")

    print(f"File '{file_to_hide}' has been successfully hidden in '{output_image_path}'.")


def load_file_decrypt(key_path, passphrase, image_path):
    # Load the public key
    private_key = load_private_key(key_path, passphrase)

    # Open the audio
    img = Image.open(image_path)

    return private_key, img

def extract_file_from_img_util(img, private_key):

    # Determine the size of the encrypted session key based on the private key size
    encrypted_session_key_size = private_key.key_size // 8
    
    # Use the sum of the image dimensions as the seed
    seed = compute_seed_from_image_dimensions(img)
    prng = random.Random(seed)  # Create a new instance of a random number generator

    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Image must be in RGB or RGBA format.")
    
    # Convert to RGBA if not already in that format
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    pixels = np.array(img)
    
    # Flatten the image array for easier processing
    flat_pixels = pixels.flatten()
    
    # Use only the red channel for RGBA
    channel_multiplier = 4

    # Extract the file size from the first 64 pixels
    file_size = 0
    for i in range(64):
        file_size = (file_size << 1) | (flat_pixels[i * channel_multiplier] & 0x1)
    
    # Calculate the number of bytes that can be extracted
    num_bytes_to_extract = file_size
    
    # Prepare a list to store the extracted bytes
    extracted_bytes = []

    # Generate a list of unique indices to extract the data
    pixel_indices = list(range(pixels.size // 4))
    prng.shuffle(pixel_indices)  # Shuffle using the seeded PRNG

    # Extract the file size from the first 64 pixels
    file_size = 0
    for i in range(64):
        idx = pixel_indices[i]
        seventh_bit = (((pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0]) >> 1) & 0x1)
        xor_bit = (pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0] & 0x1) ^ seventh_bit
        file_size = (file_size << 1) | xor_bit

    # Calculate the number of bytes that can be extracted
    num_bytes_to_extract = file_size

    # Extract the hidden bits and reconstruct the bytes using the same indices
    extracted_bytes = []
    for i in range(num_bytes_to_extract):
        byte = 0
        for bit in range(8):
            idx = pixel_indices[64 + i * 8 + bit]
            seventh_bit = (((pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0]) >> 1) & 0x1)
            xor_bit = (pixels[idx // pixels.shape[1], idx % pixels.shape[1], 0] & 0x1) ^ seventh_bit
            byte = (byte << 1) | xor_bit
        extracted_bytes.append(byte)
    
    # Get the filename and filedata from extracted bytes
    filedata, filename = decrypt_postprocess(extracted_bytes, encrypted_session_key_size, private_key)
    
    return filedata, filename


def extract_file_from_img(img_path, output_file_path, private_key_path, passphrase):
    private_key, img = load_file_decrypt(private_key_path, passphrase, img_path)

    filedata, filename = extract_file_from_img_util(img, private_key)
    
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
