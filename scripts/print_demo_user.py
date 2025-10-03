"""
Utility to print demo user document from Firestore for debugging password hash issues.
"""
import asyncio
from app.services.firebase_service import FirebaseService
from app.utils.anonymization import anonymization_service

DEMO_EMAIL = "demo@evergrow360.com"

async def main():
    firebase_service = FirebaseService()
    firebase_service._initialize_firebase()
    user_id = anonymization_service.generate_anonymous_id(DEMO_EMAIL)
    doc_ref = firebase_service.db.collection('users').document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        print(f"Demo user password_hash for {DEMO_EMAIL} (ID: {user_id}):")
        print(data.get('password_hash'))
    else:
        print(f"No document found for demo user {DEMO_EMAIL} (ID: {user_id})")

if __name__ == "__main__":
    asyncio.run(main())
