"""
Payment API endpoints for Evergrow360
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
import uuid
from datetime import datetime

from app.utils.security import require_auth, log_access, input_sanitizer

# Create blueprint
payment_bp = Blueprint('payment', __name__)

# Mock Stripe service (in production, would use actual Stripe API)
class MockStripeService:
    def __init__(self):
        self.payment_intents = {}

    def create_payment_intent(self, amount, currency='usd', metadata=None):
        """Mock creating a Stripe payment intent"""
        intent_id = f'pi_mock_{uuid.uuid4().hex[:14]}'
        client_secret = f'pi_mock_secret_{uuid.uuid4().hex[:24]}'

        self.payment_intents[intent_id] = {
            'id': intent_id,
            'amount': amount,
            'currency': currency,
            'status': 'requires_payment_method',
            'client_secret': client_secret,
            'metadata': metadata or {},
            'created': datetime.utcnow().isoformat()
        }

        return {
            'id': intent_id,
            'client_secret': client_secret,
            'amount': amount,
            'currency': currency
        }

    def confirm_payment_intent(self, payment_intent_id, payment_method_id=None):
        """Mock confirming a payment intent"""
        if payment_intent_id not in self.payment_intents:
            raise ValueError('Payment intent not found')

        intent = self.payment_intents[payment_intent_id]
        intent['status'] = 'succeeded'
        intent['confirmed_at'] = datetime.utcnow().isoformat()

        return intent

    def get_payment_intent(self, payment_intent_id):
        """Get payment intent details"""
        return self.payment_intents.get(payment_intent_id)

# Initialize mock Stripe service
stripe_service = MockStripeService()

# Validation schemas
class PaymentIntentSchema(Schema):
    amount = fields.Int(required=True, validate=validate.Range(min=1))
    currency = fields.Str(required=False, load_default='usd', validate=validate.OneOf(['usd', 'eur', 'gbp']))
    booking_id = fields.Str(required=False)
    coach_id = fields.Str(required=False)
    description = fields.Str(required=False, validate=validate.Length(max=1000))


class PaymentConfirmationSchema(Schema):
    payment_intent_id = fields.Str(required=True)
    payment_method_id = fields.Str(required=False)  # Would be required in real Stripe


@payment_bp.route('/create-intent', methods=['POST'])
@jwt_required()
@log_access('create_payment_intent', 'payment_data')
def create_payment_intent():
    """Create Stripe payment intent"""
    try:
        current_user_id = get_jwt_identity()

        # Validate request data
        schema = PaymentIntentSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400

        amount = data['amount']
        currency = data['currency']
        booking_id = data.get('booking_id')
        coach_id = data.get('coach_id')
        description = data.get('description', 'Evergrow360 Coaching Session')

        # Create metadata for tracking
        metadata = {
            'user_id': current_user_id,
            'booking_id': booking_id,
            'coach_id': coach_id,
            'description': description
        }

        # Create payment intent with Stripe
        try:
            payment_intent = stripe_service.create_payment_intent(
                amount=amount,
                currency=currency,
                metadata=metadata
            )

            return jsonify({
                'payment_intent_id': payment_intent['id'],
                'client_secret': payment_intent['client_secret'],
                'amount': payment_intent['amount'],
                'currency': payment_intent['currency'],
                'status': 'requires_payment_method',
                'metadata': metadata
            }), 200

        except Exception as stripe_error:
            current_app.logger.error(f"Stripe payment intent creation failed: {stripe_error}")
            return jsonify({
                'error': 'Payment intent creation failed',
                'message': 'Unable to process payment request'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Failed to create payment intent: {e}")
        return jsonify({
            'error': 'Failed to create payment intent',
            'message': 'Unable to process payment request'
        }), 500


@payment_bp.route('/confirm', methods=['POST'])
@jwt_required()
@log_access('confirm_payment', 'payment_data')
def confirm_payment():
    """Confirm payment"""
    try:
        current_user_id = get_jwt_identity()

        # Validate request data
        schema = PaymentConfirmationSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify({
                'error': 'Validation failed',
                'details': err.messages
            }), 400

        payment_intent_id = data['payment_intent_id']
        payment_method_id = data.get('payment_method_id')

        # Get payment intent details
        payment_intent = stripe_service.get_payment_intent(payment_intent_id)

        if not payment_intent:
            return jsonify({
                'error': 'Payment intent not found'
            }), 404

        # Verify ownership
        if payment_intent['metadata'].get('user_id') != current_user_id:
            return jsonify({
                'error': 'Access denied',
                'message': 'You can only confirm your own payments'
            }), 403

        # Confirm payment with Stripe
        try:
            confirmed_payment = stripe_service.confirm_payment_intent(
                payment_intent_id=payment_intent_id,
                payment_method_id=payment_method_id
            )

            # Update booking status if this was for a booking
            booking_id = payment_intent['metadata'].get('booking_id')
            if booking_id:
                # In real implementation, would update booking status
                pass

            # Create payment record
            payment_record = {
                'payment_id': f'pay_{uuid.uuid4().hex[:14]}',
                'user_id': current_user_id,
                'payment_intent_id': payment_intent_id,
                'amount': confirmed_payment['amount'],
                'currency': confirmed_payment['currency'],
                'status': 'completed',
                'booking_id': booking_id,
                'coach_id': payment_intent['metadata'].get('coach_id'),
                'completed_at': confirmed_payment['confirmed_at'],
                'metadata': payment_intent['metadata']
            }

            return jsonify({
                'message': 'Payment confirmed successfully',
                'payment_id': payment_record['payment_id'],
                'status': 'completed',
                'amount': payment_record['amount'],
                'currency': payment_record['currency'],
                'booking_id': booking_id
            }), 200

        except Exception as stripe_error:
            current_app.logger.error(f"Stripe payment confirmation failed: {stripe_error}")
            return jsonify({
                'error': 'Payment confirmation failed',
                'message': 'Unable to confirm payment'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Failed to confirm payment: {e}")
        return jsonify({
            'error': 'Failed to confirm payment',
            'message': 'Unable to process payment confirmation'
        }), 500


@payment_bp.route('/history', methods=['GET'])
@jwt_required()
@log_access('get_payment_history', 'payment_data')
def get_payment_history():
    """Get user's payment history"""
    try:
        current_user_id = get_jwt_identity()

        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status')  # completed, pending, failed

        # Mock payment history
        mock_payments = [
            {
                'payment_id': 'pay_mock_001',
                'payment_intent_id': 'pi_mock_abc123',
                'amount': 350,
                'currency': 'usd',
                'status': 'completed',
                'booking_id': 'booking_001',
                'coach_id': 'coach_001',
                'coach_name': 'Sarah Thompson',
                'description': '1-on-1 Coaching Session',
                'completed_at': '2024-01-10T14:30:00Z',
                'receipt_url': 'https://dashboard.stripe.com/receipts/mock_receipt_001'
            },
            {
                'payment_id': 'pay_mock_002',
                'payment_intent_id': 'pi_mock_def456',
                'amount': 175,
                'currency': 'usd',
                'status': 'completed',
                'booking_id': 'booking_002',
                'coach_id': 'coach_003',
                'coach_name': 'Jennifer Park',
                'description': 'Discovery Session',
                'completed_at': '2024-01-12T11:15:00Z',
                'receipt_url': 'https://dashboard.stripe.com/receipts/mock_receipt_002'
            }
        ]

        # Filter by status if provided
        if status:
            mock_payments = [p for p in mock_payments if p['status'] == status]

        # Apply pagination
        total_count = len(mock_payments)
        paginated_payments = mock_payments[offset:offset + limit]

        # Calculate totals
        total_spent = sum(p['amount'] for p in mock_payments if p['status'] == 'completed')

        return jsonify({
            'payments': paginated_payments,
            'total_count': total_count,
            'total_spent': total_spent,
            'currency': 'usd',
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get payment history: {e}")
        return jsonify({
            'error': 'Failed to retrieve payment history',
            'message': 'Unable to load payment data'
        }), 500


@payment_bp.route('/methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    """Get user's saved payment methods"""
    try:
        current_user_id = get_jwt_identity()

        # Mock saved payment methods
        mock_payment_methods = [
            {
                'id': 'pm_mock_card_001',
                'type': 'card',
                'card': {
                    'brand': 'visa',
                    'last4': '4242',
                    'exp_month': 12,
                    'exp_year': 2025
                },
                'is_default': True,
                'created': '2024-01-01T00:00:00Z'
            }
        ]

        return jsonify({
            'payment_methods': mock_payment_methods,
            'default_method': next((pm for pm in mock_payment_methods if pm['is_default']), None)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get payment methods: {e}")
        return jsonify({
            'error': 'Failed to retrieve payment methods',
            'message': 'Unable to load payment method data'
        }), 500


@payment_bp.route('/methods', methods=['POST'])
@jwt_required()
@log_access('add_payment_method', 'payment_data')
def add_payment_method():
    """Add a new payment method"""
    try:
        current_user_id = get_jwt_identity()

        data = request.json
        payment_method_id = data.get('payment_method_id')  # From Stripe Elements

        if not payment_method_id:
            return jsonify({
                'error': 'Payment method ID required'
            }), 400

        # Mock adding payment method
        new_payment_method = {
            'id': f'pm_mock_{uuid.uuid4().hex[:14]}',
            'type': 'card',
            'card': {
                'brand': 'visa',
                'last4': '4242',
                'exp_month': 12,
                'exp_year': 2025
            },
            'is_default': False,
            'created': datetime.utcnow().isoformat()
        }

        return jsonify({
            'message': 'Payment method added successfully',
            'payment_method': new_payment_method
        }), 201

    except Exception as e:
        current_app.logger.error(f"Failed to add payment method: {e}")
        return jsonify({
            'error': 'Failed to add payment method',
            'message': 'Unable to save payment method'
        }), 500


@payment_bp.route('/refund/<payment_id>', methods=['POST'])
@jwt_required()
@log_access('request_refund', 'payment_data')
def request_refund(payment_id):
    """Request refund for a payment"""
    try:
        current_user_id = get_jwt_identity()

        data = request.json
        reason = data.get('reason', 'Customer requested refund')
        amount = data.get('amount')  # Optional, defaults to full amount

        # Mock refund request
        mock_refund = {
            'refund_id': f'ref_{uuid.uuid4().hex[:14]}',
            'payment_id': payment_id,
            'amount': amount or 350,  # Mock amount
            'currency': 'usd',
            'status': 'succeeded',
            'reason': reason,
            'processed_at': datetime.utcnow().isoformat()
        }

        return jsonify({
            'message': 'Refund processed successfully',
            'refund': mock_refund
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to process refund: {e}")
        return jsonify({
            'error': 'Failed to process refund',
            'message': 'Unable to process refund request'
        }), 500


@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        # In production, would verify webhook signature
        payload = request.get_json()

        event_type = payload.get('type')
        event_data = payload.get('data', {})

        current_app.logger.info(f"Received Stripe webhook: {event_type}")

        # Handle different webhook events
        if event_type == 'payment_intent.succeeded':
            payment_intent = event_data.get('object', {})
            # Process successful payment
            pass
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event_data.get('object', {})
            # Handle failed payment
            pass

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        current_app.logger.error(f"Webhook processing failed: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500