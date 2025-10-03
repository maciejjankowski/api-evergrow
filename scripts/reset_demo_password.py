"""
Utility script to reset demo user password in Firebase for development/demo purposes.
"""

import os
from app.services.firebase_service import FirebaseService
from app.utils.security import PasswordSecurity
from app.utils.anonymization import anonymization_service

# Demo credentials
DEMO_EMAIL = "demo@evergrow360.com"
DEMO_PASSWORD = "Demo123!"

if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    firebase_service = FirebaseService()
    firebase_service._initialize_firebase()  # Ensure Firestore client is initialized
    password_security = PasswordSecurity()
    user_id = anonymization_service.generate_anonymous_id(DEMO_EMAIL)
    password_hash = password_security.hash_password(DEMO_PASSWORD)
    print(f"Resetting password for demo user: {DEMO_EMAIL} (ID: {user_id})")
    # Try to update, if fails, create the document
    try:
        import google.api_core.exceptions
        success = asyncio.run(firebase_service.update_user_profile(user_id, {"password_hash": password_hash}))
        if not success:
            raise Exception("Update failed")
        print("✅ Demo user password reset successfully.")
    except Exception as e:
        print(f"Update failed: {e}, trying to create user document...")
        # Create minimal user profile
        user_data = {
            'email': DEMO_EMAIL,
            'password_hash': password_hash,
            'first_name': 'Demo',
            'marketing_consent': False,
            'terms_accepted': True,
            'registration_date': datetime.utcnow().isoformat(),
            'email_verified': True,
            'onboarding_completed': True,
            # Ensure password_hash is present and not None
            'last_active': datetime.utcnow().isoformat(),
        }
        try:
            created_id = asyncio.run(firebase_service.create_user_profile(user_data))
            print(f"✅ Demo user document created: {created_id}")
        except Exception as ce:
            print(f"❌ Failed to create demo user document: {ce}")
