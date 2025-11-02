# models.py
from django.db import models
from django.core.exceptions import ValidationError
from image_transliteration.helper.pipeline_mapping import (
    preprocessing_map,
    feature_extraction_map,
    feature_encoding_map,
    classification_map,
)

PIPELINE_CATEGORIES = [
    ("preprocessing", "Preprocessing"),
    ("feature_extraction", "Feature Extraction"),
    ("feature_encoding", "Feature Encoding"),
    ("classification", "Classification"),
]

MODEL_CONFIGURATION_CATEGORIES = [
    ("feature_extraction", "Feature Extraction"),
    ("feature_encoding", "Feature Encoding"),
    ("classification", "Classification"),
]

class ModelConfig(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
    complete_name = models.CharField(max_length=200, help_text="Full descriptive name of the model")
    category = models.CharField(max_length=50, choices=MODEL_CONFIGURATION_CATEGORIES)
    params = models.JSONField(help_text="Define parameter names and expected data types as JSON")

    def __str__(self):
        return self.model_name

    def clean(self):
        if not isinstance(self.params, dict):
            raise ValidationError("Params must be a valid JSON object (key-value pairs).")
        for key, val in self.params.items():
            if not isinstance(key, str):
                raise ValidationError(f"Parameter name '{key}' must be a string.")
        super().clean()



class ModelPipelineMethod(models.Model):
    module_name = models.CharField(max_length=100, unique=True)
    complete_name = models.CharField(max_length=200, help_text="Full descriptive name of the method")
    category = models.CharField(max_length=50, choices=PIPELINE_CATEGORIES)
    description = models.TextField(blank=True, null=True)

    def clean(self):
        category_map = {
            "preprocessing": preprocessing_map,
            "feature_extraction": feature_extraction_map,
            "feature_encoding": feature_encoding_map,
            "classification": classification_map,
        }

        if self.category not in category_map:
            raise ValidationError(f"Invalid category '{self.category}'.")

        valid_map = category_map[self.category]
        if self.module_name not in valid_map:
            raise ValidationError(
                f"'{self.module_name}' is not a registered module under category '{self.category}'."
            )

        super().clean()

    def __str__(self):
        return f"{self.module_name} ({self.category})"
