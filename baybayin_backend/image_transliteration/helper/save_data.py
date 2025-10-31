import os
import cv2 

from constants.constants import PREPROCESSED_IMAGE_DATA_DIR

class SaveImageData:
    def __init__(self):
        pass
    
    def save_preprocessed_data(self, preprocessed_images, preprocessed_folder):
        saving_image_errors = {}
        
        current_path = os.path.dirname(os.path.abspath(__file__))
        preprocessed_image_path = os.path.abspath(os.path.join(current_path, "..", "..", PREPROCESSED_IMAGE_DATA_DIR, preprocessed_folder))
                
        # print(preprocessed_image_path) # debugging purposes
                
        for folder, imgs in preprocessed_images.items():
            current_folder_path = os.path.join(preprocessed_image_path, folder)
            # print(current_folder_path) # debugging purposes
            os.makedirs(current_folder_path, exist_ok=True)
            for img_name, img in imgs.items():
                save_image_path = os.path.join(current_folder_path, (img_name + ".jpg"))
                if not cv2.imwrite(save_image_path, img):
                    saving_image_errors[folder].append(img_name)
        
        return saving_image_errors