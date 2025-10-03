"""
User management API endpoints for Evergrow360
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

from app.utils.security import require_auth, log_access, input_sanitizer
from app.services.firebase_service import firebase_service

# Create blueprint
user_bp = Blueprint('user', __name__)

# Validation schemas
class ProfileUpdateSchema(Schema):
    first_name = fields.Str(required=False, validate=validate.Length(max=50))
    last_name = fields.Str(required=False, validate=validate.Length(max=50))
    company = fields.Str(required=False, validate=validate.Length(max=100))
    job_title = fields.Str(required=False, validate=validate.Length(max=100))
    industry = fields.Str(required=False, validate=validate.Length(max=100))
    experience_years = fields.Int(required=False, validate=validate.Range(min=0, max=50))
    location = fields.Str(required=False, validate=validate.Length(max=100))
    timezone = fields.Str(required=False, validate=validate.Length(max=50))
    bio = fields.Str(required=False, validate=validate.Length(max=500))
    linkedin_url = fields.Url(required=False)
    website_url = fields.Url(required=False)
    phone = fields.Str(required=False, validate=validate.Length(max=20))


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@log_access('get_user_profile', 'user_data')
def get_profile():
    """Get user profile (anonymized)"""
    try:
        current_user_id = get_jwt_identity()

        # Get user profile from Firebase
        user_profile = firebase_service.get_user_profile_sync(current_user_id)

        if not user_profile:
            return jsonify({
                'error': 'User profile not found'
            }), 404

        # Return anonymized profile data
        profile_data = {
            'user_id': current_user_id,
            'first_name': user_profile.get('first_name', ''),
            'last_name': user_profile.get('last_name', ''),
            'company': user_profile.get('company', ''),
            'job_title': user_profile.get('job_title', ''),
            'industry': user_profile.get('industry', ''),
            'experience_years': user_profile.get('experience_years', 0),
            'location': user_profile.get('location', ''),
            'timezone': user_profile.get('timezone', 'UTC'),
            'bio': user_profile.get('bio', ''),
            'linkedin_url': user_profile.get('linkedin_url', ''),
            'website_url': user_profile.get('website_url', ''),
            'phone': user_profile.get('phone', ''),
            'registration_date': user_profile.get('registration_date'),
            'last_login': user_profile.get('last_login'),
            'onboarding_completed': user_profile.get('onboarding_completed', False),
            'assessment_completed': user_profile.get('assessment_completed', False),
            'subscription_tier': user_profile.get('subscription_tier', 'free'),
            'profile_completion_percentage': calculate_profile_completion(user_profile)
        }

        return jsonify(profile_data), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get user profile: {e}")
        return jsonify({
            'error': 'Failed to retrieve profile',
            'message': 'Unable to load user profile'
        }), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
@log_access('update_user_profile', 'user_data')
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()

        # Validate request data
        schema = ProfileUpdateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400

        # Sanitize text inputs
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = input_sanitizer.sanitize_string(value)
            else:
                sanitized_data[key] = value

        # Add update metadata
        sanitized_data['updated_at'] = datetime.utcnow().isoformat()
        sanitized_data['profile_last_updated'] = datetime.utcnow().isoformat()

        # Update user profile in Firebase
        success = firebase_service.update_user_profile(current_user_id, sanitized_data)

        if success:
            # Get updated profile to return
            updated_profile = firebase_service.get_user_profile(current_user_id)

            profile_data = {
                'user_id': current_user_id,
                'first_name': updated_profile.get('first_name', ''),
                'last_name': updated_profile.get('last_name', ''),
                'company': updated_profile.get('company', ''),
                'job_title': updated_profile.get('job_title', ''),
                'industry': updated_profile.get('industry', ''),
                'experience_years': updated_profile.get('experience_years', 0),
                'location': updated_profile.get('location', ''),
                'timezone': updated_profile.get('timezone', 'UTC'),
                'bio': updated_profile.get('bio', ''),
                'linkedin_url': updated_profile.get('linkedin_url', ''),
                'website_url': updated_profile.get('website_url', ''),
                'phone': updated_profile.get('phone', ''),
                'profile_completion_percentage': calculate_profile_completion(updated_profile)
            }

            return jsonify({
                'message': 'Profile updated successfully',
                'profile': profile_data
            }), 200
        else:
            return jsonify({
                'error': 'Failed to update profile'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Failed to update user profile: {e}")
        return jsonify({
            'error': 'Failed to update profile',
            'message': 'Unable to save profile changes'
        }), 500


@user_bp.route('/profile/completion', methods=['GET'])
@jwt_required()
def get_profile_completion():
    """Get profile completion status and suggestions"""
    try:
        current_user_id = get_jwt_identity()

        user_profile = firebase_service.get_user_profile(current_user_id)

        if not user_profile:
            return jsonify({
                'error': 'User profile not found'
            }), 404

        completion_percentage = calculate_profile_completion(user_profile)
        completion_status = get_completion_status(completion_percentage)
        missing_fields = get_missing_fields(user_profile)

        return jsonify({
            'completion_percentage': completion_percentage,
            'completion_status': completion_status,
            'missing_fields': missing_fields,
            'next_steps': get_completion_suggestions(missing_fields),
            'is_complete': completion_percentage >= 80
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get profile completion: {e}")
        return jsonify({
            'error': 'Failed to get completion status',
            'message': 'Unable to calculate profile completion'
        }), 500


@user_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
@log_access('get_user_dashboard', 'user_data')
def get_dashboard_summary():
    """Get user dashboard summary data"""
    try:
        current_user_id = get_jwt_identity()

        # Get user profile
        user_profile = firebase_service.get_user_profile(current_user_id)

        if not user_profile:
            return jsonify({
                'error': 'User profile not found'
            }), 404

        # Get recent assessments
        assessments = firebase_service.get_user_assessments(current_user_id, limit=5)

        # Get coaching plans
        coaching_plans = firebase_service.get_user_coaching_plans(current_user_id)

        # Get upcoming sessions (mock data for now)
        upcoming_sessions = [
            {
                'id': 'session_001',
                'coach_name': 'Sarah Thompson',
                'date': '2024-01-15T14:00:00Z',
                'type': '1-on-1 Coaching',
                'status': 'confirmed'
            }
        ]

        # Calculate dashboard metrics
        dashboard_data = {
            'user': {
                'name': f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip() or 'User',
                'onboarding_completed': user_profile.get('onboarding_completed', False),
                'assessment_completed': user_profile.get('assessment_completed', False),
                'subscription_tier': user_profile.get('subscription_tier', 'free')
            },
            'stats': {
                'assessments_completed': len(assessments),
                'coaching_plans_active': len([p for p in coaching_plans if p.get('status') == 'active']),
                'sessions_completed': 12,  # Mock data
                'goals_achieved': 8  # Mock data
            },
            'recent_activity': [
                {
                    'type': 'assessment',
                    'title': 'Leadership Assessment Completed',
                    'date': assessments[0].get('completed_at') if assessments else None,
                    'status': 'completed'
                },
                {
                    'type': 'session',
                    'title': 'Coaching Session with Sarah Thompson',
                    'date': '2024-01-10T14:00:00Z',
                    'status': 'completed'
                }
            ],
            'upcoming_sessions': upcoming_sessions,
            'current_goals': [
                'Improve executive communication skills',
                'Develop strategic thinking capabilities',
                'Build stronger leadership presence'
            ],
            'recommendations': [
                'Book your next coaching session',
                'Review your personalized development plan',
                'Complete the communication skills assessment'
            ]
        }

        return jsonify(dashboard_data), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get dashboard summary: {e}")
        return jsonify({
            'error': 'Failed to get dashboard data',
            'message': 'Unable to load dashboard information'
        }), 500


def calculate_profile_completion(user_profile):
    """Calculate profile completion percentage"""
    required_fields = [
        'first_name', 'last_name', 'job_title', 'industry',
        'experience_years', 'location', 'bio'
    ]

    optional_fields = [
        'company', 'timezone', 'linkedin_url', 'website_url', 'phone'
    ]

    completed_required = sum(1 for field in required_fields
                           if user_profile.get(field) and str(user_profile[field]).strip())

    completed_optional = sum(1 for field in optional_fields
                           if user_profile.get(field) and str(user_profile[field]).strip())

    # Required fields: 70% weight, Optional fields: 30% weight
    required_score = (completed_required / len(required_fields)) * 70
    optional_score = (completed_optional / len(optional_fields)) * 30

    return round(required_score + optional_score, 1)


def get_completion_status(percentage):
    """Get completion status based on percentage"""
    if percentage >= 90:
        return 'excellent'
    elif percentage >= 80:
        return 'good'
    elif percentage >= 60:
        return 'fair'
    else:
        return 'incomplete'


def get_missing_fields(user_profile):
    """Get list of missing profile fields"""
    fields_to_check = [
        'first_name', 'last_name', 'company', 'job_title',
        'industry', 'experience_years', 'location', 'bio',
        'linkedin_url', 'phone'
    ]

    missing = []
    for field in fields_to_check:
        if not user_profile.get(field) or not str(user_profile[field]).strip():
            missing.append(field)

    return missing


def get_completion_suggestions(missing_fields):
    """Get suggestions for completing the profile"""
    suggestions = []

    if 'first_name' in missing_fields or 'last_name' in missing_fields:
        suggestions.append('Add your full name to personalize your experience')

    if 'job_title' in missing_fields:
        suggestions.append('Specify your current job title for better coaching recommendations')

    if 'industry' in missing_fields:
        suggestions.append('Add your industry to connect with relevant coaches')

    if 'bio' in missing_fields:
        suggestions.append('Write a brief bio to help coaches understand your background')

    if 'linkedin_url' in missing_fields:
        suggestions.append('Link your LinkedIn profile for professional networking')

    if not suggestions:
        suggestions.append('Your profile is well-completed! Consider updating it regularly.')

    return suggestions