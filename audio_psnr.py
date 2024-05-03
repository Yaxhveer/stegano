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
fs1, y1 = wav.read('examples/chime.wav')
fs2, y2 = wav.read('examples/audio-chime.wav')

# Ensure both audio signals have the same length
min_length = min(len(y1), len(y2))
y1 = y1[:min_length]
y2 = y2[:min_length]

# Calculate MSE
err = np.sum((y1 - y2) ** 2) / (min_length)
MSE = np.sqrt(err)
mm = np.mean((y1 - y2) ** 2)

# Constants
MAXVAL = 65535

# Calculate PSNR
# PSNR = 20 * np.log10(MAXVAL / MSE)

PSNR = calculate_psnr(y1, y2)

print(f"PSNR: {PSNR}")
