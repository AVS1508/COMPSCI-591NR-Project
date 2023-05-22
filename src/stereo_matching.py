import math
import cv2
import numpy as np
import matplotlib.pyplot as plt

for obj in ['bed', 'chair']:
    for idx in range(1, 3):
        # Load the left and right images of the stereoscopic pair
        left_image_rgb = cv2.imread(f'./images/{obj}_{idx}_left.png', cv2.IMREAD_COLOR)
        left_image_gray = cv2.imread(f'./images/{obj}_{idx}_left.png', cv2.IMREAD_GRAYSCALE)
        right_image_gray = cv2.imread(f'./images/{obj}_{idx}_right.png', cv2.IMREAD_GRAYSCALE)

        # Create a StereoBM object for stereo matching
        stereo = cv2.StereoBM_create(
            numDisparities=32,
            blockSize=5,
        )

        # Perform stereo matching
        disparity = stereo.compute(left_image_gray, right_image_gray)

        # Normalize the disparity values for visualization
        disparity_normalized = np.uint8(255 * (disparity - disparity.min()) / (disparity.max() - disparity.min()))

        # Create depth map using parameters from the camera (depth_renderer)
        baseline, focus = 1.0, 1.2 * math.sqrt(3)
        depth = baseline * focus / (disparity_normalized + np.finfo(np.float32).eps)

        # Compute the normalized depth map (using offset for amenable clipping of occluded regions of the image at 50%+ gray)
        depth_normalized = cv2.normalize(depth, None, 128, 255, cv2.NORM_MINMAX) + 127

        # Display the depth map
        plt.figure(figsize=(5.12, 5.12))
        plt.imshow(depth_normalized, cmap='gray')
        plt.savefig(f'./images/{obj}_{idx}_depth.png')
        # plt.show()

        # Create the 4-channel RGB-SD image
        rgb_sd_image = np.zeros((left_image_rgb.shape[0], left_image_rgb.shape[1], 4), dtype=np.uint8)
        rgb_sd_image[:, :, :3] = left_image_rgb  # Assign the RGB channels
        rgb_sd_image[:, :, 3] = depth_normalized  # Assign the normalized depth map to the fourth channel

        # Save the resulting image
        cv2.imwrite(f'./images/{obj}_{idx}_rgbsd.png', rgb_sd_image)
        
        # Load the ground truth depth map
        ground_truth_depth = cv2.imread(f'./images/{obj}_{idx}_depth.png', cv2.IMREAD_GRAYSCALE)
        
        # Compute the mean squared error (MSE)
        mse = np.mean((cv2.normalize(depth_normalized.astype(np.float32), None, 0, 1, cv2.NORM_MINMAX) - cv2.normalize(ground_truth_depth.astype(np.float32), None, 0, 1, cv2.NORM_MINMAX))**2)

        print(f"Mean Squared Error (MSE): {mse}")