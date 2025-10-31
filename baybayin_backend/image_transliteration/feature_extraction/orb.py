import cv2

class ORBFeatureExtractor:
    def __init__(self):
        self.orb = None
    
    def initialize(self, **params):
        nfeatures = params.get('nfeatures', 500)
        scaleFactor = params.get('scale_factor', 1.2)
        nlevels = params.get('nlevels', 8)
        self.orb = cv2.ORB_create(nfeatures=nfeatures, scaleFactor=scaleFactor, nlevels=nlevels)
    
    def extract_feature_with_orb(self, img):
        if img is None:
            print("ERROR: image is empty")
            return None, None
        
        keypoints, descriptors = self.orb.detectAndCompute(img, None)
        
        if descriptors is None:
            print("WARNING: No keypoints detected")
            return [], None
        
        return keypoints, descriptors
