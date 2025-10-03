"""
Marketplace API endpoints for Evergrow360
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create blueprint
marketplace_bp = Blueprint('marketplace', __name__)

# Mock data for coaches
MOCK_COACHES = [
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
        'availability': 'Available this week',
        'image_url': '/app/shared/images/coach-1.jpg',
        'languages': ['English', 'Spanish'],
        'certifications': ['PCC', 'MCC', 'Executive Coaching Certification']
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
        'availability': 'Available next week',
        'image_url': '/app/shared/images/coach-2.jpg',
        'languages': ['English', 'Portuguese'],
        'certifications': ['PCC', 'Agile Coaching Certification']
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
        'availability': 'Available today',
        'image_url': '/app/shared/images/coach-3.jpg',
        'languages': ['English', 'Korean'],
        'certifications': ['PCC', 'Presentation Skills Certification']
    },
    {
        'id': 'coach_004',
        'name': 'David Chen',
        'title': 'Change Management Coach',
        'specialties': ['Organizational Change', 'Transformation Leadership', 'Crisis Management'],
        'experience_years': 18,
        'rating': 4.7,
        'review_count': 203,
        'price_per_hour': 325,
        'bio': 'Former Deloitte partner with extensive experience in large-scale transformations',
        'availability': 'Available in 2 weeks',
        'image_url': '/app/shared/images/coach-4.jpg',
        'languages': ['English', 'Mandarin'],
        'certifications': ['MCC', 'Change Management Certification']
    },
    {
        'id': 'coach_005',
        'name': 'Lisa Johnson',
        'title': 'Diversity & Inclusion Coach',
        'specialties': ['DEI Leadership', 'Inclusive Culture', 'Unconscious Bias'],
        'experience_years': 14,
        'rating': 4.8,
        'review_count': 98,
        'price_per_hour': 290,
        'bio': 'Former CHRO at Fortune 500 company specializing in inclusive leadership',
        'availability': 'Available this month',
        'image_url': '/app/shared/images/coach-5.jpg',
        'languages': ['English', 'French'],
        'certifications': ['PCC', 'DEI Certification', 'Cultural Intelligence']
    },
    {
        'id': 'coach_006',
        'name': 'Robert Kim',
        'title': 'Financial Leadership Coach',
        'specialties': ['CFO Coaching', 'Financial Strategy', 'Risk Management'],
        'experience_years': 16,
        'rating': 4.6,
        'review_count': 134,
        'price_per_hour': 340,
        'bio': 'Former investment banker and CFO coach for multinational corporations',
        'availability': 'Available next week',
        'image_url': '/app/shared/images/coach-6.jpg',
        'languages': ['English', 'Japanese'],
        'certifications': ['PCC', 'Financial Leadership Certification']
    }
]

# Mock data for courses
MOCK_COURSES = [
    {
        'id': 'course_001',
        'title': 'Executive Presence & Communication',
        'instructor': 'Jennifer Park',
        'instructor_id': 'coach_003',
        'description': 'Master the art of executive communication and build commanding presence',
        'duration_weeks': 8,
        'price': 1200,
        'rating': 4.8,
        'enrollment_count': 245,
        'level': 'Intermediate',
        'topics': ['Public Speaking', 'Executive Presence', 'Stakeholder Communication'],
        'format': 'Video + Live Sessions',
        'image_url': '/app/shared/images/course-1.jpg'
    },
    {
        'id': 'course_002',
        'title': 'Strategic Leadership for Tech Executives',
        'instructor': 'Michael Rodriguez',
        'instructor_id': 'coach_002',
        'description': 'Navigate complex technology landscapes and lead engineering organizations',
        'duration_weeks': 12,
        'price': 1800,
        'rating': 4.7,
        'enrollment_count': 189,
        'level': 'Advanced',
        'topics': ['Technology Strategy', 'Engineering Leadership', 'Innovation Management'],
        'format': 'Video + Group Coaching',
        'image_url': '/app/shared/images/course-2.jpg'
    },
    {
        'id': 'course_003',
        'title': 'Leading Through Change',
        'instructor': 'David Chen',
        'instructor_id': 'coach_004',
        'description': 'Develop skills to lead organizations through transformation and uncertainty',
        'duration_weeks': 10,
        'price': 1500,
        'rating': 4.9,
        'enrollment_count': 312,
        'level': 'Advanced',
        'topics': ['Change Management', 'Crisis Leadership', 'Organizational Transformation'],
        'format': 'Video + Case Studies',
        'image_url': '/app/shared/images/course-3.jpg'
    }
]


@marketplace_bp.route('/coaches', methods=['GET'])
def get_coaches():
    """Get available coaches with filtering and search"""
    try:
        # Get query parameters
        search = request.args.get('search', '').lower()
        specialty = request.args.get('specialty', '').lower()
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        min_rating = request.args.get('min_rating', type=float)
        availability = request.args.get('availability', '').lower()
        sort_by = request.args.get('sort_by', 'rating')  # rating, price, experience
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc

        # Start with all coaches
        coaches = MOCK_COACHES.copy()

        # Apply filters
        if search:
            coaches = [c for c in coaches if
                      search in c['name'].lower() or
                      search in c['title'].lower() or
                      any(search in s.lower() for s in c['specialties'])]

        if specialty:
            coaches = [c for c in coaches if
                      any(specialty in s.lower() for s in c['specialties'])]

        if min_price is not None:
            coaches = [c for c in coaches if c['price_per_hour'] >= min_price]

        if max_price is not None:
            coaches = [c for c in coaches if c['price_per_hour'] <= max_price]

        if min_rating is not None:
            coaches = [c for c in coaches if c['rating'] >= min_rating]

        if availability:
            coaches = [c for c in coaches if availability in c['availability'].lower()]

        # Sort results
        reverse = sort_order == 'desc'
        if sort_by == 'price':
            coaches.sort(key=lambda x: x['price_per_hour'], reverse=reverse)
        elif sort_by == 'experience':
            coaches.sort(key=lambda x: x['experience_years'], reverse=reverse)
        else:  # rating (default)
            coaches.sort(key=lambda x: x['rating'], reverse=reverse)

        return jsonify({
            'coaches': coaches,
            'total_count': len(coaches),
            'filters_applied': {
                'search': search,
                'specialty': specialty,
                'price_range': f"{min_price or 0}-{max_price or 'max'}",
                'min_rating': min_rating,
                'availability': availability
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get coaches: {e}")
        return jsonify({
            'error': 'Failed to retrieve coaches',
            'message': 'Unable to load coach data'
        }), 500


@marketplace_bp.route('/coaches/<coach_id>', methods=['GET'])
def get_coach_details(coach_id):
    """Get detailed information about a specific coach"""
    try:
        coach = next((c for c in MOCK_COACHES if c['id'] == coach_id), None)

        if not coach:
            return jsonify({
                'error': 'Coach not found'
            }), 404

        # Add additional details for detailed view
        detailed_coach = coach.copy()
        detailed_coach.update({
            'detailed_bio': f"{coach['bio']}. With over {coach['experience_years']} years of experience, {coach['name'].split()[0]} has helped numerous executives achieve breakthrough results in their leadership journeys.",
            'education': [
                'MBA from Top-Tier Business School',
                'Executive Coaching Certification',
                'Advanced Leadership Development Programs'
            ],
            'client_types': [
                'C-Suite Executives',
                'VP/Director Level Leaders',
                'High-Potential Managers'
            ],
            'sample_reviews': [
                {
                    'rating': 5,
                    'text': 'Exceptional coach who helped me navigate a major career transition.',
                    'client': 'Anonymous Executive'
                },
                {
                    'rating': 5,
                    'text': 'Transformative experience that accelerated my leadership growth.',
                    'client': 'Anonymous Executive'
                }
            ],
            'packages': [
                {
                    'name': 'Discovery Session',
                    'duration': 60,
                    'price': coach['price_per_hour'],
                    'description': 'Initial consultation to assess coaching needs and fit'
                },
                {
                    'name': '3-Month Program',
                    'duration': 720,  # 12 sessions
                    'price': coach['price_per_hour'] * 12 * 0.9,  # 10% discount
                    'description': 'Comprehensive coaching program with regular sessions'
                },
                {
                    'name': '6-Month Transformation',
                    'duration': 1440,  # 24 sessions
                    'price': coach['price_per_hour'] * 24 * 0.85,  # 15% discount
                    'description': 'Extended program for deep leadership transformation'
                }
            ]
        })

        return jsonify(detailed_coach), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get coach details: {e}")
        return jsonify({
            'error': 'Failed to retrieve coach details',
            'message': 'Unable to load coach information'
        }), 500


@marketplace_bp.route('/courses', methods=['GET'])
def get_courses():
    """Get available courses with filtering"""
    try:
        # Get query parameters
        search = request.args.get('search', '').lower()
        instructor = request.args.get('instructor', '').lower()
        level = request.args.get('level', '').lower()
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        min_rating = request.args.get('min_rating', type=float)
        sort_by = request.args.get('sort_by', 'rating')  # rating, price, duration
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc

        # Start with all courses
        courses = MOCK_COURSES.copy()

        # Apply filters
        if search:
            courses = [c for c in courses if
                      search in c['title'].lower() or
                      search in c['description'].lower() or
                      any(search in t.lower() for t in c['topics'])]

        if instructor:
            courses = [c for c in courses if instructor in c['instructor'].lower()]

        if level:
            courses = [c for c in courses if level in c['level'].lower()]

        if min_price is not None:
            courses = [c for c in courses if c['price'] >= min_price]

        if max_price is not None:
            courses = [c for c in courses if c['price'] <= max_price]

        if min_rating is not None:
            courses = [c for c in courses if c['rating'] >= min_rating]

        # Sort results
        reverse = sort_order == 'desc'
        if sort_by == 'price':
            courses.sort(key=lambda x: x['price'], reverse=reverse)
        elif sort_by == 'duration':
            courses.sort(key=lambda x: x['duration_weeks'], reverse=reverse)
        else:  # rating (default)
            courses.sort(key=lambda x: x['rating'], reverse=reverse)

        return jsonify({
            'courses': courses,
            'total_count': len(courses),
            'filters_applied': {
                'search': search,
                'instructor': instructor,
                'level': level,
                'price_range': f"{min_price or 0}-{max_price or 'max'}",
                'min_rating': min_rating
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get courses: {e}")
        return jsonify({
            'error': 'Failed to retrieve courses',
            'message': 'Unable to load course data'
        }), 500


@marketplace_bp.route('/courses/<course_id>', methods=['GET'])
def get_course_details(course_id):
    """Get detailed information about a specific course"""
    try:
        course = next((c for c in MOCK_COURSES if c['id'] == course_id), None)

        if not course:
            return jsonify({
                'error': 'Course not found'
            }), 404

        # Add additional details for detailed view
        detailed_course = course.copy()
        detailed_course.update({
            'detailed_description': f"{course['description']}. This comprehensive program combines self-paced learning with live coaching sessions to accelerate your leadership development.",
            'learning_objectives': [
                'Develop advanced leadership skills and competencies',
                'Build strategic thinking and decision-making capabilities',
                'Enhance communication and influence skills',
                'Create actionable plans for professional growth'
            ],
            'curriculum': [
                {
                    'week': 1,
                    'title': 'Foundation & Assessment',
                    'topics': ['Self-assessment', 'Goal setting', 'Current state analysis']
                },
                {
                    'week': 2,
                    'title': 'Core Leadership Skills',
                    'topics': ['Communication fundamentals', 'Emotional intelligence', 'Team dynamics']
                },
                {
                    'week': 3,
                    'title': 'Strategic Thinking',
                    'topics': ['Problem-solving frameworks', 'Decision-making models', 'Long-term planning']
                }
            ],
            'prerequisites': [
                'Minimum 3 years management experience',
                'Commitment to personal development',
                'Access to computer and internet for virtual sessions'
            ],
            'included_materials': [
                'Video lectures and presentations',
                'Worksheets and exercises',
                'Reading materials and resources',
                'Access to online community',
                'Certificate of completion'
            ],
            'reviews': [
                {
                    'rating': 5,
                    'text': 'Transformative experience that completely changed my approach to leadership.',
                    'author': 'Anonymous Executive'
                },
                {
                    'rating': 5,
                    'text': 'Excellent content and outstanding instructor support throughout the program.',
                    'author': 'Anonymous Executive'
                }
            ]
        })

        return jsonify(detailed_course), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get course details: {e}")
        return jsonify({
            'error': 'Failed to retrieve course details',
            'message': 'Unable to load course information'
        }), 500


@marketplace_bp.route('/search', methods=['GET'])
def search_marketplace():
    """Unified search across coaches and courses"""
    try:
        query = request.args.get('q', '').lower()
        category = request.args.get('category', 'all')  # all, coaches, courses

        if not query:
            return jsonify({
                'error': 'Search query required'
            }), 400

        results = {
            'coaches': [],
            'courses': [],
            'total_results': 0
        }

        # Search coaches
        if category in ['all', 'coaches']:
            coach_results = []
            for coach in MOCK_COACHES:
                if (query in coach['name'].lower() or
                    query in coach['title'].lower() or
                    any(query in specialty.lower() for specialty in coach['specialties']) or
                    query in coach['bio'].lower()):
                    coach_results.append({
                        'id': coach['id'],
                        'name': coach['name'],
                        'title': coach['title'],
                        'type': 'coach',
                        'rating': coach['rating'],
                        'price': coach['price_per_hour']
                    })
            results['coaches'] = coach_results

        # Search courses
        if category in ['all', 'courses']:
            course_results = []
            for course in MOCK_COURSES:
                if (query in course['title'].lower() or
                    query in course['description'].lower() or
                    any(query in topic.lower() for topic in course['topics'])):
                    course_results.append({
                        'id': course['id'],
                        'title': course['title'],
                        'instructor': course['instructor'],
                        'type': 'course',
                        'rating': course['rating'],
                        'price': course['price']
                    })
            results['courses'] = course_results

        results['total_results'] = len(results['coaches']) + len(results['courses'])

        return jsonify(results), 200

    except Exception as e:
        current_app.logger.error(f"Failed to search marketplace: {e}")
        return jsonify({
            'error': 'Search failed',
            'message': 'Unable to perform search'
        }), 500