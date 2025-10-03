"""
OpenAI service for AI-powered coaching features

This module provides secure integration with OpenAI API for:
- Assessment analysis and insights
- Personalized coaching plan generation
- Progress recommendations
- Content personalization
"""

import openai
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import current_app

from app.utils.security import input_sanitizer


class AICoachingService:
    """
    AI-powered coaching service using OpenAI GPT models
    
    Focuses on:
    - Professional development insights
    - Personalized coaching recommendations
    - Goal-oriented action plans
    - Progress tracking suggestions
    """
    
    def __init__(self):
        self._client = None
        self._model = None
        self._max_tokens = None
        self._temperature = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            from flask import current_app
            self._client = openai.OpenAI(
                api_key=current_app.config.get('OPENAI_API_KEY')
            )
            self._model = current_app.config.get('OPENAI_MODEL', 'gpt-4-turbo-preview')
            self._max_tokens = current_app.config.get('OPENAI_MAX_TOKENS', 2000)
            self._temperature = current_app.config.get('OPENAI_TEMPERATURE', 0.7)
        return self._client
    
    async def analyze_assessment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user assessment and generate insights
        
        Args:
            assessment_data: Anonymized assessment responses
            
        Returns:
            AI analysis with coaching insights and recommendations
        """
        try:
            client = self._get_client()
            
            # Prepare assessment data for AI analysis
            sanitized_responses = self._sanitize_assessment_data(assessment_data)
            
            # Create AI prompt for assessment analysis
            prompt = self._create_assessment_analysis_prompt(sanitized_responses)
            
            # Get AI analysis
            response = await self._get_ai_response(prompt, max_tokens=1500)
            
            # Parse and structure the response
            analysis = self._parse_assessment_analysis(response)
            
            # Add metadata
            analysis['analysis_date'] = datetime.utcnow().isoformat()
            analysis['model_used'] = self._model
            analysis['confidence_score'] = self._calculate_confidence_score(sanitized_responses)
            
            return analysis
            
        except Exception as e:
            current_app.logger.error(f"Assessment analysis failed: {e}")
            return self._get_fallback_analysis()
    
    async def generate_coaching_plan(self, 
                                   user_profile: Dict[str, Any], 
                                   assessment_insights: Dict[str, Any],
                                   goals: List[str]) -> Dict[str, Any]:
        """
        Generate personalized coaching plan based on profile and assessment
        
        Args:
            user_profile: Anonymized user profile data
            assessment_insights: Results from assessment analysis
            goals: User's coaching goals
            
        Returns:
            Comprehensive coaching plan with actionable steps
        """
        try:
            # Sanitize input data
            sanitized_profile = self._sanitize_profile_data(user_profile)
            sanitized_goals = [input_sanitizer.sanitize_string(goal) for goal in goals]
            
            # Create coaching plan prompt
            prompt = self._create_coaching_plan_prompt(
                sanitized_profile, 
                assessment_insights, 
                sanitized_goals
            )
            
            # Get AI-generated plan
            response = await self._get_ai_response(prompt, max_tokens=2000)
            
            # Parse and structure the plan
            coaching_plan = self._parse_coaching_plan(response)
            
            # Add plan metadata
            coaching_plan['plan_created'] = datetime.utcnow().isoformat()
            coaching_plan['plan_version'] = '1.0'
            coaching_plan['estimated_duration_weeks'] = self._estimate_plan_duration(coaching_plan)
            
            return coaching_plan
            
        except Exception as e:
            current_app.logger.error(f"Coaching plan generation failed: {e}")
            return self._get_fallback_coaching_plan()
    
    async def generate_progress_recommendations(self, 
                                              user_sessions: List[Dict[str, Any]],
                                              current_goals: List[str]) -> Dict[str, Any]:
        """
        Generate recommendations based on session progress
        
        Args:
            user_sessions: Anonymized session history
            current_goals: Current coaching goals
            
        Returns:
            Personalized progress recommendations
        """
        try:
            # Analyze session patterns
            session_summary = self._summarize_sessions(user_sessions)
            
            # Create progress analysis prompt
            prompt = self._create_progress_analysis_prompt(session_summary, current_goals)
            
            # Get AI recommendations
            response = await self._get_ai_response(prompt, max_tokens=1200)
            
            # Parse recommendations
            recommendations = self._parse_progress_recommendations(response)
            
            # Add recommendation metadata
            recommendations['generated_date'] = datetime.utcnow().isoformat()
            recommendations['based_on_sessions'] = len(user_sessions)
            
            return recommendations
            
        except Exception as e:
            current_app.logger.error(f"Progress recommendations failed: {e}")
            return self._get_fallback_recommendations()
    
    async def generate_session_preparation(self, 
                                         upcoming_session: Dict[str, Any],
                                         user_progress: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate preparation materials for upcoming session
        
        Args:
            upcoming_session: Session details and focus areas
            user_progress: Current progress and challenges
            
        Returns:
            Session preparation materials and discussion points
        """
        try:
            # Create session preparation prompt
            prompt = self._create_session_prep_prompt(upcoming_session, user_progress)
            
            # Get AI-generated preparation materials
            response = await self._get_ai_response(prompt, max_tokens=1000)
            
            # Parse preparation materials
            preparation = self._parse_session_preparation(response)
            
            return preparation
            
        except Exception as e:
            current_app.logger.error(f"Session preparation generation failed: {e}")
            return self._get_fallback_session_prep()
    
    # Private helper methods
    
    def _sanitize_assessment_data(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize assessment data for AI processing"""
        sanitized = {}
        
        # Only include safe, coaching-relevant data
        safe_fields = [
            'professional_role', 'main_challenges', 'skill_priorities',
            'learning_style', 'goal_timeframe', 'commitment_level',
            'feedback_openness_score', 'satisfaction_baseline'
        ]
        
        for field in safe_fields:
            if field in assessment_data:
                value = assessment_data[field]
                if isinstance(value, str):
                    sanitized[field] = input_sanitizer.sanitize_string(value)
                elif isinstance(value, list):
                    sanitized[field] = [input_sanitizer.sanitize_string(str(item)) for item in value]
                else:
                    sanitized[field] = value
        
        return sanitized
    
    def _sanitize_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize profile data for AI processing"""
        return {
            'professional_role': profile_data.get('coaching_preferences', {}).get('professional_role'),
            'industry_sector': profile_data.get('coaching_preferences', {}).get('industry_sector'),
            'experience_level': profile_data.get('coaching_preferences', {}).get('experience_level'),
            'coaching_focus_areas': profile_data.get('coaching_preferences', {}).get('coaching_focus_areas', []),
            'management_level': profile_data.get('business_context', {}).get('management_level'),
            'company_size_range': profile_data.get('business_context', {}).get('company_size_range')
        }
    
    def _create_assessment_analysis_prompt(self, assessment_data: Dict[str, Any]) -> str:
        """Create prompt for assessment analysis"""
        return f"""
As an expert executive coach, analyze this professional assessment and provide insights:

ASSESSMENT DATA:
Role: {assessment_data.get('professional_role', 'Not specified')}
Main Challenges: {assessment_data.get('main_challenges', [])}
Skill Priorities: {assessment_data.get('skill_priorities', [])}
Learning Style: {assessment_data.get('learning_style', 'Not specified')}
Commitment Level: {assessment_data.get('commitment_level', 'Not specified')}/5
Feedback Openness: {assessment_data.get('feedback_openness_score', 'Not specified')}/10
Current Satisfaction: {assessment_data.get('satisfaction_baseline', 'Not specified')}/10

ANALYSIS REQUEST:
Please provide a professional coaching analysis in JSON format with:
1. "strengths": 3-4 identified strengths based on responses
2. "development_areas": 3-4 key areas for development
3. "coaching_readiness": Assessment of readiness for coaching (1-10)
4. "recommended_intensity": Suggested coaching intensity (light/regular/intensive)
5. "success_factors": 3-4 factors that will contribute to coaching success
6. "potential_challenges": 2-3 potential obstacles to address
7. "recommended_focus": Top 3 focus areas for coaching
8. "learning_approach": Recommended learning approach based on style

Respond only with valid JSON.
"""
    
    def _create_coaching_plan_prompt(self, 
                                   profile: Dict[str, Any], 
                                   insights: Dict[str, Any], 
                                   goals: List[str]) -> str:
        """Create prompt for coaching plan generation"""
        return f"""
As an expert executive coach, create a comprehensive coaching plan:

PROFILE:
Role: {profile.get('professional_role')}
Industry: {profile.get('industry_sector')}
Experience: {profile.get('experience_level')}
Management Level: {profile.get('management_level')}
Focus Areas: {profile.get('coaching_focus_areas', [])}

ASSESSMENT INSIGHTS:
Development Areas: {insights.get('development_areas', [])}
Recommended Focus: {insights.get('recommended_focus', [])}
Coaching Readiness: {insights.get('coaching_readiness', 'Unknown')}

GOALS:
{chr(10).join(f'- {goal}' for goal in goals)}

COACHING PLAN REQUEST:
Create a detailed coaching plan in JSON format with:
1. "plan_overview": Brief description of the coaching approach
2. "phases": Array of 3-4 coaching phases, each with:
   - "phase_name": Name of the phase
   - "duration_weeks": Expected duration
   - "objectives": 2-3 learning objectives
   - "key_activities": 3-4 main activities/exercises
   - "success_metrics": How to measure progress
3. "weekly_structure": Recommended weekly activities
4. "milestone_schedule": Key milestones and checkpoints
5. "resources": Recommended books, tools, or exercises
6. "homework_suggestions": Between-session activities
7. "success_indicators": How to measure overall success

Respond only with valid JSON.
"""
    
    def _create_progress_analysis_prompt(self, 
                                       session_summary: Dict[str, Any], 
                                       goals: List[str]) -> str:
        """Create prompt for progress analysis"""
        return f"""
As an expert executive coach, analyze progress and provide recommendations:

SESSION HISTORY SUMMARY:
Total Sessions: {session_summary.get('total_sessions', 0)}
Average Satisfaction: {session_summary.get('avg_satisfaction', 0)}/10
Topics Covered: {session_summary.get('topics_covered', [])}
Skills Practiced: {session_summary.get('skills_practiced', [])}
Completion Rate: {session_summary.get('homework_completion_rate', 0)}%

CURRENT GOALS:
{chr(10).join(f'- {goal}' for goal in goals)}

RECOMMENDATIONS REQUEST:
Provide progress analysis in JSON format with:
1. "progress_assessment": Overall progress evaluation (1-10)
2. "strengths_demonstrated": 3-4 strengths shown in sessions
3. "areas_for_improvement": 2-3 areas needing more focus
4. "goal_progress": Assessment of progress toward each goal
5. "next_steps": 3-4 recommended next actions
6. "session_recommendations": Suggestions for upcoming sessions
7. "skill_focus": Top 2-3 skills to prioritize
8. "motivation_boosters": Ways to maintain motivation

Respond only with valid JSON.
"""
    
    def _create_session_prep_prompt(self, 
                                  session_details: Dict[str, Any], 
                                  progress: Dict[str, Any]) -> str:
        """Create prompt for session preparation"""
        return f"""
As an expert executive coach, prepare materials for an upcoming session:

SESSION DETAILS:
Focus Areas: {session_details.get('focus_areas', [])}
Session Type: {session_details.get('session_type', 'Individual')}
Duration: {session_details.get('duration_minutes', 60)} minutes

CURRENT PROGRESS:
Recent Topics: {progress.get('recent_topics', [])}
Challenges: {progress.get('current_challenges', [])}
Achievements: {progress.get('recent_achievements', [])}

PREPARATION REQUEST:
Create session preparation in JSON format with:
1. "session_objectives": 2-3 clear objectives for the session
2. "discussion_points": 4-5 key discussion topics
3. "exercises": 2-3 coaching exercises or activities
4. "reflection_questions": 3-4 questions for self-reflection
5. "homework_review": Points to review from previous session
6. "resources": Any materials or tools to prepare
7. "outcome_measures": How to measure session success

Respond only with valid JSON.
"""
    
    async def _get_ai_response(self, prompt: str, max_tokens: int = None) -> str:
        """Get response from OpenAI API"""
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert executive coach with 20+ years of experience in leadership development and professional coaching. You provide evidence-based, actionable insights and recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens or self._max_tokens,
                temperature=self._temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            current_app.logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _parse_assessment_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI assessment analysis response"""
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            current_app.logger.error("Failed to parse AI assessment analysis")
            return self._get_fallback_analysis()
    
    def _parse_coaching_plan(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI coaching plan response"""
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            current_app.logger.error("Failed to parse AI coaching plan")
            return self._get_fallback_coaching_plan()
    
    def _parse_progress_recommendations(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI progress recommendations response"""
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            current_app.logger.error("Failed to parse AI progress recommendations")
            return self._get_fallback_recommendations()
    
    def _parse_session_preparation(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI session preparation response"""
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            current_app.logger.error("Failed to parse AI session preparation")
            return self._get_fallback_session_prep()
    
    def _summarize_sessions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize session history for AI analysis"""
        if not sessions:
            return {
                'total_sessions': 0,
                'avg_satisfaction': 0,
                'topics_covered': [],
                'skills_practiced': [],
                'homework_completion_rate': 0
            }
        
        total_sessions = len(sessions)
        total_satisfaction = sum(s.get('satisfaction_score', 0) for s in sessions)
        avg_satisfaction = total_satisfaction / total_sessions if total_sessions > 0 else 0
        
        # Aggregate topics and skills
        all_topics = []
        all_skills = []
        homework_completed = 0
        
        for session in sessions:
            outcomes = session.get('outcomes', {})
            all_topics.extend(outcomes.get('topics_covered', []))
            all_skills.extend(outcomes.get('skills_practiced', []))
            
            if session.get('progress_metrics', {}).get('homework_completion'):
                homework_completed += 1
        
        # Get unique topics and skills
        unique_topics = list(set(all_topics))
        unique_skills = list(set(all_skills))
        
        homework_completion_rate = (homework_completed / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            'total_sessions': total_sessions,
            'avg_satisfaction': round(avg_satisfaction, 1),
            'topics_covered': unique_topics[:10],  # Top 10 topics
            'skills_practiced': unique_skills[:8],  # Top 8 skills
            'homework_completion_rate': round(homework_completion_rate, 1)
        }
    
    def _calculate_confidence_score(self, assessment_data: Dict[str, Any]) -> float:
        """Calculate confidence score for AI analysis"""
        # Simple confidence calculation based on data completeness
        total_fields = 8
        completed_fields = sum(1 for key in [
            'professional_role', 'main_challenges', 'skill_priorities',
            'learning_style', 'commitment_level', 'feedback_openness_score',
            'satisfaction_baseline', 'goal_timeframe'
        ] if assessment_data.get(key))
        
        return round(completed_fields / total_fields, 2)
    
    def _estimate_plan_duration(self, coaching_plan: Dict[str, Any]) -> int:
        """Estimate total duration of coaching plan in weeks"""
        phases = coaching_plan.get('phases', [])
        total_weeks = sum(phase.get('duration_weeks', 4) for phase in phases)
        return max(total_weeks, 8)  # Minimum 8 weeks
    
    # Fallback methods for error cases
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        return {
            'strengths': [
                'Professional commitment to growth',
                'Willingness to seek coaching',
                'Clear recognition of development needs'
            ],
            'development_areas': [
                'Leadership effectiveness',
                'Communication skills',
                'Strategic thinking'
            ],
            'coaching_readiness': 7,
            'recommended_intensity': 'regular',
            'success_factors': [
                'Open to feedback',
                'Committed to change',
                'Clear goals'
            ],
            'potential_challenges': [
                'Time management',
                'Implementation consistency'
            ],
            'recommended_focus': [
                'Goal clarification',
                'Action planning',
                'Progress tracking'
            ],
            'learning_approach': 'Structured with regular practice',
            'fallback': True
        }
    
    def _get_fallback_coaching_plan(self) -> Dict[str, Any]:
        """Fallback coaching plan when AI fails"""
        return {
            'plan_overview': 'Comprehensive leadership development program',
            'phases': [
                {
                    'phase_name': 'Assessment and Goal Setting',
                    'duration_weeks': 2,
                    'objectives': ['Clarify goals', 'Assess current state'],
                    'key_activities': ['360 feedback', 'Goal setting workshop'],
                    'success_metrics': ['Clear goals defined', 'Baseline established']
                },
                {
                    'phase_name': 'Skill Development',
                    'duration_weeks': 6,
                    'objectives': ['Build core skills', 'Practice new behaviors'],
                    'key_activities': ['Skill workshops', 'Role playing', 'Action learning'],
                    'success_metrics': ['Skill improvement', 'Behavior change']
                },
                {
                    'phase_name': 'Integration and Sustainment',
                    'duration_weeks': 4,
                    'objectives': ['Integrate learning', 'Sustain change'],
                    'key_activities': ['Real-world application', 'Peer support'],
                    'success_metrics': ['Sustained behavior', 'Goal achievement']
                }
            ],
            'fallback': True
        }
    
    def _get_fallback_recommendations(self) -> Dict[str, Any]:
        """Fallback recommendations when AI fails"""
        return {
            'progress_assessment': 7,
            'strengths_demonstrated': [
                'Consistent participation',
                'Open to feedback',
                'Takes action on insights'
            ],
            'areas_for_improvement': [
                'Goal focus',
                'Implementation consistency'
            ],
            'next_steps': [
                'Continue regular sessions',
                'Practice new skills',
                'Track progress'
            ],
            'fallback': True
        }
    
    def _get_fallback_session_prep(self) -> Dict[str, Any]:
        """Fallback session preparation when AI fails"""
        return {
            'session_objectives': [
                'Review progress',
                'Address challenges',
                'Plan next steps'
            ],
            'discussion_points': [
                'Recent achievements',
                'Current challenges',
                'Goal progress',
                'Learning insights'
            ],
            'exercises': [
                'Reflection exercise',
                'Action planning'
            ],
            'fallback': True
        }


# Global service instance
ai_coaching_service = AICoachingService()