from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import ModelConfig, ModelPipelineMethod
from image_transliteration.helper.pipeline_mapping import (
    preprocessing_map,
    feature_extraction_map,
    feature_encoding_map,
    classification_map,
)
from image_transliteration.services.firestore_services import save_document, delete_document

CATEGORY_MAP = {
    "preprocessing": preprocessing_map,
    "feature_extraction": feature_extraction_map,
    "feature_encoding": feature_encoding_map,
    "classification": classification_map,
}

class ModelPipelineMethodForm(forms.ModelForm):
    class Meta:
        model = ModelPipelineMethod
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        module_name = cleaned_data.get("module_name")

        if category not in CATEGORY_MAP:
            raise ValidationError(f"Invalid category '{category}'.")
        if module_name not in CATEGORY_MAP[category]:
            raise ValidationError(
                f"'{module_name}' is not a registered module under category '{category}'."
            )
        return cleaned_data

class ModelConfigForm(forms.ModelForm):
    class Meta:
        model = ModelConfig
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        params = cleaned_data.get("params")
        if not isinstance(params, dict):
            raise ValidationError("Params must be a valid JSON object (key-value pairs).")
        for key in params.keys():
            if not isinstance(key, str):
                raise ValidationError(f"Parameter name '{key}' must be a string.")
        return cleaned_data


@admin.register(ModelConfig)
class ModelConfigAdmin(admin.ModelAdmin):
    form = ModelConfigForm
    list_display = ("model_name", "complete_name", "category")
    search_fields = ("model_name", "complete_name")
    list_filter = ("category",)
    fieldsets = (
        ("Model Information", {
            "fields": ("model_name", "complete_name", "category", "params"),
            "description": (
                "Define the parameter schema for this model as JSON. "
                "Select the model configuration category and make the params datatype "
                "compatible with TypeScript (e.g., string, number, boolean) and example value. "
                "Example: {'params': {'datatype': 'value', 'sample': 'nfeatures'}}"
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        save_document(
            "model_config",
            obj.model_name,
            {
                "model_name": obj.model_name,
                "complete_name": obj.complete_name,
                "category": obj.category,
                "params": obj.params,
            },
        )

    def delete_model(self, request, obj):
        delete_document("model_config", obj.model_name)
        super().delete_model(request, obj)


@admin.register(ModelPipelineMethod)
class ModelPipelineMethodAdmin(admin.ModelAdmin):
    form = ModelPipelineMethodForm
    list_display = ("module_name", "complete_name", "category", "description")
    search_fields = ("module_name", "complete_name", "category")
    list_filter = ("category",)
    fieldsets = (
        ("Pipeline Module", {
            "fields": ("module_name", "complete_name", "category", "description"),
            "description": "Register a pipeline module available for building model pipelines.",
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("module_name", "category")
        return ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        save_document(
            "model_pipeline_methods",
            obj.module_name,
            {
                "module_name": obj.module_name,
                "complete_name": obj.complete_name,
                "category": obj.category,
                "description": obj.description or "",
            },
        )

    def delete_model(self, request, obj):
        delete_document("model_pipeline_methods", obj.module_name)
        super().delete_model(request, obj)
