import numpy as np
import scipy.io.wavfile as wav

# Create a function that takes two images’ paths as a parameter
def calculate_psnr(faudio, saudio):
   # Compute the difference between corresponding pixels
   diff = np.subtract(faudio, saudio)
   # Get the square of the difference
   squared_diff = np.square(diff)

   # Compute the mean squared error
   mse = np.mean(squared_diff)

   # Compute the PSNR
   max_pixel = 65535
   psnr = 20 * np.log10(max_pixel) - 10 * np.log10(mse)
    
   return psnr

# Read WAV files
_, y1 = wav.read('examples/audio.wav')
_, y2 = wav.read('examples/audio-secret.wav')

# Ensure both audio signals have the same length
min_length = min(len(y1), len(y2))
y1 = y1[:min_length]
y2 = y2[:min_length]

PSNR = calculate_psnr(y1, y2)

print(f"PSNR: {PSNR}")
