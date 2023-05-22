import math
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from skimage.metrics import structural_similarity as compute_ssim

metrics = dict()
for obj in ['bed', 'chair', 'planes', 'cabinets']:
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

        # Save the depth map
        plt.figure(figsize=(5.12, 5.12))
        plt.imshow(depth_normalized, cmap='gray')
        plt.savefig(f'./images/{obj}_{idx}_depth.png')

        # Create the 4-channel RGB-SD image
        rgb_sd_image = np.zeros((left_image_rgb.shape[0], left_image_rgb.shape[1], 4), dtype=np.uint8)
        rgb_sd_image[:, :, :3] = left_image_rgb  # Assign the RGB channels
        rgb_sd_image[:, :, 3] = depth_normalized  # Assign the normalized depth map to the fourth channel

        # Save the resulting image
        cv2.imwrite(f'./images/{obj}_{idx}_rgbsd.png', rgb_sd_image)
        
        ground_truth_rgb_image_normed = cv2.normalize(cv2.imread(f'./images/{obj}_{idx}_right.png', cv2.IMREAD_UNCHANGED), None, 0, 1, cv2.NORM_MINMAX)
        ground_truth_depth_map_normed = cv2.normalize(cv2.imread(f'./images/{obj}_{idx}_depth.png', cv2.IMREAD_UNCHANGED)[:, :, 3], None, 0, 1, cv2.NORM_MINMAX)
        generated_rgbsd_image_color_normed = cv2.normalize(cv2.imread(f'./images/{obj}_{idx}_rgbsd.png', cv2.IMREAD_UNCHANGED)[:, :, :3], None, 0, 1, cv2.NORM_MINMAX)
        generated_rgbsd_image_depth_normed = cv2.normalize(cv2.imread(f'./images/{obj}_{idx}_rgbsd.png', cv2.IMREAD_UNCHANGED)[:, :, 3], None, 0, 1, cv2.NORM_MINMAX)
        
        # Compute the PSNRs
        mses = [np.mean((ground_truth_rgb_image_normed - generated_rgbsd_image_color_normed) ** 2), np.mean((ground_truth_depth_map_normed - generated_rgbsd_image_depth_normed) ** 2)]
        psnrs = [20 * np.log10(1.0 / np.sqrt(mses[0])), 20 * np.log10(1.0 / np.sqrt(mses[1]))] 

        # Compute the SSIMs
        ssims = compute_ssim(ground_truth_rgb_image_normed, generated_rgbsd_image_color_normed, channel_axis=2), compute_ssim(ground_truth_depth_map_normed, generated_rgbsd_image_depth_normed)

        # Compute the ARDs (assuming both images have the same dimensions)
        ards = [
            np.mean(np.abs(ground_truth_rgb_image_normed - generated_rgbsd_image_color_normed) / (ground_truth_rgb_image_normed + np.finfo(np.float32).eps)),
            np.mean(np.abs(ground_truth_depth_map_normed - generated_rgbsd_image_depth_normed) / (ground_truth_depth_map_normed + np.finfo(np.float32).eps))
        ]

        
        metrics[obj] = {
            'MSE_RGB': mses[0],
            'MSE_DEPTH': mses[1],
            'PSNR_RGB': psnrs[0],
            'PSNR_DEPTH': psnrs[1],
            'SSIM_RGB': ssims[0],
            'SSIM_DEPTH': ssims[1],
            'ARD_RGB': ards[0],
            'ARD_DEPTH': ards[1]
        }

        # Print the computed metrics
        print(f"Mean Squared Error (MSE)            with {obj:10s} for (i) RGB Map= {mses[0]:.5f} and (ii) Depth Map= {mses[1]:.5f}")
        print(f"Peak Signal-to-Noise Ratio (PSNR)   with {obj:10s} for (i) RGB Map= {psnrs[0]:.5f} and (ii) Depth Map= {psnrs[1]:.5f}")
        print(f"Absolute Relative Difference (ARD)  with {obj:10s} for (i) RGB Map= {ards[0]:.10e} and (ii) Depth Map= {ards[1]:.10e}")
        print(f"Structural Similarity Index (SSIM)  with {obj:10s} for (i) RGB Map= {ssims[0]:.10e} and (ii) Depth Map= {ssims[1]:.10e}")

metrics = pd.DataFrame(metrics)
metrics.to_latex('./images/metrics.tex')