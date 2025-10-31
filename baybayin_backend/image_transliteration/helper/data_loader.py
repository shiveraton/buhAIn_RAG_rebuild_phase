import cv2
import os

from constants.constants import TRAINING_RAW_PATH_DIR

class DataImageLoader:
    
    def __init__(self):
        pass
    
    def _obtain_target_path(self, path_folder):
        current_path = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.abspath(os.path.join(current_path, "..", "..", path_folder))
        return target_path
    
    def load_test_data(self, test_path, test_folder, index):
        target_folder = os.path.join(test_path, test_folder)
        test_data_path = self._obtain_target_path(target_folder)
        print(f"test data path {test_data_path}")
        
        if not os.path.isdir(test_data_path):
            return None

    
        imgs = []
        for image in os.listdir(test_data_path):
            if image.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif")):
                imgs.append(image)

        if not imgs:
            return None

        if index < 0 or index >= len(imgs):
            return None

        image_name = imgs[index]
        image_path = os.path.join(test_data_path, image_name)

        print(imgs)
        print(image_name)

        img = cv2.imread(image_path)
        if img is None:
            return None

        return img
        
    def load_training_data(self, training_path, training_folder):
        target_folder = os.path.join(training_path, training_folder)
        training_data_path = self._obtain_target_path(target_folder)
        
        print(f"training data path {training_data_path}")
        raw_images = {}
        
        for folder_name in os.listdir(training_data_path):
            folder_path = os.path.join(training_data_path, folder_name)
            
            if os.path.isdir(folder_path):
                print(folder_name)
                raw_images[folder_name] = {}
                for img_name in os.listdir(folder_path):
                    if not img_name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif")):
                        continue 
            
                    img_path = os.path.join(folder_path, img_name)
                    img = cv2.imread(img_path)  
                    
                    if img is None:
                        continue 
                    
                    name_without_ext, _ = os.path.splitext(img_name)
                    raw_images[folder_name][name_without_ext] = img
                    
        return raw_images
