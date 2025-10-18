import numpy as np
from sklearn.cluster import KMeans
import joblib  
import os

from constants.constants import IMAGE_ARTIFACT_DIR

class BagOfVisualWords:
    def __init__(self, num_clusters=500, random_state=42, verbose=0, vocab_model_name="vocab.pkl"):
        self.num_clusters = num_clusters
        self.kmeans = KMeans(n_clusters=num_clusters, random_state=random_state, verbose=verbose, n_init=10)
        self.vocab_model_name = vocab_model_name
        self.vocabulary = None

    def build_vocabulary(self, all_descriptors):
        all_descriptors = np.vstack(all_descriptors)
        self.kmeans.fit(all_descriptors)
        self.vocabulary = self.kmeans.cluster_centers_

    def encode(self, descriptors):
        if descriptors is None or descriptors.size == 0:
            return None
        
        cluster_labels = self.kmeans.predict(descriptors)
        hist, _ = np.histogram(cluster_labels, bins=np.arange(self.num_clusters+1))
        hist = hist.astype(float)
        hist /= (hist.sum() + 1e-7)
        
        return hist

    def save_vocabulary(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        os.makedirs(artifact_dir, exist_ok=True)
        
        path = os.path.join(artifact_dir, self.get_vocab_model_name())
        joblib.dump(self.kmeans, path)
        
        print(f"Vocabulary saved to {path}")

    def load_vocabulary(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        
        path = os.path.join(artifact_dir, self.get_vocab_model_name())
        if not os.path.exists(path):
            raise FileNotFoundError(f"No vocabulary file found at {path}")

        self.kmeans = joblib.load(path)
        self.vocabulary = self.kmeans.cluster_centers_
        print(f"Vocabulary loaded from {path}")

    
    def get_vocab_size(self):
        return self.num_clusters
    
    def get_vocab_model_name(self):
        return self.vocab_model_name