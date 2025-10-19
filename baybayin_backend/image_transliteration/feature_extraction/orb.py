import cv2

class ORBFeatureExtractor:
    
    def __init__(self, nfeatures=500):
        self.orb = cv2.ORB_create(nfeatures=nfeatures)
    
    def extract_feature_with_orb(self, img):
        if img is None:
            print("ERROR: image is empty")
            return None, None
        
        keypoints, descriptors = self.orb.detectAndCompute(img, None)
        
        if descriptors is None:
            print("WARNING: No keypoints detected")
            return [], None
        
        return keypoints, descriptors