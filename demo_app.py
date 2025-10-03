#!/usr/bin/env python3
"""
Evergrow360 Backend Demo - Simplified Version
Demonstrates Flask + Jinja2 + Mock Firebase + Mock OpenAI integration
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Simple Flask app without external dependencies for demo
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
    from jinja2 import Template
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available - creating demo files only")

# Mock services to demonstrate functionality
class MockFirebaseService:
    """Mock Firebase service demonstrating data structure and operations"""
    
    def __init__(self):
        self.users = {}
        self.assessments = {}
        self.coaching_plans = {}
        self.sessions = {}
    
    def save_user(self, user_data):
        user_id = self._generate_anonymous_id(user_data.get('email', ''))
        anonymized_data = self._anonymize_user_data(user_data)
        self.users[user_id] = anonymized_data
        return user_id
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def save_assessment(self, assessment_data):
        assessment_id = str(uuid.uuid4())
        self.assessments[assessment_id] = assessment_data
        return assessment_id
    
    def save_coaching_plan(self, plan_data):
        plan_id = str(uuid.uuid4())
        self.coaching_plans[plan_id] = plan_data
        return plan_id
    
    def _generate_anonymous_id(self, email):
        """Generate consistent anonymous ID from email"""
        if not email:
            return str(uuid.uuid4())
        
        # Simple hash for demo
        hash_object = hashlib.sha256(email.encode())
        return hash_object.hexdigest()[:32]
    
    def _anonymize_user_data(self, user_data):
        """Anonymize user data for storage"""
        return {
            'user_id': self._generate_anonymous_id(user_data.get('email', '')),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'coaching_preferences': {
                'professional_role': user_data.get('role', 'unspecified'),
                'industry_sector': user_data.get('industry', 'unspecified'),
                'experience_level': user_data.get('experience', 'unspecified'),
                'coaching_focus_areas': user_data.get('focus_areas', []),
            },
            'subscription_tier': user_data.get('subscription', 'free'),
            'data_processing_consent': user_data.get('consent', True)
        }

class MockOpenAIService:
    """Mock OpenAI service demonstrating AI coaching functionality"""
    
    def analyze_assessment(self, assessment_data):
        """Mock assessment analysis"""
        return {
            'strengths': [
                'Strong analytical thinking',
                'Open to feedback and learning',
                'Clear professional goals'
            ],
            'development_areas': [
                'Leadership communication',
                'Strategic planning',
                'Team motivation'
            ],
            'coaching_readiness': 8,
            'recommended_intensity': 'regular',
            'success_factors': [
                'High commitment level',
                'Clear objectives',
                'Growth mindset'
            ],
            'recommended_focus': [
                'Leadership development',
                'Communication skills',
                'Strategic thinking'
            ],
            'learning_approach': 'Combination of individual coaching and group workshops',
            'confidence_score': 0.85
        }
    
    def generate_coaching_plan(self, user_profile, assessment_insights, goals):
        """Mock coaching plan generation"""
        return {
            'plan_overview': 'Comprehensive leadership development program tailored to your role and goals',
            'phases': [
                {
                    'phase_name': 'Assessment and Foundation',
                    'duration_weeks': 2,
                    'objectives': ['Establish baseline', 'Set clear goals', 'Build coaching relationship'],
                    'key_activities': ['360-degree feedback', 'Goal setting workshop', 'Strengths assessment'],
                    'success_metrics': ['Clear goal definition', 'Baseline measurements', 'Action plan created']
                },
                {
                    'phase_name': 'Skill Development',
                    'duration_weeks': 8,
                    'objectives': ['Build core leadership skills', 'Practice new behaviors', 'Apply learning'],
                    'key_activities': ['Weekly coaching sessions', 'Skill practice exercises', 'Real-world application'],
                    'success_metrics': ['Skill improvement scores', 'Behavior change evidence', 'Feedback improvements']
                },
                {
                    'phase_name': 'Integration and Mastery',
                    'duration_weeks': 4,
                    'objectives': ['Integrate new habits', 'Sustain improvements', 'Plan continued growth'],
                    'key_activities': ['Advanced scenarios', 'Peer coaching', 'Long-term planning'],
                    'success_metrics': ['Sustained behavior change', 'Goal achievement', 'Future growth plan']
                }
            ],
            'weekly_structure': {
                'individual_sessions': '1 hour per week',
                'group_activities': '2 hours every 2 weeks', 
                'self_study': '2-3 hours per week',
                'practice_time': '1-2 hours per week'
            },
            'resources': [
                'Leadership assessment tools',
                'Communication skill builders',
                'Strategic thinking frameworks',
                'Recommended reading list'
            ],
            'estimated_duration_weeks': 14
        }

# Demo data for showcase
DEMO_COACHES = [
    {
        'id': 'coach_001',
        'name': 'Sarah Thompson',
        'title': 'Executive Leadership Coach',
        'specialties': ['C-Suite Leadership', 'Strategic Thinking', 'Executive Presence'],
        'experience_years': 15,
        'rating': 4.9,
        'review_count': 127,
        'price_per_hour': 350,
        'bio': 'Former Fortune 500 executive with 15+ years coaching C-level leaders',
        'availability': 'Available this week'
    },
    {
        'id': 'coach_002', 
        'name': 'Michael Rodriguez',
        'title': 'Technology Leadership Coach',
        'specialties': ['Engineering Management', 'Team Building', 'Technical Leadership'],
        'experience_years': 12,
        'rating': 4.8,
        'review_count': 89,
        'price_per_hour': 275,
        'bio': 'Ex-Google engineering director specializing in tech leadership development',
        'availability': 'Available next week'
    },
    {
        'id': 'coach_003',
        'name': 'Jennifer Park',
        'title': 'Communication & Influence Coach', 
        'specialties': ['Executive Communication', 'Public Speaking', 'Influence & Persuasion'],
        'experience_years': 10,
        'rating': 4.9,
        'review_count': 156,
        'price_per_hour': 300,
        'bio': 'Former McKinsey consultant specializing in executive communication',
        'availability': 'Available today'
    }
]

if FLASK_AVAILABLE:
    app = Flask(__name__)
    app.secret_key = 'demo-secret-key'
    
    # Initialize mock services
    firebase_service = MockFirebaseService()
    openai_service = MockOpenAIService()
    
    @app.route('/')
    def index():
        """Homepage with platform overview"""
        stats = {
            'total_coaches': len(DEMO_COACHES),
            'successful_sessions': 2547,
            'average_rating': 4.8,
            'user_satisfaction': 96
        }
        return render_template('index.html', stats=stats)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration with server-side processing"""
        if request.method == 'POST':
            user_data = {
                'email': request.form.get('email'),
                'role': request.form.get('role'),
                'industry': request.form.get('industry'),
                'experience': request.form.get('experience'),
                'consent': request.form.get('consent') == 'on'
            }
            
            # Save anonymized user data
            user_id = firebase_service.save_user(user_data)
            session['user_id'] = user_id
            
            flash('Registration successful! Welcome to Evergrow360.', 'success')
            return redirect(url_for('assessment'))
        
        return render_template('auth/register.html')
    
    @app.route('/assessment', methods=['GET', 'POST'])
    def assessment():
        """AI-powered assessment with server-side processing"""
        if 'user_id' not in session:
            return redirect(url_for('register'))
        
        if request.method == 'POST':
            assessment_data = {
                'user_id': session['user_id'],
                'professional_role': request.form.get('role'),
                'main_challenges': request.form.getlist('challenges'),
                'skill_priorities': request.form.getlist('skills'),
                'learning_style': request.form.get('learning_style'),
                'goal_timeframe': request.form.get('timeframe'),
                'commitment_level': int(request.form.get('commitment', 1)),
                'feedback_openness_score': int(request.form.get('feedback', 1)),
                'satisfaction_baseline': int(request.form.get('satisfaction', 1)),
                'submitted_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Save assessment
            assessment_id = firebase_service.save_assessment(assessment_data)
            
            # Generate AI analysis
            ai_analysis = openai_service.analyze_assessment(assessment_data)
            
            # Save coaching plan
            user = firebase_service.get_user(session['user_id'])
            coaching_plan = openai_service.generate_coaching_plan(user, ai_analysis, [])
            
            plan_data = {
                'user_id': session['user_id'],
                'assessment_id': assessment_id,
                'ai_analysis': ai_analysis,
                'coaching_plan': coaching_plan,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            plan_id = firebase_service.save_coaching_plan(plan_data)
            session['coaching_plan_id'] = plan_id
            
            flash('Assessment complete! Your personalized coaching plan is ready.', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('assessment/form.html')
    
    @app.route('/dashboard')
    def dashboard():
        """User dashboard with progress and recommendations"""
        if 'user_id' not in session:
            return redirect(url_for('register'))
        
        user = firebase_service.get_user(session['user_id'])
        coaching_plan = None
        
        if 'coaching_plan_id' in session:
            coaching_plan = firebase_service.coaching_plans.get(session['coaching_plan_id'])
        
        dashboard_data = {
            'user': user,
            'coaching_plan': coaching_plan,
            'upcoming_sessions': [],  # Would be populated from database
            'recent_achievements': [
                'Completed leadership assessment',
                'Set 3 professional development goals',
                'Started coaching journey'
            ],
            'next_steps': [
                'Book your first coaching session',
                'Review your personalized plan',
                'Connect with recommended coaches'
            ]
        }
        
        return render_template('dashboard/index.html', data=dashboard_data)
    
    @app.route('/marketplace')
    def marketplace():
        """Coach marketplace with filtering and search"""
        search_query = request.args.get('search', '')
        specialty_filter = request.args.get('specialty', '')
        price_filter = request.args.get('price', '')
        
        coaches = DEMO_COACHES.copy()
        
        # Apply filters (simplified for demo)
        if search_query:
            coaches = [c for c in coaches if search_query.lower() in c['name'].lower() or 
                      search_query.lower() in c['title'].lower()]
        
        if specialty_filter:
            coaches = [c for c in coaches if specialty_filter in c['specialties']]
        
        if price_filter:
            if price_filter == 'low':
                coaches = [c for c in coaches if c['price_per_hour'] < 300]
            elif price_filter == 'high':
                coaches = [c for c in coaches if c['price_per_hour'] >= 300]
        
        return render_template('marketplace/index.html', 
                             coaches=coaches, 
                             search_query=search_query,
                             specialty_filter=specialty_filter,
                             price_filter=price_filter)
    
    @app.route('/coach/<coach_id>')
    def coach_profile(coach_id):
        """Individual coach profile page"""
        coach = next((c for c in DEMO_COACHES if c['id'] == coach_id), None)
        if not coach:
            flash('Coach not found.', 'error')
            return redirect(url_for('marketplace'))
        
        return render_template('coach/profile.html', coach=coach)
    
    @app.route('/book/<coach_id>', methods=['GET', 'POST'])
    def book_session(coach_id):
        """Session booking with coach"""
        coach = next((c for c in DEMO_COACHES if c['id'] == coach_id), None)
        if not coach:
            flash('Coach not found.', 'error')
            return redirect(url_for('marketplace'))
        
        if request.method == 'POST':
            booking_data = {
                'coach_id': coach_id,
                'user_id': session.get('user_id'),
                'session_date': request.form.get('date'),
                'session_time': request.form.get('time'),
                'session_type': request.form.get('type'),
                'duration': int(request.form.get('duration', 60)),
                'total_cost': coach['price_per_hour'] * (int(request.form.get('duration', 60)) / 60),
                'booked_at': datetime.now(timezone.utc).isoformat()
            }
            
            # In real implementation, would process payment and create calendar event
            flash(f'Session booked with {coach["name"]} for {booking_data["session_date"]} at {booking_data["session_time"]}!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('booking/form.html', coach=coach)
    
    @app.route('/api/assessment/analyze', methods=['POST'])
    def api_analyze_assessment():
        """API endpoint for assessment analysis"""
        try:
            data = request.get_json()
            
            # Validate and sanitize input
            if not data or 'assessment_data' not in data:
                return jsonify({'error': 'Invalid input data'}), 400
            
            # Generate AI analysis
            analysis = openai_service.analyze_assessment(data['assessment_data'])
            
            return jsonify({
                'status': 'success',
                'analysis': analysis,
                'confidence_score': analysis['confidence_score']
            })
            
        except Exception as e:
            return jsonify({'error': 'Analysis failed', 'message': str(e)}), 500
    
    @app.route('/api/coaching/plan', methods=['POST'])  
    def api_generate_plan():
        """API endpoint for coaching plan generation"""
        try:
            data = request.get_json()
            
            if not data or 'user_profile' not in data or 'goals' not in data:
                return jsonify({'error': 'Invalid input data'}), 400
            
            # Generate coaching plan
            plan = openai_service.generate_coaching_plan(
                data['user_profile'],
                data.get('assessment_insights', {}),
                data['goals']
            )
            
            return jsonify({
                'status': 'success',
                'coaching_plan': plan
            })
            
        except Exception as e:
            return jsonify({'error': 'Plan generation failed', 'message': str(e)}), 500
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'evergrow360-demo',
            'version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    if __name__ == '__main__':
        app.run(debug=True, host='127.0.0.1', port=5000)

else:
    print("Demo backend created successfully!")
    print("To run: pip install flask && python demo_app.py")