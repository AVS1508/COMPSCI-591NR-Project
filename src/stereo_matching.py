import math
import cv2
import numpy as np
import matplotlib.pyplot as plt

for obj in ['bed', 'chair']:
    for idx in range(1,3):
        # Load the left and right images of the stereoscopic pair
        left_image = cv2.imread(f'./images/{obj}_{idx}_left.png', cv2.IMREAD_GRAYSCALE)
        right_image = cv2.imread(f'./images/{obj}_{idx}_right.png', cv2.IMREAD_GRAYSCALE)

        # Create a StereoBM object for stereo matching
        stereo = cv2.StereoBM_create(
            numDisparities=16,
            blockSize=5,
        )

        # Perform stereo matching
        disparity = stereo.compute(left_image, right_image)

        # Normalize the disparity values for visualization
        # disparity_normalized = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        # Create depth map using parameters from the camera (depth_renderer)
        baseline, focus = 1.0, 1.2 * math.sqrt(3)
        depth = baseline * focus / disparity

        # Display the disparity map
        plt.figure(figsize=(5.12, 5.12))
        plt.imshow(depth, cmap='gray')
        plt.savefig(f'./images/{obj}_{idx}_depth.png')
        plt.show()
