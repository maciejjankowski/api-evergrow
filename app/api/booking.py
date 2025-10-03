"""
Booking API endpoints for Evergrow360
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timedelta
import uuid

from app.utils.security import require_auth, log_access, input_sanitizer
from app.services.firebase_service import firebase_service

# Create blueprint
booking_bp = Blueprint('booking', __name__)

# Validation schemas
class BookingCreateSchema(Schema):
    coach_id = fields.Str(required=True)
    session_date = fields.DateTime(required=True)
    session_type = fields.Str(required=True, validate=validate.OneOf([
        'discovery', 'one_on_one', 'group_session', 'workshop'
    ]))
    duration_minutes = fields.Int(required=True, validate=validate.Range(min=30, max=180))
    notes = fields.Str(required=False, validate=validate.Length(max=500))
    timezone = fields.Str(required=False, load_default='UTC')


class BookingUpdateSchema(Schema):
    session_date = fields.DateTime(required=False)
    duration_minutes = fields.Int(required=False, validate=validate.Range(min=30, max=180))
    notes = fields.Str(required=False, validate=validate.Length(max=500))
    status = fields.Str(required=False, validate=validate.OneOf([
        'pending', 'confirmed', 'cancelled', 'completed'
    ]))


# Mock coach availability data
MOCK_COACH_AVAILABILITY = {
    'coach_001': {  # Sarah Thompson
        'timezone': 'America/New_York',
        'working_hours': {'start': '09:00', 'end': '17:00'},
        'available_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'booked_slots': [
            '2024-01-15T14:00:00Z',
            '2024-01-16T10:00:00Z'
        ]
    },
    'coach_002': {  # Michael Rodriguez
        'timezone': 'America/Los_Angeles',
        'working_hours': {'start': '08:00', 'end': '16:00'},
        'available_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'booked_slots': [
            '2024-01-18T13:00:00Z'
        ]
    },
    'coach_003': {  # Jennifer Park
        'timezone': 'America/Chicago',
        'working_hours': {'start': '09:00', 'end': '17:00'},
        'available_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'booked_slots': []
    }
}


@booking_bp.route('/create', methods=['POST'])
@jwt_required()
@log_access('create_booking', 'booking_data')
def create_booking():
    """Create new session booking"""
    try:
        current_user_id = get_jwt_identity()

        # Validate request data
        schema = BookingCreateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400

        coach_id = data['coach_id']
        session_date = data['session_date']
        session_type = data['session_type']
        duration_minutes = data['duration_minutes']
        notes = data.get('notes', '')
        timezone = data.get('timezone', 'UTC')

        # Check if coach exists and is available
        if coach_id not in MOCK_COACH_AVAILABILITY:
            return jsonify({
                'error': 'Coach not found'
            }), 404

        # Check availability
        if not is_slot_available(coach_id, session_date, duration_minutes):
            return jsonify({
                'error': 'Time slot not available',
                'message': 'The selected time slot is already booked or outside working hours'
            }), 409

        # Calculate pricing
        pricing = calculate_session_pricing(coach_id, session_type, duration_minutes)

        # Create booking
        booking_id = str(uuid.uuid4())
        booking_data = {
            'booking_id': booking_id,
            'user_id': current_user_id,
            'coach_id': coach_id,
            'session_date': session_date.isoformat(),
            'session_type': session_type,
            'duration_minutes': duration_minutes,
            'timezone': timezone,
            'notes': input_sanitizer.sanitize_string(notes) if notes else '',
            'status': 'pending',
            'pricing': pricing,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Save booking (in real implementation, would save to database)
        # For now, we'll just return success
        success = True  # await firebase_service.save_booking(booking_data)

        if success:
            return jsonify({
                'message': 'Booking created successfully',
                'booking_id': booking_id,
                'booking_details': {
                    'coach_id': coach_id,
                    'session_date': session_date.isoformat(),
                    'session_type': session_type,
                    'duration': duration_minutes,
                    'total_price': pricing['total'],
                    'status': 'pending'
                },
                'next_steps': [
                    'Complete payment to confirm booking',
                    'Receive confirmation email with session details',
                    'Add session to your calendar'
                ]
            }), 201
        else:
            return jsonify({
                'error': 'Failed to create booking'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Failed to create booking: {e}")
        return jsonify({
            'error': 'Failed to create booking',
            'message': 'Unable to process booking request'
        }), 500


@booking_bp.route('/sessions', methods=['GET'])
@jwt_required()
@log_access('get_user_sessions', 'booking_data')
def get_user_sessions():
    """Get user session bookings"""
    try:
        current_user_id = get_jwt_identity()

        # Get query parameters
        status = request.args.get('status')  # pending, confirmed, completed, cancelled
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Get user bookings (mock data for now)
        mock_bookings = [
            {
                'booking_id': 'booking_001',
                'coach_id': 'coach_001',
                'coach_name': 'Sarah Thompson',
                'session_date': '2024-01-15T14:00:00Z',
                'session_type': 'one_on_one',
                'duration_minutes': 60,
                'status': 'confirmed',
                'total_price': 350,
                'notes': 'Discussing leadership transition',
                'created_at': '2024-01-10T10:00:00Z'
            },
            {
                'booking_id': 'booking_002',
                'coach_id': 'coach_003',
                'coach_name': 'Jennifer Park',
                'session_date': '2024-01-22T11:00:00Z',
                'session_type': 'discovery',
                'duration_minutes': 30,
                'status': 'pending',
                'total_price': 175,
                'notes': 'Initial consultation',
                'created_at': '2024-01-12T15:30:00Z'
            }
        ]

        # Filter by status if provided
        if status:
            mock_bookings = [b for b in mock_bookings if b['status'] == status]

        # Apply pagination
        total_count = len(mock_bookings)
        paginated_bookings = mock_bookings[offset:offset + limit]

        return jsonify({
            'sessions': paginated_bookings,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get user sessions: {e}")
        return jsonify({
            'error': 'Failed to retrieve sessions',
            'message': 'Unable to load booking data'
        }), 500


@booking_bp.route('/sessions/<booking_id>', methods=['GET'])
@jwt_required()
@log_access('get_booking_details', 'booking_data')
def get_booking_details(booking_id):
    """Get detailed information about a specific booking"""
    try:
        current_user_id = get_jwt_identity()

        # Get booking details (mock data)
        mock_booking = {
            'booking_id': booking_id,
            'user_id': current_user_id,
            'coach_id': 'coach_001',
            'coach_name': 'Sarah Thompson',
            'coach_email': 'sarah.thompson@evergrow360.com',
            'session_date': '2024-01-15T14:00:00Z',
            'session_type': 'one_on_one',
            'duration_minutes': 60,
            'timezone': 'America/New_York',
            'status': 'confirmed',
            'total_price': 350,
            'currency': 'USD',
            'notes': 'Discussing leadership transition',
            'meeting_link': 'https://meet.evergrow360.com/session/abc123',
            'calendar_event_id': 'event_12345',
            'created_at': '2024-01-10T10:00:00Z',
            'updated_at': '2024-01-10T10:00:00Z'
        }

        # Verify ownership (in real implementation)
        if mock_booking['user_id'] != current_user_id:
            return jsonify({
                'error': 'Access denied',
                'message': 'You can only access your own bookings'
            }), 403

        return jsonify(mock_booking), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get booking details: {e}")
        return jsonify({
            'error': 'Failed to retrieve booking details',
            'message': 'Unable to load booking information'
        }), 500


@booking_bp.route('/sessions/<booking_id>', methods=['PUT'])
@jwt_required()
@log_access('update_booking', 'booking_data')
def update_booking(booking_id):
    """Update an existing booking"""
    try:
        current_user_id = get_jwt_identity()

        # Validate request data
        schema = BookingUpdateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400

        # Check if booking exists and belongs to user (mock check)
        mock_booking = {
            'booking_id': booking_id,
            'user_id': current_user_id,
            'status': 'confirmed'
        }

        if mock_booking['user_id'] != current_user_id:
            return jsonify({
                'error': 'Access denied'
            }), 403

        # Check if booking can be modified (not too close to session time)
        session_date = datetime.fromisoformat('2024-01-15T14:00:00Z'.replace('Z', '+00:00'))
        now = datetime.utcnow()
        hours_until_session = (session_date - now).total_seconds() / 3600

        if hours_until_session < 24 and 'session_date' in data:
            return jsonify({
                'error': 'Cannot modify booking',
                'message': 'Bookings cannot be rescheduled less than 24 hours before the session'
            }), 400

        # Update booking (mock update)
        updated_data = data.copy()
        updated_data['updated_at'] = datetime.utcnow().isoformat()

        return jsonify({
            'message': 'Booking updated successfully',
            'booking_id': booking_id,
            'updated_fields': list(data.keys())
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to update booking: {e}")
        return jsonify({
            'error': 'Failed to update booking',
            'message': 'Unable to modify booking'
        }), 500


@booking_bp.route('/sessions/<booking_id>/cancel', methods=['POST'])
@jwt_required()
@log_access('cancel_booking', 'booking_data')
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        current_user_id = get_jwt_identity()

        # Check if booking exists and belongs to user (mock check)
        mock_booking = {
            'booking_id': booking_id,
            'user_id': current_user_id,
            'status': 'confirmed',
            'session_date': '2024-01-15T14:00:00Z'
        }

        if mock_booking['user_id'] != current_user_id:
            return jsonify({
                'error': 'Access denied'
            }), 403

        # Check cancellation policy
        session_date = datetime.fromisoformat(mock_booking['session_date'].replace('Z', '+00:00'))
        now = datetime.utcnow()
        hours_until_session = (session_date - now).total_seconds() / 3600

        if hours_until_session < 12:
            return jsonify({
                'error': 'Cannot cancel booking',
                'message': 'Bookings cannot be cancelled less than 12 hours before the session'
            }), 400

        # Calculate refund amount
        refund_amount = calculate_refund_amount(mock_booking['total_price'], hours_until_session)

        # Cancel booking (mock cancellation)
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking_id': booking_id,
            'refund_amount': refund_amount,
            'cancellation_policy': 'Full refund if cancelled more than 48 hours before session'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to cancel booking: {e}")
        return jsonify({
            'error': 'Failed to cancel booking',
            'message': 'Unable to process cancellation'
        }), 500


@booking_bp.route('/availability/<coach_id>', methods=['GET'])
def get_coach_availability(coach_id):
    """Get coach availability for booking"""
    try:
        # Check if coach exists
        if coach_id not in MOCK_COACH_AVAILABILITY:
            return jsonify({
                'error': 'Coach not found'
            }), 404

        coach_availability = MOCK_COACH_AVAILABILITY[coach_id]

        # Get date range from query params
        start_date = request.args.get('start_date', datetime.utcnow().date().isoformat())
        days_ahead = request.args.get('days_ahead', 30, type=int)

        # Generate available time slots
        available_slots = generate_available_slots(coach_id, start_date, days_ahead)

        return jsonify({
            'coach_id': coach_id,
            'timezone': coach_availability['timezone'],
            'working_hours': coach_availability['working_hours'],
            'available_days': coach_availability['working_days'],
            'available_slots': available_slots,
            'booked_slots': coach_availability['booked_slots']
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get coach availability: {e}")
        return jsonify({
            'error': 'Failed to get availability',
            'message': 'Unable to load coach schedule'
        }), 500


def is_slot_available(coach_id, session_date, duration_minutes):
    """Check if a time slot is available for booking"""
    coach_availability = MOCK_COACH_AVAILABILITY.get(coach_id)
    if not coach_availability:
        return False

    # Check if slot is already booked
    slot_time = session_date.isoformat()
    if slot_time in coach_availability['booked_slots']:
        return False

    # Check if within working hours (simplified check)
    # In real implementation, would convert timezones and check business hours

    return True


def calculate_session_pricing(coach_id, session_type, duration_minutes):
    """Calculate pricing for a session"""
    # Mock pricing - in real implementation would get from database
    base_rates = {
        'coach_001': 350,  # Sarah Thompson
        'coach_002': 275,  # Michael Rodriguez
        'coach_003': 300   # Jennifer Park
    }

    base_rate = base_rates.get(coach_id, 300)
    duration_hours = duration_minutes / 60

    # Apply session type multiplier
    type_multipliers = {
        'discovery': 0.5,  # Half price for discovery sessions
        'one_on_one': 1.0,
        'group_session': 0.7,  # 30% discount for group sessions
        'workshop': 0.8
    }

    multiplier = type_multipliers.get(session_type, 1.0)
    subtotal = base_rate * duration_hours * multiplier

    # Add platform fee (10%)
    platform_fee = subtotal * 0.1
    total = subtotal + platform_fee

    return {
        'base_rate': base_rate,
        'duration_hours': duration_hours,
        'type_multiplier': multiplier,
        'subtotal': round(subtotal, 2),
        'platform_fee': round(platform_fee, 2),
        'total': round(total, 2),
        'currency': 'USD'
    }


def calculate_refund_amount(total_price, hours_until_session):
    """Calculate refund amount based on cancellation policy"""
    if hours_until_session >= 48:  # More than 48 hours
        return total_price  # Full refund
    elif hours_until_session >= 24:  # 24-48 hours
        return total_price * 0.5  # 50% refund
    else:
        return 0  # No refund


def generate_available_slots(coach_id, start_date, days_ahead):
    """Generate available time slots for a coach"""
    coach_availability = MOCK_COACH_AVAILABILITY.get(coach_id, {})
    available_slots = []

    start = datetime.fromisoformat(start_date)
    working_hours = coach_availability.get('working_hours', {'start': '09:00', 'end': '17:00'})

    for day_offset in range(days_ahead):
        current_date = start + timedelta(days=day_offset)
        day_name = current_date.strftime('%A').lower()

        # Check if coach works on this day
        if day_name not in coach_availability.get('available_days', []):
            continue

        # Generate hourly slots during working hours
        start_hour = int(working_hours['start'].split(':')[0])
        end_hour = int(working_hours['end'].split(':')[0])

        for hour in range(start_hour, end_hour):
            slot_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_iso = slot_time.isoformat() + 'Z'

            # Check if slot is not booked
            if slot_iso not in coach_availability.get('booked_slots', []):
                available_slots.append(slot_iso)

    return available_slots