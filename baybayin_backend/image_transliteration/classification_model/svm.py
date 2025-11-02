import numpy as np
import joblib
import os
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix
from image_transliteration.constants.constants import IMAGE_ARTIFACT_DIR


class SVMClassifier:
    def __init__(self):
        self.svm = None
        self.artifact_name = None

    def initialize(self, **params):
        C = params.get('C', 1.0)
        kernel = params.get('kernel', 'rbf')  # 'linear', 'poly', 'rbf', 'sigmoid'
        gamma = params.get('gamma', 'scale')  # 'scale', 'auto', or float
        probability = params.get('probability', True)
        
        self.svm = SVC(C=C, kernel=kernel, gamma=gamma, probability=probability)
        self.artifact_name = str(params.get('artifact_name', 'svm'))

    def train(self, X_train, y_train):
        if len(X_train) == 0 or len(y_train) == 0:
            raise ValueError("Training data or labels are empty.")
        self.svm.fit(X_train, y_train)

    def predict(self, X_test):
        if not hasattr(self.svm, "classes_"):
            raise ValueError("SVM model is not trained yet.")
        
        if X_test.ndim == 1:
            X_test = X_test.reshape(1, -1)
        
        return self.svm.predict(X_test)

    def predict_proba(self, X_test):
        if not hasattr(self.svm, "classes_"):
            raise ValueError("SVM model is not trained yet.")
        if not self.svm.probability:
            raise ValueError("SVM probability estimation was not enabled during initialization.")
        return self.svm.predict_proba(X_test)

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
        if not hasattr(self.svm, "classes_"):
            raise ValueError("SVM model is not trained yet.")
        
        y_pred = self.svm.predict(X_test)
        accuracy = self.svm.score(X_test, y_test)

        cm = confusion_matrix(y_test, y_pred, labels=self.svm.classes_)

        per_class_accuracy = {}
        for i, label in enumerate(self.svm.classes_):
            total = np.sum(cm[i])
            correct = cm[i, i]
            percent = (correct / total * 100) if total > 0 else 0
            per_class_accuracy[label] = round(percent, 2)

        return accuracy, self.format_confusion_matrix(cm, self.svm.classes_), per_class_accuracy

    def save_model(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        os.makedirs(artifact_dir, exist_ok=True)

        path = os.path.join(artifact_dir, self.get_artifact_model_name())
        joblib.dump(self.svm, path)
        print(f"SVM model saved to {path}")

    def load_model(self, artifact_path=IMAGE_ARTIFACT_DIR):
        current_path = os.path.dirname(os.path.abspath(__file__))
        artifact_dir = os.path.abspath(os.path.join(current_path, "..", artifact_path))
        path = os.path.join(artifact_dir, self.get_artifact_model_name())

        if not os.path.exists(path):
            raise FileNotFoundError(f"No model file found at {path}")

        self.svm = joblib.load(path)
        print(f"SVM model loaded from {path}")

    def get_artifact_model_name(self):
        name = self.artifact_name
        if not name.endswith(".pkl"):
            name += ".pkl"
        return name
