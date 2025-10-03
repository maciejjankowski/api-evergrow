"""
Coaching API endpoints for Evergrow360

This module provides AI-powered coaching functionality:
- Generate personalized coaching plans
- Get progress recommendations
- Track coaching goals
- Access coaching resources
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

from app.utils.security import require_auth, log_access, input_sanitizer
from app.services.firebase_service import firebase_service
from app.services.ai_service import ai_coaching_service

# Create blueprint
coaching_bp = Blueprint('coaching', __name__)


# Validation schemas
class CoachingPlanRequestSchema(Schema):
    goals = fields.List(fields.Str(validate=validate.Length(max=200)), required=True)
    timeframe = fields.Str(required=True, validate=validate.OneOf([
        '1_month', '3_months', '6_months', '1_year'
    ]))
    intensity = fields.Str(required=False, validate=validate.OneOf([
        'light', 'regular', 'intensive'
    ]))


@coaching_bp.route('/plan/generate', methods=['POST'])
@jwt_required()
@log_access('generate_coaching_plan', 'coaching_data')
def generate_coaching_plan():
    """
    Generate AI-powered coaching plan based on assessment and goals
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Validate request data
        schema = CoachingPlanRequestSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400
        
        # Get user profile and assessment
        user_profile = firebase_service.get_user_profile(current_user_id)
        if not user_profile:
            return jsonify({
                'error': 'User profile not found'
            }), 404
        
        # Get latest assessment
        assessments = firebase_service.get_user_assessments(current_user_id)
        if not assessments:
            return jsonify({
                'error': 'Assessment required',
                'message': 'Please complete the assessment before generating a coaching plan'
            }), 400
        
        latest_assessment = assessments[0]
        assessment_insights = latest_assessment.get('insights', {})
        
        # Sanitize goals
        sanitized_goals = [
            input_sanitizer.sanitize_string(goal) for goal in data['goals']
        ]
        
        # Generate AI coaching plan
        try:
            coaching_plan = ai_coaching_service.generate_coaching_plan(
                user_profile=user_profile,
                assessment_insights=assessment_insights,
                goals=sanitized_goals
            )
            
            # Save coaching plan
            plan_data = {
                'user_id': current_user_id,
                'goals': sanitized_goals,
                'timeframe': data['timeframe'],
                'intensity': data.get('intensity', 'regular'),
                'detailed_plan': coaching_plan,
                'generated_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            plan_id = firebase_service.save_coaching_plan(plan_data)
            
            return jsonify({
                'message': 'Coaching plan generated successfully',
                'plan_id': plan_id,
                'plan_overview': coaching_plan.get('plan_overview'),
                'phases': coaching_plan.get('phases', []),
                'estimated_duration_weeks': coaching_plan.get('estimated_duration_weeks', 12),
                'weekly_structure': coaching_plan.get('weekly_structure'),
                'success_indicators': coaching_plan.get('success_indicators', [])
            }), 201
            
        except Exception as ai_error:
            current_app.logger.error(f"AI coaching plan generation failed: {ai_error}")
            return jsonify({
                'error': 'Plan generation failed',
                'message': 'Unable to generate coaching plan at this time'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Coaching plan generation failed: {e}")
        return jsonify({
            'error': 'Plan generation failed',
            'message': 'An unexpected error occurred'
        }), 500


@coaching_bp.route('/plan/<plan_id>', methods=['GET'])
@jwt_required()
@log_access('get_coaching_plan', 'coaching_data')
def get_coaching_plan(plan_id):
    """
    Get specific coaching plan by ID
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get coaching plan
        plan = firebase_service.get_coaching_plan(plan_id)
        if not plan:
            return jsonify({
                'error': 'Coaching plan not found'
            }), 404
        
        # Verify ownership
        if plan.get('user_id') != current_user_id:
            return jsonify({
                'error': 'Access denied',
                'message': 'You can only access your own coaching plans'
            }), 403
        
        return jsonify({
            'plan_id': plan_id,
            'goals': plan.get('goals', []),
            'timeframe': plan.get('timeframe'),
            'intensity': plan.get('intensity'),
            'status': plan.get('status', 'active'),
            'created_at': plan.get('generated_at'),
            'plan_details': plan.get('detailed_plan', {}),
            'progress': plan.get('progress', {})
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get coaching plan: {e}")
        return jsonify({
            'error': 'Failed to retrieve coaching plan',
            'message': 'Unable to get plan data'
        }), 500


@coaching_bp.route('/plans', methods=['GET'])
@jwt_required()
@log_access('get_user_coaching_plans', 'coaching_data')
def get_user_coaching_plans():
    """
    Get all coaching plans for the current user
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get all coaching plans for user
        plans = firebase_service.get_user_coaching_plans(current_user_id)
        
        # Format response data
        plan_summaries = []
        for plan in plans:
            plan_summary = {
                'plan_id': plan.get('plan_id'),
                'goals': plan.get('goals', []),
                'timeframe': plan.get('timeframe'),
                'intensity': plan.get('intensity'),
                'status': plan.get('status', 'active'),
                'created_at': plan.get('generated_at'),
                'phases_count': len(plan.get('detailed_plan', {}).get('phases', [])),
                'progress_percentage': plan.get('progress', {}).get('overall_percentage', 0)
            }
            plan_summaries.append(plan_summary)
        
        return jsonify({
            'plans': plan_summaries,
            'total_count': len(plan_summaries),
            'active_plans': len([p for p in plan_summaries if p['status'] == 'active'])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get user coaching plans: {e}")
        return jsonify({
            'error': 'Failed to retrieve coaching plans',
            'message': 'Unable to get plans data'
        }), 500


@coaching_bp.route('/recommendations', methods=['GET'])
@jwt_required()
@log_access('get_coaching_recommendations', 'coaching_data')
def get_coaching_recommendations():
    """
    Get AI-powered coaching recommendations based on progress
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get user sessions for progress analysis
        sessions = firebase_service.get_user_sessions(current_user_id, limit=10)
        
        # Get current coaching plans
        plans = firebase_service.get_user_coaching_plans(current_user_id)
        active_plans = [p for p in plans if p.get('status') == 'active']
        
        if not active_plans:
            return jsonify({
                'error': 'No active coaching plan',
                'message': 'Please create a coaching plan first'
            }), 400
        
        # Get current goals from active plan
        current_goals = active_plans[0].get('goals', [])
        
        # Generate AI recommendations
        try:
            recommendations = ai_coaching_service.generate_progress_recommendations(
                user_sessions=sessions,
                current_goals=current_goals
            )
            
            return jsonify({
                'recommendations': recommendations,
                'based_on_sessions': len(sessions),
                'current_goals': current_goals,
                'generated_at': datetime.utcnow().isoformat()
            }), 200
            
        except Exception as ai_error:
            current_app.logger.error(f"AI recommendations failed: {ai_error}")
            return jsonify({
                'error': 'Recommendations unavailable',
                'message': 'Unable to generate recommendations at this time'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Failed to get coaching recommendations: {e}")
        return jsonify({
            'error': 'Failed to get recommendations',
            'message': 'Unable to generate recommendations'
        }), 500


@coaching_bp.route('/progress/update', methods=['POST'])
@jwt_required()
@log_access('update_coaching_progress', 'coaching_data')
def update_coaching_progress():
    """
    Update progress on coaching goals and activities
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({
                'error': 'Missing progress data'
            }), 400
        
        plan_id = data.get('plan_id')
        progress_updates = data.get('progress_updates', {})
        
        if not plan_id:
            return jsonify({
                'error': 'Plan ID required'
            }), 400
        
        # Get coaching plan
        plan = firebase_service.get_coaching_plan(plan_id)
        if not plan or plan.get('user_id') != current_user_id:
            return jsonify({
                'error': 'Coaching plan not found or access denied'
            }), 404
        
        # Update progress
        current_progress = plan.get('progress', {})
        current_progress.update(progress_updates)
        current_progress['last_updated'] = datetime.utcnow().isoformat()
        
        # Calculate overall progress percentage
        if 'goal_completions' in progress_updates:
            total_goals = len(plan.get('goals', []))
            completed_goals = sum(progress_updates['goal_completions'].values())
            overall_percentage = (completed_goals / total_goals * 100) if total_goals > 0 else 0
            current_progress['overall_percentage'] = round(overall_percentage, 1)
        
        # Update plan with new progress
        update_success = firebase_service.update_user_profile(current_user_id, {
            f'coaching_plans.{plan_id}.progress': current_progress
        })
        
        if update_success:
            return jsonify({
                'message': 'Progress updated successfully',
                'progress': current_progress
            }), 200
        else:
            return jsonify({
                'error': 'Failed to update progress'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Failed to update coaching progress: {e}")
        return jsonify({
            'error': 'Failed to update progress',
            'message': 'Unable to save progress updates'
        }), 500


@coaching_bp.route('/resources', methods=['GET'])
@jwt_required()
@log_access('get_coaching_resources', 'coaching_data')
def get_coaching_resources():
    """
    Get personalized coaching resources and materials
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get user profile for personalization
        user_profile = firebase_service.get_user_profile(current_user_id)
        if not user_profile:
            return jsonify({
                'error': 'User profile not found'
            }), 404
        
        # Get coaching preferences
        coaching_prefs = user_profile.get('coaching_preferences', {})
        focus_areas = coaching_prefs.get('coaching_focus_areas', [])
        
        # Generate personalized resources
        resources = {
            'articles': [
                {
                    'title': 'Effective Leadership Communication',
                    'description': 'Learn key strategies for clear, impactful leadership communication',
                    'url': '/resources/articles/leadership-communication',
                    'type': 'article',
                    'duration_minutes': 15,
                    'relevant_for': ['leadership', 'communication']
                },
                {
                    'title': 'Strategic Thinking Framework',
                    'description': 'A practical framework for developing strategic thinking skills',
                    'url': '/resources/articles/strategic-thinking',
                    'type': 'article',
                    'duration_minutes': 20,
                    'relevant_for': ['strategy', 'leadership']
                }
            ],
            'exercises': [
                {
                    'title': '360-Degree Feedback Reflection',
                    'description': 'Structured reflection on feedback received from colleagues',
                    'url': '/resources/exercises/360-feedback',
                    'type': 'exercise',
                    'duration_minutes': 30,
                    'relevant_for': ['leadership', 'self-awareness']
                },
                {
                    'title': 'Goal Setting Workshop',
                    'description': 'Interactive workshop for setting and tracking SMART goals',
                    'url': '/resources/exercises/goal-setting',
                    'type': 'exercise',
                    'duration_minutes': 45,
                    'relevant_for': ['goal-setting', 'productivity']
                }
            ],
            'tools': [
                {
                    'title': 'Leadership Assessment Tool',
                    'description': 'Self-assessment tool for identifying leadership strengths and gaps',
                    'url': '/resources/tools/leadership-assessment',
                    'type': 'tool',
                    'duration_minutes': 25,
                    'relevant_for': ['leadership', 'assessment']
                }
            ]
        }
        
        # Filter resources based on user's focus areas
        if focus_areas:
            filtered_resources = {}
            for category, items in resources.items():
                filtered_items = []
                for item in items:
                    item_relevance = item.get('relevant_for', [])
                    if any(area in item_relevance for area in focus_areas):
                        item['matched_areas'] = [area for area in focus_areas if area in item_relevance]
                        filtered_items.append(item)
                filtered_resources[category] = filtered_items
            resources = filtered_resources
        
        return jsonify({
            'resources': resources,
            'personalized_for': focus_areas,
            'total_items': sum(len(items) for items in resources.values())
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get coaching resources: {e}")
        return jsonify({
            'error': 'Failed to get resources',
            'message': 'Unable to retrieve coaching resources'
        }), 500