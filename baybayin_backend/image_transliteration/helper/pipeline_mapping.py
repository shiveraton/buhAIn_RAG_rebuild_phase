from image_transliteration.preprocessing.preprocessing import DataImagePreprocessor
from image_transliteration.feature_extraction.orb import ORBFeatureExtractor
from image_transliteration.feature_extraction.sift import SIFTFeatureExtractor
from image_transliteration.vocabulary_model.bovw import BagOfVisualWords
from image_transliteration.classification_model.knn import KNNClassifier
from image_transliteration.classification_model.svm import SVMClassifier

preprocessor = DataImagePreprocessor()

preprocessing_map = {
    'grayscaling': preprocessor.apply_grayscale,
    'binarization': preprocessor.apply_binarization,
    'resize': preprocessor.apply_resize,
    'erosion': preprocessor.apply_erosion,
    'median_blur': preprocessor.apply_median_blur,
    'thinning': preprocessor.apply_thinning,
    'dilation': preprocessor.apply_dilation,
    'bilateral_filter': preprocessor.apply_bilateral_filter,
    'segmentation': preprocessor.apply_segmentation,
}

feature_extraction_map = {
    'orb': ORBFeatureExtractor,
    'sift': SIFTFeatureExtractor,
}

feature_encoding_map = {
    'bovw': BagOfVisualWords,
}

classification_map = {
    'knn': KNNClassifier,
    'svm': SVMClassifier,
}

ALL_MODULES = {
    **preprocessing_map,
    **feature_extraction_map,
    **feature_encoding_map,
    **classification_map,
}