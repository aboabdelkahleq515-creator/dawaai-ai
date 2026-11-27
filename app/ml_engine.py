"""
Machine Learning & Deep Learning Inference Engine for Dawaa'i AI.
Provides real-time clinical drug classification (Decision Tree & Random Forest)
and packaging form visual recognition (PyTorch CNN).
"""
import os
import json
import base64
import io
import re
from typing import Optional, Dict, Any, List
import numpy as np
import joblib

import torch
import torch.nn as nn
from PIL import Image

PACKAGING_CLASSES = [
    "Tablets", "Capsules", "Oral Liquid / Syrup", "Injection", "Cream / Ointment", "Drops"
]

class DrugPackagingCNN(nn.Module):
    """
    Convolutional Neural Network for identifying pharmaceutical dosage & packaging forms.
    Input: (B, 3, 64, 64) Normalized Image Tensor
    """
    def __init__(self, num_classes=len(PACKAGING_CLASSES)):
        super(DrugPackagingCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2)
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2)
        
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.relu3 = nn.ReLU()
        self.pool3 = nn.AdaptiveAvgPool2d((4, 4))
        
        self.dropout = nn.Dropout(0.35)
        self.fc1 = nn.Linear(128 * 4 * 4, 128)
        self.fc_relu = nn.ReLU()
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x = self.pool3(self.relu3(self.bn3(self.conv3(x))))
        x = x.view(x.size(0), -1)
        x = self.dropout(self.fc_relu(self.fc1(x)))
        x = self.fc2(x)
        return x


class MLEngine:
    """Manages loaded ML & DL models for fast inference."""
    _instance = None

    def __init__(self):
        self.vectorizer = None
        self.rf_pregnancy = None
        self.dt_pregnancy = None
        self.rf_category = None
        self.dt_category = None
        self.cnn_model = None
        self.classes = PACKAGING_CLASSES
        self.is_loaded = False
        self._load_models()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MLEngine()
        return cls._instance

    def _load_models(self):
        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        try:
            vec_path = os.path.join(models_dir, "tfidf_vectorizer.pkl")
            rf_preg_path = os.path.join(models_dir, "random_forest_pregnancy.pkl")
            dt_preg_path = os.path.join(models_dir, "decision_tree_pregnancy.pkl")
            rf_cat_path = os.path.join(models_dir, "random_forest_category.pkl")
            dt_cat_path = os.path.join(models_dir, "decision_tree_category.pkl")
            cnn_path = os.path.join(models_dir, "packaging_cnn_model.pt")

            if os.path.exists(vec_path):
                self.vectorizer = joblib.load(vec_path)
            if os.path.exists(rf_preg_path):
                self.rf_pregnancy = joblib.load(rf_preg_path)
            if os.path.exists(dt_preg_path):
                self.dt_pregnancy = joblib.load(dt_preg_path)
            if os.path.exists(rf_cat_path):
                self.rf_category = joblib.load(rf_cat_path)
            if os.path.exists(dt_cat_path):
                self.dt_category = joblib.load(dt_cat_path)

            if os.path.exists(cnn_path):
                self.cnn_model = DrugPackagingCNN(num_classes=len(self.classes))
                state_dict = torch.load(cnn_path, map_location=torch.device('cpu'), weights_only=True)
                self.cnn_model.load_state_dict(state_dict)
                self.cnn_model.eval()

            self.is_loaded = True
            print("MLEngine: All ML & DL models successfully loaded into memory.")
        except Exception as e:
            print(f"MLEngine loading warning: {e}")

    def predict_clinical_profile(
        self,
        drug_name: str = "",
        active_ingredient: str = "",
        dosage_form: str = "",
        uses: str = "",
        side_effects: str = ""
    ) -> Dict[str, Any]:
        """
        Runs Decision Tree and Random Forest to classify:
        1. Pregnancy & Lactation Safety Level
        2. Therapeutic Category
        Returns comparative predictions with confidence scores.
        """
        required = (self.vectorizer, self.rf_pregnancy, self.dt_pregnancy, self.rf_category, self.dt_category)
        if any(m is None for m in required):
            return {"available": False, "reason": "Models not loaded"}

        text_input = f"{drug_name} {active_ingredient} {dosage_form} {uses} {side_effects}".strip()
        if not text_input:
            # Never invent an input: with no text there is nothing to classify
            return {"available": False, "reason": "No text to classify"}

        try:
            X_vec = self.vectorizer.transform([text_input])

            rf_preg_pred = self.rf_pregnancy.predict(X_vec)[0]
            rf_preg_conf = float(np.max(self.rf_pregnancy.predict_proba(X_vec)[0]))
            rf_cat_pred = self.rf_category.predict(X_vec)[0]
            rf_cat_conf = float(np.max(self.rf_category.predict_proba(X_vec)[0]))
            dt_preg_pred = self.dt_pregnancy.predict(X_vec)[0]
            dt_cat_pred = self.dt_category.predict(X_vec)[0]
        except Exception as e:
            return {"available": False, "error": str(e)}

        preg_ar_map = {
            "Safe / Low Risk": "آمن / مخاطر منخفضة (Category A/B)",
            "Caution / Consult Doctor": "استشر الطبيب بحذر (Category C)",
            "High Risk / Contraindicated": "محظور / عالي الخطورة للحمل (Category D/X)"
        }

        preg_agree = bool(rf_preg_pred == dt_preg_pred)
        # Only show a pregnancy hint when both models agree AND the forest is reasonably sure.
        # Otherwise report "unknown" instead of a coin-flip.
        preg_reliable = preg_agree and rf_preg_conf >= 0.70
        shown_level = rf_preg_pred if preg_reliable else "Unknown"

        return {
            "available": True,
            # IMPORTANT: this is a statistical hint trained on text, NOT a clinical safety verdict.
            # The UI must show safety from the verified database / safety_profile, never from here.
            "is_safety_verdict": False,
            "pregnancy_safety": {
                "predicted_level": shown_level,
                "predicted_level_ar": preg_ar_map.get(shown_level, "غير مؤكد - راجع الصيدلي"),
                "confidence": round(rf_preg_conf * 100, 1),
                "random_forest_prediction": rf_preg_pred,
                "decision_tree_prediction": dt_preg_pred,
                "model_agreement": preg_agree,
                "reliable": preg_reliable
            },
            "therapeutic_category": {
                "predicted_category": rf_cat_pred,
                "confidence": round(rf_cat_conf * 100, 1),
                "random_forest_prediction": rf_cat_pred,
                "decision_tree_prediction": dt_cat_pred,
                "model_agreement": bool(rf_cat_pred == dt_cat_pred)
            },
            "ensemble_notes": "Secondary ML hint only. Not used for safety decisions."
        }

    def predict_packaging_form_cnn(self, image_data: Any) -> Dict[str, Any]:
        """
        Classifies packaging/dosage form using the trained PyTorch CNN.
        Accepts: base64 string, bytes, or PIL Image.
        Returns predicted form class, confidence percentage, and class probabilities.
        """
        if not self.cnn_model:
            return {"available": False, "reason": "CNN model not loaded"}

        try:
            # Decode image
            pil_img = None
            if isinstance(image_data, str):
                clean_b64 = image_data
                if "," in image_data:
                    clean_b64 = image_data.split(",", 1)[1]
                img_bytes = base64.b64decode(clean_b64)
                pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            elif isinstance(image_data, bytes):
                pil_img = Image.open(io.BytesIO(image_data)).convert("RGB")
            elif isinstance(image_data, Image.Image):
                pil_img = image_data.convert("RGB")

            if pil_img is None:
                return {"available": False, "error": "Invalid image format"}

            # Resize to 64x64 and normalize to [0, 1]
            pil_resized = pil_img.resize((64, 64))
            arr = np.array(pil_resized, dtype=np.float32) / 255.0
            # Transpose (H, W, C) -> (C, H, W)
            arr = np.transpose(arr, (2, 0, 1))
            tensor = torch.from_numpy(arr).unsqueeze(0)  # Shape (1, 3, 64, 64)

            with torch.no_grad():
                outputs = self.cnn_model(tensor)
                probs = torch.softmax(outputs, dim=1)[0].numpy()
                pred_idx = int(np.argmax(probs))
                pred_class = self.classes[pred_idx]
                pred_conf = float(probs[pred_idx])

            # Arabic mapping for packaging forms
            ar_forms = {
                "Tablets": "أقراص / شرائط بليستر (Tablets)",
                "Capsules": "كبسولات دوائية (Capsules)",
                "Oral Liquid / Syrup": "شراب / محلول فموي (Syrup)",
                "Injection": "حقن / أمبولات زجاجية (Injection)",
                "Cream / Ointment": "مرهم / كريم موضعي (Ointment)",
                "Drops": "قطرات طبية (Drops)"
            }

            all_scores = {
                self.classes[i]: round(float(probs[i]) * 100, 1)
                for i in range(len(self.classes))
            }

            return {
                "available": True,
                "predicted_form": pred_class,
                "predicted_form_ar": ar_forms.get(pred_class, pred_class),
                "confidence": round(pred_conf * 100, 1),
                "usable": pred_conf >= 0.60,  # below this, do not use the form as a feature
                "class_probabilities": all_scores,
                "model_type": "Convolutional Neural Network (PyTorch CNN 3-Block)"
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

# Singleton helper functions
def get_ml_engine() -> MLEngine:
    return MLEngine.get_instance()

def predict_drug_ml(name: str = "", active: str = "", form: str = "", uses: str = "", side_effects: str = "") -> dict:
    return get_ml_engine().predict_clinical_profile(name, active, form, uses, side_effects)

def predict_packaging_cnn(image_data: Any) -> dict:
    return get_ml_engine().predict_packaging_form_cnn(image_data)
