# Evergrow360 Coaching App - Application Screens

This directory contains the application screens and user interface components for the Evergrow360 coaching platform.

## Directory Structure

```
app/
├── auth/                    # Authentication screens
├── onboarding/             # AI-powered onboarding flow
├── dashboard/              # User dashboard screens
├── marketplace/            # Coach and course marketplace
├── booking/                # Session booking system
├── sessions/               # Video call and session management
├── payments/               # Billing and payment screens
├── admin/                  # Admin panel screens
├── profile/                # User profile management
├── feedback/               # Feedback and support screens
├── shared/                 # Shared components and layouts
└── user-journeys/          # User journey documentation
```

## Core Features Implemented

Based on the meta analysis, the following core features are implemented:

### 1. User Registration & Login
- Email/password signup with verification
- Google OAuth integration
- Password reset functionality

### 2. AI-Powered Onboarding
- Dynamic chat survey for needs assessment
- Profile completion status tracking
- Business goals and preferences collection

### 3. User Dashboard
- Welcome messages and progress tracking
- Session management and booking buttons
- Personalized action reminders

### 4. Coach & Course Marketplace
- Browse coaches and services
- View details, pricing, and reviews
- Booking system integration

### 5. Session Booking & Video Integration
- Calendar booking system (Meetn integration)
- Meeting links and session management
- Group and 1:1 session support

### 6. Payments & Billing
- Stripe-powered checkout
- Subscription and pay-per-session options
- Billing history and invoices

### 7. AI-Driven Resources
- Personalized coaching plans
- Session summaries and feedback
- Downloadable resources

### 8. Admin Panel
- User and booking management
- Payment oversight
- Content management

## User Journeys

### A) New User Journey
1. Landing page → Registration
2. AI onboarding assessment
3. Dashboard and first booking
4. Session participation
5. Progress tracking and follow-up

### B) Returning User Journey
1. Login and dashboard check
2. New session booking or content access
3. Progress review and reports
4. Automated email sequences

### C) Admin/Coach Journey
1. Admin panel access
2. User and booking monitoring
3. Feedback review and response
4. Content and service management

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Styling**: Custom CSS with brand colors (#D4AF37 gold, #0A1929 navy)
- **Layout**: Responsive grid system
- **Icons**: Custom icon set
- **Integrations**: Stripe, Meetn, AI tools