import cv2

class SIFTFeatureExtractor:

    def __init__(self):
        self.sift = None

    def initialize(self, **params):
        nfeatures = params.get('nfeatures', 0)
        contrastThreshold = params.get('contrastThreshold', 0.04)
        edgeThreshold = params.get('edgeThreshold', 10)
        sigma = params.get('sigma', 1.6)

        self.sift = cv2.SIFT_create(
            nfeatures=nfeatures,
            contrastThreshold=contrastThreshold,
            edgeThreshold=edgeThreshold,
            sigma=sigma
        )

    def extract_feature_with_sift(self, img):
        if img is None:
            print("ERROR: image is empty")
            return None, None

        keypoints, descriptors = self.sift.detectAndCompute(img, None)

        if descriptors is None:
            print("WARNING: No keypoints detected")
            return [], None

        return keypoints, descriptors
