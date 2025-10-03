# User Journeys - Evergrow360 Coaching App

This document outlines the complete user journeys for the Evergrow360 coaching platform, reflecting the requirements analyzed from the `__meta` folder.

## Journey Overview

The platform supports three primary user journeys:
1. **New User Journey** - Registration to first booking
2. **Returning User Journey** - Follow-up sessions and content access
3. **Admin/Coach Journey** - Back office management

---

## A) New User Journey - Registration to Booking

### 1. Landing Page Visit
**Screen**: Marketing website (existing Jekyll site)
- User sees value proposition and call-to-action
- Clear messaging about AI-powered coaching
- Social proof with testimonials and statistics

### 2. Account Registration
**Screen**: `/app/auth/register.html`
- **Options**: Email/password or Google OAuth
- **Fields**: Full name, email, password, password confirmation
- **Validation**: Real-time form validation with helpful error messages
- **Privacy**: Terms acceptance and marketing opt-in
- **Success**: Email verification sent, welcome modal displayed

### 3. AI-Powered Onboarding
**Screen**: `/app/onboarding/welcome.html` → `/app/onboarding/assessment.html`

#### Welcome Screen
- Personalized greeting using registration data
- Platform feature overview with icons and descriptions
- Trust indicators (10,000+ professionals helped, 95% success rate)
- Clear call-to-action to start assessment

#### AI Assessment
- **8 Comprehensive Questions** covering:
  - Professional role and position
  - Main business challenges
  - Improvement areas (multi-select)
  - Feedback reception style
  - Current satisfaction levels (1-10 scale)
  - Learning preferences
  - 6-month professional goals (open text)
  - Time commitment availability
- **Progress Tracking**: Step 2 of 4 with visual progress bar
- **AI Analysis**: Simulated processing with animated feedback
- **Data Storage**: Responses saved for personalized recommendations

### 4. First Dashboard Visit
**Screen**: `/app/dashboard/index.html`
- **Welcome Message**: "Welcome back, [Name]!" with personalized greeting
- **Progress Overview**: Visual onboarding completion status
- **Quick Actions**: Prominent "Book Session" and "Explore Marketplace" buttons
- **Personalized Stats**: Sessions completed, growth score, active goals
- **AI Recommendations**: Based on assessment responses

### 5. Browse Coaches/Marketplace
**Screen**: `/app/marketplace/index.html`
- **Filtering Options**: By category, price, duration, and session type
- **Search Functionality**: Find coaches, courses, or skills
- **Featured Section**: Highlighted coaches and courses
- **Coach Profiles**: Ratings, specialties, availability, and pricing
- **Course Catalog**: Modules, duration, level, and reviews
- **Workshop Options**: Group sessions with participant requirements

### 6. Session Booking Process
**Screen**: `/app/booking/index.html`

#### Step 1: Session Details
- Selected item summary with coach/course information
- Session type selection (individual vs. group)
- Duration options with dynamic pricing
- Focus areas selection (optional)
- Additional notes field for specific requirements

#### Step 2: Schedule Selection
- **Calendar Interface**: Monthly view with available dates
- **Time Slots**: Available times based on coach availability
- **Booking Summary**: Real-time summary of selections
- **Validation**: Date and time required before proceeding

#### Step 3: Payment Processing
- **Payment Methods**: Credit card, PayPal, or session credits
- **Secure Forms**: Stripe integration for card processing
- **Order Summary**: Itemized breakdown with total cost
- **Security**: PCI-compliant payment processing

#### Step 4: Confirmation
- **Success Message**: Booking confirmed with checkmark animation
- **Session Details**: Complete booking information
- **Next Steps**: Checklist of post-booking actions
- **Quick Actions**: Return to dashboard or view sessions

### 7. Pre-Session Content Access
**Screen**: Dashboard with personalized recommendations
- AI-generated preparation materials based on assessment
- Goal-setting exercises related to session focus
- Resource downloads and reading materials
- Calendar integration reminders

### 8. Session Participation
**Screen**: Video call interface (referenced but not fully implemented)
- Meeting link accessible from dashboard or email
- Join session functionality
- Post-session feedback collection

---

## B) Returning User Journey - Follow-Up Sessions

### 1. User Login
**Screen**: `/app/auth/login.html`
- **Quick Login**: Email/password or Google OAuth
- **Remember Me**: Optional session persistence
- **Password Recovery**: Forgot password flow
- **Demo Credentials**: Testing functionality available

### 2. Dashboard Check
**Screen**: `/app/dashboard/index.html`
- **Recent Activities**: Session completions, goal updates, resource access
- **Upcoming Sessions**: Next scheduled appointments with join buttons
- **Progress Tracking**: Skill development progress bars
- **AI Recommendations**: Personalized next steps based on history

### 3. New Session Booking or Content Access
**Screens**: Marketplace → Booking flow (same as new user)
- **Recommendations**: AI-suggested coaches based on history
- **Credits Usage**: Apply available session credits
- **Recurring Sessions**: Option to book follow-up sessions
- **Content Library**: Access to purchased courses and materials

### 4. Progress Review and Reports
**Screen**: Dashboard progress section
- **Skill Development**: Visual progress indicators
- **Goal Tracking**: Current goals with completion percentages
- **Session History**: Past sessions with coach feedback
- **Downloadable Reports**: Progress summaries and action plans

### 5. Automated Email Sequences
**External Integration**: Email automation system
- **Reminders**: Session reminders 24 hours and 1 hour before
- **Follow-up**: Post-session feedback requests and next steps
- **Tips**: Weekly coaching tips based on focus areas
- **Progress**: Monthly progress reports and goal reviews

---

## C) Admin/Coach Journey - Back Office Management

### 1. Admin Login
**Screen**: Dedicated admin authentication (referenced)
- **Secure Access**: Role-based authentication
- **Admin Portal**: Separate interface from user dashboard
- **Multi-level Access**: Different permissions for admins and coaches

### 2. User and Booking Monitoring
**Screen**: Admin dashboard with management tools
- **User List**: All registered users with activity status
- **Session Management**: Booking calendar and session oversight
- **Payment Tracking**: Revenue analytics and payment status
- **Filter/Search**: Find users by various criteria
- **Export Functionality**: Data export for external analysis

### 3. Feedback Review and Response
**Screen**: Feedback management interface
- **Feedback Inbox**: User-submitted feedback and support requests
- **Response Tools**: Direct communication with users
- **Issue Tracking**: Problem resolution workflow
- **Quality Assurance**: Coach performance monitoring

### 4. Content and Service Management
**Screen**: Content management system
- **Coach Profiles**: Add, edit, and manage coach listings
- **Course Catalog**: Create and update course offerings
- **Resource Library**: Upload and organize downloadable materials
- **Pricing Management**: Adjust session and course pricing

---

## Technical Implementation Notes

### Data Flow
1. **User Registration** → Temporary storage → Onboarding completion → User profile creation
2. **Assessment Responses** → AI analysis simulation → Personalized recommendations
3. **Booking Process** → Session creation → Payment processing → Confirmation emails
4. **Session Management** → Calendar integration → Video call links → Post-session feedback

### Storage Strategy
- **Local Storage**: Session management, onboarding progress, temporary data
- **Persistent Storage**: User profiles, booking history, progress tracking
- **Security**: Secure token-based authentication, payment data protection

### Integration Points
- **Stripe**: Payment processing and subscription management
- **Meetn**: Video call scheduling and management
- **Email System**: Automated sequences and notifications
- **AI Services**: Assessment analysis and recommendation engine

### Responsive Design
- **Mobile-First**: All screens optimized for mobile devices
- **Progressive Enhancement**: Desktop features layer on top of mobile base
- **Touch-Friendly**: Large buttons and touch targets
- **Fast Loading**: Optimized images and minimal JavaScript

---

## User Experience Principles

### Personalization
- **Name Usage**: Personal greetings throughout the platform
- **Recommendation Engine**: AI-driven suggestions based on user data
- **Progress Tracking**: Individual goal setting and achievement monitoring
- **Adaptive Interface**: Content and options based on user preferences

### Trust Building
- **Social Proof**: Statistics, testimonials, and success stories
- **Transparency**: Clear pricing, policies, and process explanations
- **Security**: Visible security measures and privacy protections
- **Professional Design**: Consistent branding and high-quality visuals

### Conversion Optimization
- **Clear CTAs**: Prominent action buttons at each step
- **Progress Indicators**: Visual feedback on process completion
- **Reduced Friction**: Minimal form fields and easy navigation
- **Multiple Paths**: Various ways to achieve the same goals

### Accessibility
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **Color Contrast**: WCAG-compliant color combinations
- **Font Sizing**: Readable text sizes and clear typography