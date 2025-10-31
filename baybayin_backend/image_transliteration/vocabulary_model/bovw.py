import numpy as np
from sklearn.cluster import KMeans
import joblib
import os

from image_transliteration.constants.constants import IMAGE_ARTIFACT_DIR


class BagOfVisualWords:
    def __init__(self):
        self.kmeans = None
        self.vocabulary = None
        self.artifact_name = None
        self.num_clusters = None

    def initialize(self, **params):
        n_clusters = params.get('n_clusters', 500)
        random_state = params.get('random_state', 42)
        verbose = params.get('verbose', 0)

        self.kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            verbose=verbose,
            n_init=10
        )

        self.artifact_name = str(params.get('artifact_name', 'vocab'))
        self.num_clusters = n_clusters

    def build_vocabulary(self, all_descriptors):
        if self.kmeans is None:
            raise ValueError("KMeans model is not initialized. Call initialize() first.")

        if not all_descriptors:
            raise ValueError("Descriptor list is empty.")

        all_descriptors = np.vstack(all_descriptors)
        self.kmeans.fit(all_descriptors)
        self.vocabulary = self.kmeans.cluster_centers_

        print(f"Vocabulary built with {self.num_clusters} clusters.")

    def encode(self, descriptors):
        if self.kmeans is None:
            raise ValueError("KMeans model is not initialized or vocabulary not built.")
        if descriptors is None or descriptors.size == 0:
            print("WARNING: Empty descriptors received.")
            return np.zeros(self.num_clusters)

        cluster_labels = self.kmeans.predict(descriptors)
        hist, _ = np.histogram(cluster_labels, bins=np.arange(self.num_clusters + 1))
        hist = hist.astype(float)
        hist /= (hist.sum() + 1e-7)  # normalize histogram

        return hist

    def save_vocabulary(self, artifact_path=IMAGE_ARTIFACT_DIR):
        if self.kmeans is None:
            raise ValueError("Cannot save. KMeans model not initialized or trained.")

        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        os.makedirs(artifact_dir, exist_ok=True)

        path = os.path.join(artifact_dir, self.get_artifact_model_name())
        joblib.dump(self.kmeans, path)

        print(f"Vocabulary saved to {path}")

    def load_vocabulary(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        path = os.path.join(artifact_dir, self.get_artifact_model_name())

        if not os.path.exists(path):
            raise FileNotFoundError(f"No vocabulary file found at {path}")

        self.kmeans = joblib.load(path)
        self.vocabulary = self.kmeans.cluster_centers_
        self.num_clusters = len(self.vocabulary)

        print(f"Vocabulary loaded from {path}")

    def get_artifact_model_name(self):
        """Return artifact filename with .pkl extension."""
        name = self.artifact_name or "vocab"
        if not name.endswith(".pkl"):
            name += ".pkl"
        return name
