import cv2
import numpy as np

from image_transliteration.preprocessing.preprocessing import DataImagePreprocessor
from image_transliteration.feature_extraction.orb import ORBFeatureExtractor
from image_transliteration.models.bovw import BagOfVisualWords
from image_transliteration.models.knn import KNNClassifier

def image_transliteration_pipeline(image, direction, role="user"):
    preprocessor = DataImagePreprocessor()
    orb_extractor = ORBFeatureExtractor()
    bovw = BagOfVisualWords(vocab_model_name="vocab_with_orb_7.pkl")
    bovw.load_vocabulary()
    knn = KNNClassifier(artifact_model_name="knn_hist_model_7.pkl")
    knn.load_model()
    
    file_bytes = np.frombuffer(image.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        return None
    
    if role == "user":
        grayscaled_img = preprocessor.apply_grayscale(image)
        if grayscaled_img is None:
            return None
        
        binarized_img = preprocessor.apply_binarization(grayscaled_img)
        if binarized_img is None:
            return None

        median_blurred_img = preprocessor.apply_median_blur(binarized_img)
        if median_blurred_img is None:
            return None
        
        segmented_imgs = preprocessor.apply_segmentation(median_blurred_img)
        if segmented_imgs is None: # segmented_imgs returns an array 
            return None
        
        thinned_images = []
        for seg_img in segmented_imgs:
            resized_img = preprocessor.apply_resize(seg_img)
            thinned_img = preprocessor.apply_thinning(resized_img)
            thinned_images.append(thinned_img)
        if thinned_images is None:
            return None
        
        all_descriptors = []
        for thin_img in thinned_images:
            keypoints, descriptors = orb_extractor.extract_feature_with_orb(thin_img)
            all_descriptors.append(descriptors)
        if all_descriptors is None:
            return None
        
        predict_hists = []
        for desc in all_descriptors:
            hist = bovw.encode(desc)
            predict_hists.append(hist)
        if predict_hists is None:
            return None
        
        predicted_text = ""
        for hist in predict_hists:
            prediction = knn.predict(hist)
            predicted_text += prediction[0]
        
        return predicted_text