"""
Firebase service for Evergrow360 backend

This module provides secure Firebase integration with:
- Firestore database operations
- Authentication management
- Data encryption and anonymization
- Query optimization and caching
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore import Client, Query
from flask import current_app

from app.utils.security import data_encryption
from app.utils.anonymization import anonymization_service


class FirebaseService:
    def create_user_profile_sync(self, user_data: Dict[str, Any]) -> str:
        """Synchronous wrapper for create_user_profile"""
        import asyncio
        return asyncio.run(self.create_user_profile(user_data))
    
    def update_user_profile_sync(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Synchronous wrapper for update_user_profile"""
        if not self._db:
            # Mock update - just return success
            print(f"Mock update user profile {user_id}: {updates}")
            return True
        import asyncio
        return asyncio.run(self.update_user_profile(user_id, updates))
    
    def save_assessment_sync(self, assessment_data: Dict[str, Any], user_id: str) -> str:
        """Synchronous wrapper for save_assessment"""
        if not self._db:
            # Mock save - return a fake assessment ID
            assessment_id = f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
            print(f"Mock save assessment {assessment_id} for user {user_id}")
            return assessment_id
        import asyncio
        return asyncio.run(self.save_assessment(assessment_data, user_id))
    
    def save_coaching_plan_sync(self, plan_data: Dict[str, Any]) -> str:
        """Synchronous wrapper for save_coaching_plan"""
        if not self._db:
            # Mock save - return a fake plan ID
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{plan_data['user_id'][:8]}"
            print(f"Mock save coaching plan {plan_id} for user {plan_data['user_id']}")
            return plan_id
        import asyncio
        return asyncio.run(self.save_coaching_plan(plan_data))
    def get_user_profile_sync(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for get_user_profile"""
        if not self._db:
            # Return mock data when Firebase is not available
            return self._get_mock_user_profile(user_id)
        import asyncio
        return asyncio.run(self.get_user_profile(user_id))
    
    def _get_mock_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Return mock user profile data for development"""
        return {
            'user_id': user_id,
            'first_name': 'Demo',
            'last_name': 'User',
            'email': 'demo@evergrow360.com',
            'company': 'Demo Company',
            'job_title': 'Demo Role',
            'industry': 'Technology',
            'experience_years': 5,
            'location': 'San Francisco, CA',
            'timezone': 'America/Los_Angeles',
            'bio': 'Demo user for testing purposes',
            'registration_date': '2024-01-01T00:00:00Z',
            'last_login': '2024-01-01T00:00:00Z',
            'onboarding_completed': True,
            'assessment_completed': False,
            'subscription_tier': 'free',
            'profile_completion_percentage': 85
        }
        try:
            # Anonymize updates
            if 'coaching_preferences' in updates or 'business_context' in updates:
                sensitive_fields = ['coaching_preferences', 'business_context']
                encrypted_updates = data_encryption.encrypt_dict(updates, sensitive_fields)
            else:
                encrypted_updates = updates
            # Add update timestamp
            encrypted_updates['last_updated'] = datetime.now(timezone.utc).isoformat()
            self.db.collection('users').document(user_id).update(encrypted_updates)
            return True
        except Exception as e:
            print(f"Failed to update user profile {user_id}: {e}")
            return False
        """Lazy initialization of Firestore client"""
        if self._db is None:
            self._initialize_firebase()
        return self._db
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self._app = firebase_admin._apps['[DEFAULT]']
                self._db = firestore.client()
            else:
                # Initialize from environment variables or service account file
                cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                
                if cred_path and os.path.exists(cred_path):
                    # Use service account file
                    cred = credentials.Certificate(cred_path)
                else:
                    # Try to use environment variables
                    project_id = os.environ.get('FIREBASE_PROJECT_ID')
                    
                    if project_id:
                        # Use environment variables for credentials
                        cred_dict = {
                            "type": "service_account",
                            "project_id": project_id,
                            "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                            "private_key": os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                            "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
                            "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
                            "auth_uri": os.environ.get('FIREBASE_AUTH_URI'),
                            "token_uri": os.environ.get('FIREBASE_TOKEN_URI'),
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.environ.get('FIREBASE_CLIENT_EMAIL')}"
                        }
                        cred = credentials.Certificate(cred_dict)
                    else:
                        # No Firebase credentials available - use mock mode
                        print("No Firebase credentials found - using mock data mode")
                        self._db = None
                        return
                
                self._app = firebase_admin.initialize_app(cred)
            
            self._db = firestore.client()
            print("Firebase initialized successfully")
            
        except Exception as e:
            print(f"Firebase initialization failed: {e} - using mock data mode")
            self._db = None
    
    @property
    def db(self) -> Client:
        """Get Firestore client"""
        if not self._db:
            self._initialize_firebase()
        if not self._db:
            raise RuntimeError("Firebase not available - using mock data mode")
        return self._db
    
    # User Management (Anonymized)
    
    async def create_user_profile(self, user_data: Dict[str, Any]) -> str:
        """
        Create anonymized user profile
        
        Returns: Anonymous user ID
        """
        try:
            # Anonymize the user data
            anonymized_profile = anonymization_service.anonymize_user_profile(user_data)
            user_id = anonymized_profile['user_id']
            
            # Encrypt sensitive coaching data
            sensitive_fields = ['coaching_preferences', 'business_context']
            encrypted_profile = data_encryption.encrypt_dict(
                anonymized_profile, 
                sensitive_fields
            )
            
            # Store in Firestore
            self.db.collection('users').document(user_id).set(encrypted_profile)
            
            print(f"Created anonymized user profile: {user_id}")
            return user_id
            
        except Exception as e:
            print(f"User profile creation failed: {e}")
            raise
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by anonymous ID"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            encrypted_data = doc.to_dict()
            
            # Decrypt sensitive fields
            sensitive_fields = ['coaching_preferences', 'business_context']
            decrypted_data = data_encryption.decrypt_dict(
                encrypted_data,
                sensitive_fields
            )
            
            return decrypted_data
            
        except Exception as e:
            print(f"Failed to get user profile {user_id}: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile with anonymized data"""
        try:
            # Anonymize updates
            if 'coaching_preferences' in updates or 'business_context' in updates:
                sensitive_fields = ['coaching_preferences', 'business_context']
                encrypted_updates = data_encryption.encrypt_dict(updates, sensitive_fields)
            else:
                encrypted_updates = updates
            
            # Add update timestamp
            encrypted_updates['last_updated'] = datetime.now(timezone.utc).isoformat()
            
            self.db.collection('users').document(user_id).update(encrypted_updates)
            return True
            
        except Exception as e:
            print(f"Failed to update user profile {user_id}: {e}")
            return False
    
    async def delete_user_data(self, user_id: str) -> bool:
        """GDPR-compliant user data deletion"""
        try:
            batch = self.db.batch()
            
            # Delete user profile
            user_ref = self.db.collection('users').document(user_id)
            batch.delete(user_ref)
            
            # Delete assessments
            assessments = self.db.collection('assessments').where('user_id', '==', user_id).get()
            for assessment in assessments:
                batch.delete(assessment.reference)
            
            # Delete coaching plans
            plans = self.db.collection('coaching_plans').where('user_id', '==', user_id).get()
            for plan in plans:
                batch.delete(plan.reference)
            
            # Delete sessions (but keep anonymized analytics)
            sessions = self.db.collection('sessions').where('user_id', '==', user_id).get()
            for session in sessions:
                # Anonymize session data instead of deleting for analytics
                anonymized_session = {
                    'user_id': 'deleted_user',
                    'deletion_date': datetime.now(timezone.utc).isoformat(),
                    'session_type': session.to_dict().get('session_type'),
                    'duration_minutes': session.to_dict().get('duration_minutes'),
                    'satisfaction_score': session.to_dict().get('satisfaction_score')
                }
                batch.set(session.reference, anonymized_session)
            
            # Commit all changes
            batch.commit()
            
            print(f"Deleted user data for {user_id}")
            return True
            
        except Exception as e:
            print(f"Failed to delete user data {user_id}: {e}")
            return False
    
    # Assessment Management
    
    async def save_assessment(self, assessment_data: Dict[str, Any], user_id: str) -> str:
        """Save anonymized assessment data"""
        try:
            # Anonymize assessment data
            anonymized_assessment = anonymization_service.anonymize_assessment_data(
                assessment_data, user_id
            )
            
            assessment_id = anonymized_assessment['assessment_id']
            
            # Encrypt sensitive responses
            sensitive_fields = ['responses']
            encrypted_assessment = data_encryption.encrypt_dict(
                anonymized_assessment,
                sensitive_fields
            )
            
            # Store in Firestore
            self.db.collection('assessments').document(assessment_id).set(encrypted_assessment)
            
            # Update user profile with assessment completion
            await self.update_user_profile(user_id, {
                'assessment_completed': True,
                'latest_assessment_id': assessment_id,
                'assessment_completion_date': datetime.now(timezone.utc).isoformat()
            })
            
            return assessment_id
            
        except Exception as e:
            print(f"Failed to save assessment: {e}")
            raise
    
    async def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get assessment by ID"""
        try:
            doc_ref = self.db.collection('assessments').document(assessment_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            encrypted_data = doc.to_dict()
            
            # Decrypt sensitive fields
            sensitive_fields = ['responses']
            decrypted_data = data_encryption.decrypt_dict(
                encrypted_data,
                sensitive_fields
            )
            
            return decrypted_data
            
        except Exception as e:
            print(f"Failed to get assessment {assessment_id}: {e}")
            return None
    
    async def get_user_assessments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all assessments for a user"""
        try:
            assessments_ref = self.db.collection('assessments')
            query = assessments_ref.where('user_id', '==', user_id).order_by('completed_at', direction=firestore.Query.DESCENDING)
            docs = query.get()
            
            assessments = []
            for doc in docs:
                encrypted_data = doc.to_dict()
                # Decrypt for analysis
                sensitive_fields = ['responses']
                decrypted_data = data_encryption.decrypt_dict(
                    encrypted_data,
                    sensitive_fields
                )
                assessments.append(decrypted_data)
            
            return assessments
            
        except Exception as e:
            print(f"Failed to get assessments for user {user_id}: {e}")
            return []
    
    # Coaching Plans Management
    
    async def save_coaching_plan(self, plan_data: Dict[str, Any]) -> str:
        """Save AI-generated coaching plan"""
        try:
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{plan_data['user_id'][:8]}"
            
            # Encrypt sensitive plan data
            sensitive_fields = ['detailed_plan', 'personalized_recommendations']
            encrypted_plan = data_encryption.encrypt_dict(plan_data, sensitive_fields)
            
            encrypted_plan['plan_id'] = plan_id
            encrypted_plan['created_at'] = datetime.now(timezone.utc).isoformat()
            
            self.db.collection('coaching_plans').document(plan_id).set(encrypted_plan)
            
            return plan_id
            
        except Exception as e:
            print(f"Failed to save coaching plan: {e}")
            raise
    
    async def get_coaching_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get coaching plan by ID"""
        try:
            doc_ref = self.db.collection('coaching_plans').document(plan_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            encrypted_data = doc.to_dict()
            
            # Decrypt sensitive fields
            sensitive_fields = ['detailed_plan', 'personalized_recommendations']
            decrypted_data = data_encryption.decrypt_dict(
                encrypted_data,
                sensitive_fields
            )
            
            return decrypted_data
            
        except Exception as e:
            print(f"Failed to get coaching plan {plan_id}: {e}")
            return None
    
    async def get_user_coaching_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all coaching plans for a user"""
        try:
            plans_ref = self.db.collection('coaching_plans')
            query = plans_ref.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING)
            docs = query.get()
            
            plans = []
            for doc in docs:
                encrypted_data = doc.to_dict()
                # Decrypt for user access
                sensitive_fields = ['detailed_plan', 'personalized_recommendations']
                decrypted_data = data_encryption.decrypt_dict(
                    encrypted_data,
                    sensitive_fields
                )
                plans.append(decrypted_data)
            
            return plans
            
        except Exception as e:
            print(f"Failed to get coaching plans for user {user_id}: {e}")
            return []
    
    # Session Management
    
    async def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save anonymized session data"""
        try:
            # Anonymize session data
            anonymized_session = anonymization_service.anonymize_session_data(session_data)
            session_id = anonymized_session['session_id']
            
            # Encrypt session outcomes
            sensitive_fields = ['outcomes']
            encrypted_session = data_encryption.encrypt_dict(
                anonymized_session,
                sensitive_fields
            )
            
            self.db.collection('sessions').document(session_id).set(encrypted_session)
            
            # Update user session count
            await self.increment_user_sessions(session_data['user_id'])
            
            return session_id
            
        except Exception as e:
            print(f"Failed to save session: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user sessions with pagination"""
        try:
            sessions_ref = self.db.collection('sessions')
            query = sessions_ref.where('user_id', '==', user_id).order_by('session_date', direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.get()
            
            sessions = []
            for doc in docs:
                encrypted_data = doc.to_dict()
                # Decrypt for user access
                sensitive_fields = ['outcomes']
                decrypted_data = data_encryption.decrypt_dict(
                    encrypted_data,
                    sensitive_fields
                )
                sessions.append(decrypted_data)
            
            return sessions
            
        except Exception as e:
            print(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    async def increment_user_sessions(self, user_id: str):
        """Increment user session count for analytics"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'total_sessions_count': firestore.Increment(1),
                'last_session_date': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            print(f"Failed to update session count for {user_id}: {e}")
    
    # Analytics (Aggregated/Anonymous)
    
    async def get_platform_analytics(self) -> Dict[str, Any]:
        """Get anonymized platform analytics"""
        try:
            # Total users (approximate)
            users_count = len(list(self.db.collection('users').select([]).get()))
            
            # Total sessions
            sessions_count = len(list(self.db.collection('sessions').select([]).get()))
            
            # User engagement metrics
            active_users_30d = self._count_active_users(30)
            
            return {
                'total_users': users_count,
                'total_sessions': sessions_count,
                'active_users_30d': active_users_30d,
                'average_sessions_per_user': sessions_count / max(users_count, 1),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"Failed to get platform analytics: {e}")
            return {}
    
    def _count_active_users(self, days: int) -> int:
        """Count users active in the last N days"""
        try:
            cutoff_date = datetime.now(timezone.utc).replace(day=datetime.now().day - days)
            cutoff_iso = cutoff_date.isoformat()
            
            active_users = self.db.collection('users').where('last_active', '>=', cutoff_iso).get()
            return len(list(active_users))
            
        except Exception as e:
            print(f"Failed to count active users: {e}")
            return 0
    
    # Marketplace Data (Public/Static)
    
    async def get_coaches(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get available coaches (public data)"""
        try:
            coaches_ref = self.db.collection('coaches')
            
            if filters:
                # Apply filters
                query = coaches_ref
                if 'category' in filters:
                    query = query.where('category', '==', filters['category'])
                if 'available' in filters:
                    query = query.where('available', '==', filters['available'])
                    
                docs = query.get()
            else:
                docs = coaches_ref.get()
            
            coaches = []
            for doc in docs:
                coach_data = doc.to_dict()
                # Remove any sensitive information
                public_coach_data = {
                    'coach_id': doc.id,
                    'name': coach_data.get('name'),
                    'title': coach_data.get('title'),
                    'specialties': coach_data.get('specialties', []),
                    'rating': coach_data.get('rating', 0),
                    'reviews_count': coach_data.get('reviews_count', 0),
                    'price_per_session': coach_data.get('price_per_session'),
                    'available_durations': coach_data.get('available_durations', []),
                    'image_url': coach_data.get('image_url'),
                    'description': coach_data.get('description'),
                    'category': coach_data.get('category'),
                    'availability': coach_data.get('availability', 'available')
                }
                coaches.append(public_coach_data)
            
            return coaches
            
        except Exception as e:
            print(f"Failed to get coaches: {e}")
            return []
    
    async def get_courses(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get available courses (public data)"""
        try:
            courses_ref = self.db.collection('courses')
            
            if filters:
                query = courses_ref
                if 'category' in filters:
                    query = query.where('category', '==', filters['category'])
                docs = query.get()
            else:
                docs = courses_ref.get()
            
            courses = []
            for doc in docs:
                course_data = doc.to_dict()
                public_course_data = {
                    'course_id': doc.id,
                    'name': course_data.get('name'),
                    'instructor': course_data.get('instructor'),
                    'description': course_data.get('description'),
                    'modules': course_data.get('modules', []),
                    'duration_hours': course_data.get('duration_hours'),
                    'price': course_data.get('price'),
                    'rating': course_data.get('rating', 0),
                    'reviews_count': course_data.get('reviews_count', 0),
                    'category': course_data.get('category'),
                    'level': course_data.get('level'),
                    'image_url': course_data.get('image_url')
                }
                courses.append(public_course_data)
            
            return courses
            
        except Exception as e:
            current_app.logger.error(f"Failed to get courses: {e}")
            return []


# Global service instance
firebase_service = FirebaseService()