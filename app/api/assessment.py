"""
Assessment API endpoints for Evergrow360

This module provides AI-powered assessment functionality:
- Submit assessment responses
- Get AI analysis results
- Retrieve assessment history
- Generate coaching insights
"""

from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

from app.utils.security import require_auth, log_access, input_sanitizer
from app.services.firebase_service import firebase_service
from app.services.ai_service import ai_coaching_service

# Create blueprint
assessment_bp = Blueprint('assessment', __name__)


# Validation schemas
class AssessmentSubmissionSchema(Schema):
    professional_role = fields.Str(required=True, validate=validate.Length(max=100))
    main_challenges = fields.List(fields.Str(validate=validate.Length(max=200)), required=True)
    skill_priorities = fields.List(fields.Str(validate=validate.Length(max=100)), required=True)
    learning_style = fields.Str(required=True, validate=validate.OneOf([
        'individual_coaching', 'group_workshops', 'self_paced', 
        'reading_research', 'hands_on_practice', 'video_tutorials'
    ]))
    goal_timeframe = fields.Str(required=True, validate=validate.OneOf([
        '1_month', '3_months', '6_months', '1_year', 'ongoing'
    ]))
    commitment_level = fields.Int(required=True, validate=validate.Range(min=1, max=5))
    feedback_openness_score = fields.Int(required=True, validate=validate.Range(min=1, max=10))
    satisfaction_baseline = fields.Int(required=True, validate=validate.Range(min=1, max=10))
    goals_text = fields.Str(required=False, validate=validate.Length(max=1000))
    additional_context = fields.Str(required=False, validate=validate.Length(max=500))


@assessment_bp.route('/form', methods=['GET'])
@jwt_required()
@log_access('view_assessment_form', 'assessment_data')
def assessment_form():
    """
    Render the assessment form using server-side templates
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user has already completed assessment
        user_profile = firebase_service.get_user_profile_sync(current_user_id)
        if user_profile and user_profile.get('assessment_completed'):
            return redirect(url_for('assessment.results', assessment_id=user_profile.get('latest_assessment_id')))
        
        # Get assessment form structure
        assessment_form = {
            'title': 'Evergrow360 Leadership Assessment',
            'description': 'Complete this assessment to receive personalized coaching insights and development recommendations.',
            'sections': [
                {
                    'id': 'professional_info',
                    'title': 'Professional Information',
                    'questions': [
                        {
                            'id': 'professional_role',
                            'type': 'text',
                            'label': 'What is your current professional role?',
                            'placeholder': 'e.g., Senior Manager, Team Lead, Individual Contributor',
                            'required': True,
                            'maxLength': 100
                        }
                    ]
                },
                {
                    'id': 'challenges',
                    'title': 'Current Challenges',
                    'questions': [
                        {
                            'id': 'main_challenges',
                            'type': 'multiselect',
                            'label': 'What are your main professional challenges? (Select all that apply)',
                            'options': [
                                'Leading remote teams',
                                'Managing difficult conversations',
                                'Building team culture',
                                'Performance management',
                                'Strategic planning',
                                'Change management',
                                'Work-life balance',
                                'Career development',
                                'Communication skills',
                                'Conflict resolution',
                                'Time management',
                                'Decision making',
                                'Motivation and engagement',
                                'Diversity and inclusion',
                                'Other'
                            ],
                            'required': True,
                            'minSelections': 1,
                            'maxSelections': 5
                        }
                    ]
                },
                {
                    'id': 'skills',
                    'title': 'Skill Development Priorities',
                    'questions': [
                        {
                            'id': 'skill_priorities',
                            'type': 'multiselect',
                            'label': 'Which skills would you like to develop? (Select up to 3)',
                            'options': [
                                'Leadership presence',
                                'Emotional intelligence',
                                'Strategic thinking',
                                'Communication',
                                'Conflict resolution',
                                'Team building',
                                'Change management',
                                'Performance coaching',
                                'Decision making',
                                'Time management',
                                'Networking',
                                'Public speaking',
                                'Project management',
                                'Innovation',
                                'Other'
                            ],
                            'required': True,
                            'minSelections': 1,
                            'maxSelections': 3
                        }
                    ]
                },
                {
                    'id': 'learning',
                    'title': 'Learning Preferences',
                    'questions': [
                        {
                            'id': 'learning_style',
                            'type': 'radio',
                            'label': 'What is your preferred learning style?',
                            'options': [
                                {'value': 'individual_coaching', 'label': 'One-on-one coaching sessions'},
                                {'value': 'group_workshops', 'label': 'Group workshops and seminars'},
                                {'value': 'self_paced', 'label': 'Self-paced online learning'},
                                {'value': 'reading_research', 'label': 'Reading and research'},
                                {'value': 'hands_on_practice', 'label': 'Hands-on practice and exercises'},
                                {'value': 'video_tutorials', 'label': 'Video tutorials and webinars'}
                            ],
                            'required': True
                        }
                    ]
                },
                {
                    'id': 'goals',
                    'title': 'Goals and Timeline',
                    'questions': [
                        {
                            'id': 'goal_timeframe',
                            'type': 'radio',
                            'label': 'What is your timeline for achieving your development goals?',
                            'options': [
                                {'value': '1_month', 'label': 'Within 1 month'},
                                {'value': '3_months', 'label': 'Within 3 months'},
                                {'value': '6_months', 'label': 'Within 6 months'},
                                {'value': '1_year', 'label': 'Within 1 year'},
                                {'value': 'ongoing', 'label': 'Ongoing development'}
                            ],
                            'required': True
                        },
                        {
                            'id': 'goals_text',
                            'type': 'textarea',
                            'label': 'Describe your specific development goals (optional)',
                            'placeholder': 'What do you want to achieve in your professional development?',
                            'required': False,
                            'maxLength': 1000
                        }
                    ]
                },
                {
                    'id': 'commitment',
                    'title': 'Commitment and Readiness',
                    'questions': [
                        {
                            'id': 'commitment_level',
                            'type': 'scale',
                            'label': 'On a scale of 1-5, how committed are you to your professional development?',
                            'min': 1,
                            'max': 5,
                            'minLabel': 'Low commitment',
                            'maxLabel': 'High commitment',
                            'required': True
                        },
                        {
                            'id': 'feedback_openness_score',
                            'type': 'scale',
                            'label': 'On a scale of 1-10, how open are you to receiving constructive feedback?',
                            'min': 1,
                            'max': 10,
                            'minLabel': 'Not open',
                            'maxLabel': 'Very open',
                            'required': True
                        },
                        {
                            'id': 'satisfaction_baseline',
                            'type': 'scale',
                            'label': 'On a scale of 1-10, how satisfied are you with your current professional situation?',
                            'min': 1,
                            'max': 10,
                            'minLabel': 'Very dissatisfied',
                            'maxLabel': 'Very satisfied',
                            'required': True
                        }
                    ]
                },
                {
                    'id': 'additional',
                    'title': 'Additional Context',
                    'questions': [
                        {
                            'id': 'additional_context',
                            'type': 'textarea',
                            'label': 'Is there any additional context about your professional situation or goals that would be helpful for us to know?',
                            'placeholder': 'Any other information that might help us provide better coaching insights...',
                            'required': False,
                            'maxLength': 500
                        }
                    ]
                }
            ],
            'estimated_completion_time': '10-15 minutes',
            'privacy_note': 'Your responses are confidential and used only to provide personalized coaching insights.'
        }
        
        return render_template('assessment/form.html', 
                             assessment=assessment_form,
                             user_profile=user_profile)
        
    except Exception as e:
        current_app.logger.error(f"Failed to render assessment form: {e}")
        return render_template('error.html', 
                             error='Unable to load assessment',
                             message='Please try again later.'), 500


@assessment_bp.route('/submit-form', methods=['POST'])
@jwt_required()
@log_access('submit_assessment_form', 'assessment_data')
def submit_assessment_form():
    """
    Handle assessment form submission with server-side rendering
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get form data
        form_data = {}
        for key in request.form:
            if key.endswith('[]'):
                # Handle multiple select fields
                form_data[key[:-2]] = request.form.getlist(key)
            else:
                form_data[key] = request.form.get(key)
        
        # Validate required fields
        schema = AssessmentSubmissionSchema()
        try:
            validated_data = schema.load(form_data)
        except ValidationError as err:
            # Re-render form with errors
            assessment_form = {
                'title': 'Evergrow360 Leadership Assessment',
                'description': 'Complete this assessment to receive personalized coaching insights and development recommendations.',
                'sections': []  # We'll rebuild this
            }
            user_profile = firebase_service.get_user_profile_sync(current_user_id)
            return render_template('assessment/form.html',
                                 assessment=assessment_form,
                                 user_profile=user_profile,
                                 errors=err.messages,
                                 form_data=form_data), 400
        
        # Sanitize text inputs
        sanitized_data = {}
        for key, value in validated_data.items():
            if isinstance(value, str):
                sanitized_data[key] = input_sanitizer.sanitize_string(value)
            elif isinstance(value, list):
                sanitized_data[key] = [
                    input_sanitizer.sanitize_string(str(item)) for item in value
                ]
            else:
                sanitized_data[key] = value
        
        # Add submission metadata
        sanitized_data['user_id'] = current_user_id
        sanitized_data['submitted_at'] = datetime.utcnow().isoformat()
        
        # Save assessment to Firebase
        assessment_id = firebase_service.save_assessment_sync(sanitized_data, current_user_id)
        
        # Generate AI analysis
        try:
            ai_analysis = ai_coaching_service.analyze_assessment_sync(sanitized_data)
            
            # Save AI analysis results
            analysis_data = {
                'user_id': current_user_id,
                'assessment_id': assessment_id,
                'ai_analysis': ai_analysis,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
            analysis_id = firebase_service.save_coaching_plan_sync(analysis_data)
            
        except Exception as ai_error:
            current_app.logger.error(f"AI analysis failed: {ai_error}")
            # Continue without AI analysis - user can still proceed
            ai_analysis = None
            analysis_id = None
        
        # Update user profile to mark assessment as completed
        firebase_service.update_user_profile_sync(current_user_id, {
            'assessment_completed': True,
            'assessment_completion_date': datetime.utcnow().isoformat(),
            'onboarding_completed': True
        })
        
        # Redirect to results page
        return redirect(url_for('assessment.results', assessment_id=assessment_id))
        
    except Exception as e:
        current_app.logger.error(f"Assessment form submission failed: {e}")
        return render_template('error.html',
                             error='Assessment submission failed',
                             message='Please try again.'), 500


@assessment_bp.route('/results/<assessment_id>')
@jwt_required()
@log_access('view_assessment_results', 'assessment_data')
def results(assessment_id):
    """
    Display assessment results using server-side rendering
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get assessment data
        assessment = firebase_service.get_assessment(assessment_id)
        if not assessment:
            return render_template('error.html',
                                 error='Assessment not found',
                                 message='The requested assessment could not be found.'), 404
        
        # Verify ownership
        if assessment.get('user_id') != current_user_id:
            return render_template('error.html',
                                 error='Access denied',
                                 message='You can only view your own assessments.'), 403
        
        # Get coaching plans associated with this assessment
        user_plans = firebase_service.get_user_coaching_plans(current_user_id)
        ai_analysis = None
        
        for plan in user_plans:
            if plan.get('assessment_id') == assessment_id:
                ai_analysis = plan.get('ai_analysis')
                break
        
        # Prepare template data
        results_data = {
            'assessment_id': assessment_id,
            'submitted_at': assessment.get('submitted_at'),
            'responses': assessment.get('responses', {}),
            'ai_analysis': ai_analysis,
            'has_ai_analysis': ai_analysis is not None
        }
        
        return render_template('assessment/results.html', 
                             results=results_data,
                             assessment=assessment)
        
    except Exception as e:
        current_app.logger.error(f"Failed to render assessment results: {e}")
        return render_template('error.html',
                             error='Unable to load results',
                             message='Please try again later.'), 500


@assessment_bp.route('/submit', methods=['POST'])
@jwt_required()
@log_access('submit_assessment', 'assessment_data')
def submit_assessment():
    """
    Submit user assessment for AI analysis
    
    Processes assessment responses and generates AI insights
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Validate request data
        schema = AssessmentSubmissionSchema()
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
            elif isinstance(value, list):
                sanitized_data[key] = [
                    input_sanitizer.sanitize_string(str(item)) for item in value
                ]
            else:
                sanitized_data[key] = value
        
        # Add submission metadata
        sanitized_data['user_id'] = current_user_id
        sanitized_data['submitted_at'] = datetime.utcnow().isoformat()
        
        # Save assessment to Firebase
        assessment_id = firebase_service.save_assessment_sync(sanitized_data, current_user_id)
        
        # Generate AI analysis
        try:
            ai_analysis = ai_coaching_service.analyze_assessment_sync(sanitized_data)
            
            # Save AI analysis results
            analysis_data = {
                'user_id': current_user_id,
                'assessment_id': assessment_id,
                'ai_analysis': ai_analysis,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
            analysis_id = firebase_service.save_coaching_plan_sync(analysis_data)
            
        except Exception as ai_error:
            current_app.logger.error(f"AI analysis failed: {ai_error}")
            # Continue without AI analysis - user can still proceed
            ai_analysis = None
            analysis_id = None
        
        # Update user profile to mark assessment as completed
        firebase_service.update_user_profile_sync(current_user_id, {
            'assessment_completed': True,
            'assessment_completion_date': datetime.utcnow().isoformat(),
            'onboarding_completed': True
        })
        
        response_data = {
            'message': 'Assessment submitted successfully',
            'assessment_id': assessment_id,
            'ai_analysis_available': ai_analysis is not None
        }
        
        if ai_analysis:
            response_data['analysis_id'] = analysis_id
            response_data['insights'] = {
                'coaching_readiness': ai_analysis.get('coaching_readiness', 'Unknown'),
                'recommended_intensity': ai_analysis.get('recommended_intensity', 'regular'),
                'top_strengths': ai_analysis.get('strengths', [])[:3],
                'development_areas': ai_analysis.get('development_areas', [])[:3]
            }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        current_app.logger.error(f"Assessment submission failed: {e}")
        return jsonify({
            'error': 'Assessment submission failed',
            'message': 'Unable to process assessment'
        }), 500


@assessment_bp.route('/results/<assessment_id>', methods=['GET'])
@jwt_required()
@log_access('get_assessment_results', 'assessment_data')
def get_assessment_results(assessment_id):
    """
    Get assessment results and AI analysis
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get assessment data
        assessment = firebase_service.get_assessment(assessment_id)
        if not assessment:
            return jsonify({
                'error': 'Assessment not found'
            }), 404
        
        # Verify ownership
        if assessment.get('user_id') != current_user_id:
            return jsonify({
                'error': 'Access denied',
                'message': 'You can only access your own assessments'
            }), 403
        
        # Get coaching plans associated with this assessment
        user_plans = firebase_service.get_user_coaching_plans(current_user_id)
        ai_analysis = None
        
        for plan in user_plans:
            if plan.get('assessment_id') == assessment_id:
                ai_analysis = plan.get('ai_analysis')
                break
        
        # Prepare response data
        response_data = {
            'assessment_id': assessment_id,
            'submitted_at': assessment.get('completed_at'),
            'responses_summary': {
                'professional_role': assessment.get('responses', {}).get('professional_challenges'),
                'focus_areas': assessment.get('responses', {}).get('skill_development_priorities'),
                'learning_preference': assessment.get('responses', {}).get('learning_preferences'),
                'commitment_level': assessment.get('responses', {}).get('commitment_level'),
                'satisfaction_baseline': assessment.get('responses', {}).get('satisfaction_baseline')
            }
        }
        
        if ai_analysis:
            response_data['ai_insights'] = {
                'strengths': ai_analysis.get('strengths', []),
                'development_areas': ai_analysis.get('development_areas', []),
                'coaching_readiness': ai_analysis.get('coaching_readiness'),
                'recommended_intensity': ai_analysis.get('recommended_intensity'),
                'success_factors': ai_analysis.get('success_factors', []),
                'recommended_focus': ai_analysis.get('recommended_focus', []),
                'learning_approach': ai_analysis.get('learning_approach'),
                'confidence_score': ai_analysis.get('confidence_score', 0.8)
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get assessment results: {e}")
        return jsonify({
            'error': 'Failed to retrieve assessment results',
            'message': 'Unable to get assessment data'
        }), 500


@assessment_bp.route('/history', methods=['GET'])
@jwt_required()
@log_access('get_assessment_history', 'assessment_data')
def get_assessment_history():
    """
    Get user's assessment history
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get all assessments for user
        assessments = firebase_service.get_user_assessments(current_user_id)
        
        # Format response data
        assessment_history = []
        for assessment in assessments:
            assessment_summary = {
                'assessment_id': assessment.get('assessment_id'),
                'completed_at': assessment.get('completed_at'),
                'insights_summary': assessment.get('insights', {}),
                'has_ai_analysis': 'ai_analysis' in assessment
            }
            assessment_history.append(assessment_summary)
        
        return jsonify({
            'assessments': assessment_history,
            'total_count': len(assessment_history)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get assessment history: {e}")
        return jsonify({
            'error': 'Failed to retrieve assessment history',
            'message': 'Unable to get assessment data'
        }), 500


@assessment_bp.route('/retake', methods=['POST'])
@jwt_required()
@log_access('retake_assessment', 'assessment_data')
def retake_assessment():
    """
    Allow user to retake assessment (e.g., after 6 months)
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's last assessment
        assessments = firebase_service.get_user_assessments(current_user_id)
        
        if not assessments:
            return jsonify({
                'error': 'No previous assessment found',
                'message': 'Please take the initial assessment first'
            }), 404
        
        # Check if enough time has passed since last assessment
        last_assessment = assessments[0]  # Most recent
        last_date = datetime.fromisoformat(last_assessment.get('completed_at'))
        time_since_last = datetime.utcnow() - last_date
        
        # Require at least 30 days between assessments
        min_days = 30
        if time_since_last.days < min_days:
            days_remaining = min_days - time_since_last.days
            return jsonify({
                'error': 'Assessment retake not available yet',
                'message': f'Please wait {days_remaining} more days before retaking the assessment',
                'days_remaining': days_remaining
            }), 429
        
        # Mark previous assessments as historical
        firebase_service.update_user_profile(current_user_id, {
            'assessment_completed': False,
            'retake_assessment_available': True
        })
        
        return jsonify({
            'message': 'Assessment retake enabled',
            'previous_assessments': len(assessments)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Assessment retake failed: {e}")
        return jsonify({
            'error': 'Assessment retake failed',
            'message': 'Unable to enable assessment retake'
        }), 500


@assessment_bp.route('/insights/detailed/<assessment_id>', methods=['GET'])
@jwt_required()
@log_access('get_detailed_insights', 'assessment_data')
def get_detailed_insights(assessment_id):
    """
    Get detailed AI insights for an assessment
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get assessment
        assessment = firebase_service.get_assessment(assessment_id)
        if not assessment or assessment.get('user_id') != current_user_id:
            return jsonify({
                'error': 'Assessment not found or access denied'
            }), 404
        
        # Get coaching plans with detailed analysis
        user_plans = firebase_service.get_user_coaching_plans(current_user_id)
        detailed_analysis = None
        
        for plan in user_plans:
            if plan.get('assessment_id') == assessment_id:
                detailed_analysis = plan.get('ai_analysis')
                break
        
        if not detailed_analysis:
            return jsonify({
                'error': 'AI analysis not available',
                'message': 'Detailed insights have not been generated for this assessment'
            }), 404
        
        # Return comprehensive insights
        return jsonify({
            'assessment_id': assessment_id,
            'detailed_insights': detailed_analysis,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get detailed insights: {e}")
        return jsonify({
            'error': 'Failed to retrieve detailed insights',
            'message': 'Unable to get insight data'
        }), 500


@assessment_bp.route('/coaching-readiness', methods=['GET'])
@jwt_required()
@log_access('get_coaching_readiness', 'assessment_data')
def get_coaching_readiness():
    """
    Get current coaching readiness score and recommendations
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get latest assessment
        assessments = firebase_service.get_user_assessments(current_user_id)
        if not assessments:
            return jsonify({
                'error': 'No assessment found',
                'message': 'Please complete the assessment first'
            }), 404
        
        latest_assessment = assessments[0]
        insights = latest_assessment.get('insights', {})
        
        # Calculate readiness score
        readiness_score = insights.get('coaching_readiness_score', 0.5)
        
        # Determine readiness level
        if readiness_score >= 0.8:
            readiness_level = 'high'
            readiness_message = 'You are highly ready for intensive coaching'
        elif readiness_score >= 0.6:
            readiness_level = 'medium'
            readiness_message = 'You are ready for regular coaching sessions'
        else:
            readiness_level = 'low'
            readiness_message = 'Consider starting with light coaching to build readiness'
        
        return jsonify({
            'readiness_score': readiness_score,
            'readiness_level': readiness_level,
            'readiness_message': readiness_message,
            'recommended_intensity': insights.get('recommended_coaching_intensity', 'regular'),
            'suggested_focus_areas': insights.get('suggested_focus_areas', []),
            'assessment_date': latest_assessment.get('completed_at')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Failed to get coaching readiness: {e}")
        return jsonify({
            'error': 'Failed to get coaching readiness',
            'message': 'Unable to calculate readiness score'
        }), 500