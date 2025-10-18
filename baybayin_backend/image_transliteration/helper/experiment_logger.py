import pandas as pd
import os
from datetime import datetime

from constants.constants import EXPERIMENT_DIR

class ExperimentLogger:
    
    def __init__(self, log_path=EXPERIMENT_DIR, folder_name="latin_training_log", experiment_file="experiment_log.xlsx"):
        self.log_path = log_path
        self.experiment_file = experiment_file
        
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.experiment_path = os.path.join(current_path, "..", "..", self.log_path, folder_name, self.experiment_file)
        
        os.makedirs(os.path.dirname(self.experiment_path), exist_ok=True)
        
        if not os.path.exists(self.experiment_path):
            df = pd.DataFrame(columns=[
                "Experiment_ID", 
                "Date", 
                "Preprocessing_Methods", 
                "Feature_Extractor", 
                "Avg_Keypoints_Per_Class", 
                "Feature_Extraction_Errors",
                "Vocab_Artifact_Name",
                "Vocab_Size", 
                "Classifier", 
                "Parameters",
                "Accuracy", 
                "Confusion_Matrix",
                "Per_Class_Accuracy",
                "Classifier_Artifact_Name",
                "Preprocessing_Errors",
                "Feature_Extraction_Errors"
            ])
            df.to_excel(self.experiment_path, index=False)
            print(f"Created new experiment log at: {self.experiment_path}")
    
    def get_last_experiment_id(self):
        if not os.path.exists(self.experiment_path):
            return 0 
        df = pd.read_excel(self.experiment_path)
        if df.empty:
            return 0
        return int(df["Experiment_ID"].max())

    def log_experiment(self, data):
        if not os.path.exists(self.experiment_path):
            df = pd.DataFrame()
        else:
            df = pd.read_excel(self.experiment_path)

        if df.empty or all(df.isna().all()):
            df = pd.DataFrame(columns=data.keys())

        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)

        df.to_excel(self.experiment_path, index=False)
        print(f"Experiment logged: {data.get('Experiment_ID', 'N/A')}")

