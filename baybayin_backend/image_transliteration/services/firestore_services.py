import os
import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore_client():
    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set!")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def save_document(collection_name: str, document_id: str, data: dict):
    db = get_firestore_client()
    db.collection(collection_name).document(document_id).set(data)


def delete_document(collection_name: str, document_id: str):
    db = get_firestore_client()
    db.collection(collection_name).document(document_id).delete()
