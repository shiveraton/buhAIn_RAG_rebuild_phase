import numpy as np
import joblib
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import confusion_matrix
from image_transliteration.constants.constants import IMAGE_ARTIFACT_DIR

class KNNClassifier:
    def __init__(self):
        self.knn = None
        self.artifact_name = None
    
    def initialize(self, **params):
        n_neighbors = params.get('n_neighbors', 1)
        weights = params.get('weights', 'distance')
        
        self.knn = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights)
        self.artifact_name = str(params.get('artifact_name', 'knn'))
        
    def train(self, X_train, y_train):
        if len(X_train) == 0 or len(y_train) == 0:
            raise ValueError("Training data or labels are empty.")
        self.knn.fit(X_train, y_train)

    def predict(self, X_test):
        if not hasattr(self.knn, "classes_"):
            raise ValueError("KNN model is not trained yet.")
        
        if X_test.ndim == 1:
            X_test = X_test.reshape(1, -1)
        
        return self.knn.predict(X_test)
    
    def predict_proba(self, X_test):
        if not hasattr(self.knn, "classes_"):
            raise ValueError("KNN model is not trained yet.")
        
        if not hasattr(self.knn, "predict_proba"):
            raise NotImplementedError("This KNN model does not support probability predictions.")
        
        if X_test.ndim == 1:
            X_test = X_test.reshape(1, -1)
        
        return self.knn.predict_proba(X_test)

    def format_confusion_matrix(self, cm, class_labels):
        return {
            true_label: {
                pred_label: int(cm[i][j])
                for j, pred_label in enumerate(class_labels)
                if cm[i][j] != 0
            }
            for i, true_label in enumerate(class_labels)
            if np.any(cm[i] != 0)
        }

    def evaluate(self, X_test, y_test):
        if not hasattr(self.knn, "classes_"):
            raise ValueError("KNN model is not trained yet.")
        
        y_pred = self.knn.predict(X_test)
        accuracy = self.knn.score(X_test, y_test)

        cm = confusion_matrix(y_test, y_pred, labels=self.knn.classes_)

        per_class_accuracy = {}
        for i, label in enumerate(self.knn.classes_):
            total = np.sum(cm[i])           
            correct = cm[i, i]     
            percent = (correct / total * 100) if total > 0 else 0
            per_class_accuracy[label] = round(percent, 2)
                
        return accuracy, self.format_confusion_matrix(cm, self.knn.classes_), per_class_accuracy

    def save_model(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        os.makedirs(artifact_dir, exist_ok=True)
        
        path = os.path.join(artifact_dir, self.get_artifact_model_name())
        joblib.dump(self.knn, path)
        
        print(f"KNN model saved to {path}")

    def load_model(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        path = os.path.join(artifact_dir, self.get_artifact_model_name())
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model file found at {path}")
        self.knn = joblib.load(path)
        
        print(f"KNN model loaded from {path}")
    
    def get_artifact_model_name(self):
        name = self.artifact_name
        if not name.endswith(".pkl"):
            name += ".pkl"
        return name
