import cv2
import numpy as np
import skimage as ski
import mahotas

from image_transliteration.constants.constants import STANDARD_IMAGE_SIZE
from image_transliteration.helper.visualizer import DataVisualizer
class DataImagePreprocessor:
    def __init__(self):
        pass

    def apply_grayscale(self, img):
        if img is None:
            print("ERROR: image is empty")
            return None
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img 

    def apply_binarization(self, img, threshold=120):
        if img is None:
            print("ERROR: image is empty")
            return None
        if len(img.shape) == 3:
            img = self.apply_grayscale(img)
        _, binarized_img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
        return binarized_img

    def _segmentation_sort_criteria(self, value):
        x = value[0]
        y = value[1]
        return x, y
    
    def apply_segmentation(self, img):
        _, thresh = cv2.threshold(img, 130, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) != 1:
            print(f"WARNING: more than 1 character detected! {len(contours)}")

        contour_values = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50 and h > 50:
                contour_values.append((x, y, w, h))

        contour_values.sort(key=self._segmentation_sort_criteria)

        characters = []
        for (x, y, w, h) in contour_values:
            # print(x, y, w, h)
            char_img = img[y:y+h, x:x+w]
            characters.append(char_img)

        # print("\n")
        return characters

    def apply_resize(self, img, img_standard_size=STANDARD_IMAGE_SIZE):
        if not isinstance(img_standard_size, tuple) or len(img_standard_size) != 2:
            print("ERROR: resize value must be a tuple (#, #)")
            return None

        if img is None:
            print("ERROR: image is empty")
            return None

        original_height, original_width = img.shape[:2]
        target_width, target_height = img_standard_size  # Cartesian style: x=width, y=height

        if original_height == 0 or original_width == 0:
            print("ERROR: image has zero width or height!")
            return None

        scale = min(target_height / original_height, target_width / original_width)

        if scale <= 0:
            print("WARNING: invalid scale (<=0). Skipping resize.")
            return img

        new_height = int(original_height * scale)
        new_width = int(original_width * scale)

        resized_img = cv2.resize(img, (new_width, new_height))

        padding_width = target_width - new_width
        padding_height = target_height - new_height
        padding_left = padding_width // 2
        padding_right = padding_width - padding_left
        padding_top = padding_height // 2
        padding_bottom = padding_height - padding_top

        padded_img = cv2.copyMakeBorder(
            resized_img, padding_top, padding_bottom,
            padding_left, padding_right,
            cv2.BORDER_CONSTANT, value=255
        )
        return padded_img

    def apply_erosion(self, img):
        if img is None:
            print("ERROR! image is empty!")
            return None

        kernel = np.ones((6,6), np.uint8)
        
        inverted_img = cv2.bitwise_not(img)
        eroded_image = cv2.erode(inverted_img, kernel=kernel, iterations=3)
        return cv2.bitwise_not(eroded_image)
    
    def apply_median_blur(self, img, kernel_size=3):
        if img is None:
            print("ERROR: image is empty")
            return None
        return cv2.medianBlur(img, kernel_size)
    
    def apply_thinning(self, img):
        if img is None:
            print("ERROR: image is empty")
            return None
        inverted_img = cv2.bitwise_not(img)
        thinned_img = ski.morphology.thin(inverted_img)
        thinned_img = (thinned_img * 255).astype(np.uint8)
        return cv2.bitwise_not(thinned_img)
    
    def apply_dilation(self, img, kernel_size=(2, 2), iterations=2):
        if img is None:
            print("ERROR: image is empty")
            return None

        kernel = np.ones(kernel_size, np.uint8)
        dilated = cv2.dilate(cv2.bitwise_not(img), kernel, iterations=iterations)
        return cv2.bitwise_not(dilated)
        
    def apply_bilateral_filter(self, img, d_val=20, sigma_color_val=30, sigma_space_val=75):
        if img is None:
            print("ERROR: image is empty")
            return None
        return cv2.bilateralFilter(img, d=d_val, sigmaColor=sigma_color_val, sigmaSpace=sigma_space_val)