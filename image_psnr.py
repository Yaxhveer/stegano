# import the cv2 as well as numpy library
import cv2
import numpy as np
# Create a function that takes two images’ paths as a parameter
def calculate_psnr(firstImage, secondImage):
   # Compute the difference between corresponding pixels
   diff = np.subtract(firstImage, secondImage)
   # Get the square of the difference
   squared_diff = np.square(diff)

   # Compute the mean squared error
   mse = np.mean(squared_diff)

   # Compute the PSNR
   max_pixel = 255
   psnr = 20 * np.log10(max_pixel) - 10 * np.log10(mse)
    
   return psnr

# Read the original and distorted images
firstI = cv2.imread('examples/dragon.png')
secondI = cv2.imread('examples/dragon-secret.png')

# Check if images are loaded successfully
if firstI is None or secondI is None:
   print("Failed to load one or both images.")
else:
   # Call the above function and perform the calculation
   psnr_score = calculate_psnr(firstI, secondI)
   # Display the result
   print("PSNR:", psnr_score)