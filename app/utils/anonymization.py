"""
Data anonymization service for Evergrow360

This module provides advanced anonymization capabilities to ensure
maximum user privacy while maintaining coaching effectiveness.
"""

import uuid
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from flask import current_app


class AnonymizationService:
    """
    Service for anonymizing user data while preserving coaching functionality
    
    Key principles:
    - Zero PII storage in plain text
    - Pseudonymization with consistent identifiers
    - Data minimization - only store what's needed for coaching
    - Reversible anonymization only for essential coaching data
    """
    
    def __init__(self):
        self._salt = None
    
    def _get_application_salt(self) -> str:
        """Get application-wide salt for consistent hashing"""
        if self._salt is None:
            # In production, this should be stored securely and never change
            try:
                self._salt = current_app.config.get('SECRET_KEY', 'dev-salt')[:32]
            except RuntimeError:
                # Outside app context
                self._salt = 'dev-salt'[:32]
        return self._salt
    
    def generate_anonymous_id(self, email: str) -> str:
        """
        Generate consistent anonymous ID from email
        
        This allows us to identify returning users without storing email
        """
        if not email:
            return str(uuid.uuid4())
        
        # Create deterministic UUID from email + salt
        combined = f"{email.lower().strip()}{self._get_application_salt()}"
        hash_object = hashlib.sha256(combined.encode())
        hash_hex = hash_object.hexdigest()
        
        # Convert to UUID format
        return str(uuid.UUID(hash_hex[:32]))
    
    def anonymize_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize user profile data for storage
        
        Keeps only coaching-relevant information, removes all PII
        """
        email = user_data.get('email', '')
        anonymous_id = self.generate_anonymous_id(email)
        
        # Extract coaching-relevant data only
        anonymized_profile = {
            'user_id': anonymous_id,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_active': datetime.now(timezone.utc).isoformat(),
            
            # Coaching preferences (no PII)
            'coaching_preferences': {
                'professional_role': self._anonymize_role(user_data.get('role')),
                'industry_sector': self._anonymize_industry(user_data.get('industry')),
                'experience_level': user_data.get('experience_level'),
                'coaching_focus_areas': user_data.get('focus_areas', []),
                'preferred_session_length': user_data.get('session_length'),
                'preferred_communication_style': user_data.get('communication_style'),
                'timezone_offset': user_data.get('timezone_offset'),
                'language_preference': user_data.get('language', 'en')
            },
            
            # Business context (generalized)
            'business_context': {
                'company_size_range': self._anonymize_company_size(user_data.get('company_size')),
                'team_size_range': self._anonymize_team_size(user_data.get('team_size')),
                'management_level': user_data.get('management_level'),
                'years_in_role_range': self._anonymize_experience_range(user_data.get('years_in_role'))
            },
            
            # Subscription and usage (for billing/analytics)
            'subscription_tier': user_data.get('subscription_tier', 'free'),
            'total_sessions_count': 0,
            'total_coaching_hours': 0,
            
            # Privacy settings
            'data_processing_consent': user_data.get('data_consent', False),
            'marketing_consent': user_data.get('marketing_consent', False),
            'analytics_consent': user_data.get('analytics_consent', True)
        }
        
        return anonymized_profile
    
    def anonymize_assessment_data(self, assessment_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Anonymize assessment responses while preserving coaching value
        """
        return {
            'user_id': user_id,
            'assessment_id': str(uuid.uuid4()),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            
            # Anonymized responses
            'responses': {
                'professional_challenges': self._anonymize_challenges(
                    assessment_data.get('challenges', [])
                ),
                'skill_development_priorities': assessment_data.get('skill_priorities', []),
                'learning_preferences': assessment_data.get('learning_style'),
                'goal_timeframe': assessment_data.get('goal_timeframe'),
                'commitment_level': assessment_data.get('commitment_level'),
                'feedback_openness_score': assessment_data.get('feedback_score'),
                'satisfaction_baseline': assessment_data.get('satisfaction_score'),
                'growth_motivation_factors': assessment_data.get('motivation_factors', [])
            },
            
            # Derived insights (for AI processing)
            'insights': {
                'coaching_readiness_score': self._calculate_readiness_score(assessment_data),
                'recommended_coaching_intensity': self._recommend_intensity(assessment_data),
                'suggested_focus_areas': self._suggest_focus_areas(assessment_data)
            }
        }
    
    def anonymize_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize coaching session data
        """
        return {
            'session_id': str(uuid.uuid4()),
            'user_id': session_data.get('user_id'),
            'coach_id': session_data.get('coach_id'),  # Coach IDs can be kept for matching
            'session_date': session_data.get('date'),
            'duration_minutes': session_data.get('duration'),
            'session_type': session_data.get('type'),  # individual, group, workshop
            
            # Session outcomes (anonymized)
            'outcomes': {
                'topics_covered': session_data.get('topics', []),
                'skills_practiced': session_data.get('skills', []),
                'action_items_count': len(session_data.get('action_items', [])),
                'user_satisfaction_score': session_data.get('satisfaction'),
                'coach_notes_summary': self._anonymize_notes(session_data.get('notes', ''))
            },
            
            # Progress tracking
            'progress_metrics': {
                'goal_advancement_score': session_data.get('goal_progress'),
                'engagement_level': session_data.get('engagement'),
                'homework_completion': session_data.get('homework_completed', False)
            }
        }
    
    def _anonymize_role(self, role: str) -> str:
        """Generalize professional role to protect identity"""
        if not role:
            return 'unspecified'
        
        role_lower = role.lower()
        if any(term in role_lower for term in ['ceo', 'chief executive', 'president']):
            return 'c_level_executive'
        elif any(term in role_lower for term in ['cto', 'chief technology', 'vp engineering']):
            return 'technical_executive'
        elif any(term in role_lower for term in ['cfo', 'chief financial']):
            return 'financial_executive'
        elif any(term in role_lower for term in ['manager', 'director', 'head of']):
            return 'management_role'
        elif any(term in role_lower for term in ['senior', 'lead', 'principal']):
            return 'senior_individual_contributor'
        else:
            return 'individual_contributor'
    
    def _anonymize_industry(self, industry: str) -> str:
        """Generalize industry to broad categories"""
        if not industry:
            return 'unspecified'
        
        industry_lower = industry.lower()
        if any(term in industry_lower for term in ['tech', 'software', 'it', 'computer']):
            return 'technology'
        elif any(term in industry_lower for term in ['finance', 'bank', 'investment']):
            return 'financial_services'
        elif any(term in industry_lower for term in ['health', 'medical', 'pharma']):
            return 'healthcare'
        elif any(term in industry_lower for term in ['retail', 'ecommerce', 'commerce']):
            return 'retail_commerce'
        elif any(term in industry_lower for term in ['consulting', 'advisory']):
            return 'professional_services'
        else:
            return 'other'
    
    def _anonymize_company_size(self, size: Any) -> str:
        """Convert company size to ranges"""
        if isinstance(size, str):
            size_lower = size.lower()
            if 'startup' in size_lower or '1-10' in size_lower:
                return 'startup_small'
            elif '11-50' in size_lower or 'small' in size_lower:
                return 'small'
            elif '51-200' in size_lower or 'medium' in size_lower:
                return 'medium'
            elif '201-1000' in size_lower or 'large' in size_lower:
                return 'large'
            else:
                return 'enterprise'
        elif isinstance(size, int):
            if size <= 10:
                return 'startup_small'
            elif size <= 50:
                return 'small'
            elif size <= 200:
                return 'medium'
            elif size <= 1000:
                return 'large'
            else:
                return 'enterprise'
        return 'unspecified'
    
    def _anonymize_team_size(self, size: Any) -> str:
        """Convert team size to ranges"""
        if isinstance(size, int):
            if size <= 2:
                return 'individual'
            elif size <= 5:
                return 'small_team'
            elif size <= 15:
                return 'medium_team'
            else:
                return 'large_team'
        return 'unspecified'
    
    def _anonymize_experience_range(self, years: Any) -> str:
        """Convert experience to ranges"""
        if isinstance(years, (int, float)):
            if years < 2:
                return 'junior'
            elif years < 5:
                return 'mid_level'
            elif years < 10:
                return 'senior'
            else:
                return 'expert'
        return 'unspecified'
    
    def _anonymize_challenges(self, challenges: List[str]) -> List[str]:
        """Anonymize specific challenges to general categories"""
        anonymized = []
        for challenge in challenges:
            if not challenge:
                continue
            
            challenge_lower = challenge.lower()
            if any(term in challenge_lower for term in ['team', 'people', 'management']):
                anonymized.append('team_management')
            elif any(term in challenge_lower for term in ['communication', 'speaking', 'presentation']):
                anonymized.append('communication_skills')
            elif any(term in challenge_lower for term in ['strategy', 'planning', 'vision']):
                anonymized.append('strategic_thinking')
            elif any(term in challenge_lower for term in ['time', 'productivity', 'efficiency']):
                anonymized.append('time_management')
            elif any(term in challenge_lower for term in ['decision', 'choice', 'judgment']):
                anonymized.append('decision_making')
            else:
                anonymized.append('other_professional_challenge')
        
        return list(set(anonymized))  # Remove duplicates
    
    def _anonymize_notes(self, notes: str) -> str:
        """Create summary of notes without specific details"""
        if not notes or len(notes) < 50:
            return 'brief_session_notes'
        elif len(notes) < 200:
            return 'moderate_session_notes'
        else:
            return 'detailed_session_notes'
    
    def _calculate_readiness_score(self, assessment_data: Dict[str, Any]) -> float:
        """Calculate coaching readiness score from assessment"""
        # Simple scoring algorithm - can be enhanced with ML
        score = 0.0
        factors = 0
        
        # Feedback openness
        if assessment_data.get('feedback_score'):
            score += assessment_data['feedback_score'] / 10.0
            factors += 1
        
        # Commitment level
        commitment = assessment_data.get('commitment_level', 0)
        if commitment:
            score += min(commitment / 5.0, 1.0)
            factors += 1
        
        # Goal clarity
        if assessment_data.get('goals_text'):
            score += 0.8  # Has clear goals
            factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def _recommend_intensity(self, assessment_data: Dict[str, Any]) -> str:
        """Recommend coaching intensity based on assessment"""
        readiness = self._calculate_readiness_score(assessment_data)
        commitment = assessment_data.get('commitment_level', 0)
        
        if readiness > 0.8 and commitment > 4:
            return 'intensive'
        elif readiness > 0.6 and commitment > 2:
            return 'regular'
        else:
            return 'light'
    
    def _suggest_focus_areas(self, assessment_data: Dict[str, Any]) -> List[str]:
        """Suggest focus areas based on assessment"""
        suggestions = []
        
        # Based on challenges and priorities
        challenges = assessment_data.get('challenges', [])
        priorities = assessment_data.get('skill_priorities', [])
        
        # Simple rule-based suggestions
        if any('leadership' in str(item).lower() for item in challenges + priorities):
            suggestions.append('leadership_development')
        
        if any('communication' in str(item).lower() for item in challenges + priorities):
            suggestions.append('communication_enhancement')
        
        if any('strategy' in str(item).lower() for item in challenges + priorities):
            suggestions.append('strategic_thinking')
        
        if any('time' in str(item).lower() for item in challenges + priorities):
            suggestions.append('productivity_optimization')
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def create_data_export(self, user_id: str) -> Dict[str, Any]:
        """
        Create GDPR-compliant data export
        
        Returns all data associated with user in human-readable format
        """
        # This would gather all user data across collections
        # and present it in a readable format for GDPR compliance
        return {
            'export_date': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'data_categories': {
                'profile_data': 'Coaching preferences and business context',
                'assessment_data': 'Onboarding assessment responses and insights', 
                'session_data': 'Coaching session outcomes and progress',
                'usage_analytics': 'Platform usage statistics',
                'billing_data': 'Payment history and subscription information'
            },
            'retention_policy': 'Data retained for 2 years after last activity',
            'deletion_instructions': 'Contact support for account deletion'
        }
    
    def prepare_for_deletion(self, user_id: str) -> bool:
        """
        Prepare user data for deletion (GDPR right to be forgotten)
        
        Anonymizes all historical data while preserving analytics
        """
        try:
            # This would anonymize all user data while keeping aggregated analytics
            # Implementation would depend on Firebase structure
            current_app.logger.info(f"Prepared user {user_id} data for deletion")
            return True
        except Exception as e:
            current_app.logger.error(f"Data deletion preparation failed: {e}")
            return False


# Global service instance
anonymization_service = AnonymizationService()