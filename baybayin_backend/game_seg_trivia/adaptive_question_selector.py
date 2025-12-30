"""
Adaptive Question Selector - AI-driven question selection
Automatically selects optimal questions based on user skill and content analysis
"""

import logging
import random
from typing import Optional, List, Tuple
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

class AdaptiveQuestionSelector:
    """
    AI-driven question selection system
    NO hardcoded rules - everything based on AI analysis and user performance
    """
    
    @staticmethod
    def select_next_question(user_skill_profile) -> Optional['PDFCodexEntry']:
        """
        AI automatically selects the BEST next question based on:
        1. User's current skill level and learning trajectory
        2. Recent performance patterns and accuracy
        3. Content difficulty and AI analysis
        4. Learning prerequisites and dependencies
        5. Content variety and category distribution
        6. Optimal challenge zone (Zone of Proximal Development)
        
        Args:
            user_skill_profile: UserSkillProfile instance
            
        Returns:
            PDFCodexEntry: Best content for next question, or None if no suitable content
        """
        
        from baybayin_codex_pdf.models import PDFCodexEntry
        from game_seg_trivia.models import TriviaQuestionAnswered
        
        # Get user's optimal difficulty target
        target_difficulty = user_skill_profile.get_recommended_difficulty()
        
        logger.info(f"Selecting question for user {user_skill_profile.user.username}: "
                   f"skill={user_skill_profile.overall_skill:.0f}, "
                   f"target_difficulty={target_difficulty:.2f}")
        
        # Get recently asked content to avoid repetition
        recent_answered = TriviaQuestionAnswered.objects.filter(
            user=user_skill_profile.user
        ).order_by('-answered_at')[:20]
        
        recent_content_ids = [ans.source_fact_id for ans in recent_answered if ans.source_fact_id]
        
        # Get available content with AI analysis
        available_content = PDFCodexEntry.objects.filter(
            ai_difficulty_score__isnull=False  # Must be analyzed by AI
        ).exclude(
            id__in=recent_content_ids  # Avoid recent questions
        )
        
        if not available_content.exists():
            logger.warning("No available content with AI analysis, falling back to any analyzed content")
            # Fallback: use any analyzed content (allow repetition if necessary)
            available_content = PDFCodexEntry.objects.filter(
                ai_difficulty_score__isnull=False
            )
            
            if not available_content.exists():
                logger.error("No AI-analyzed content available at all!")
                return None
        
        # Score and rank content using AI-driven algorithm
        scored_content = []
        
        # Sample content for performance (don't score all if there are thousands)
        sample_size = min(200, available_content.count())
        content_sample = available_content.order_by('?')[:sample_size]
        
        for content in content_sample:
            score = AdaptiveQuestionSelector._calculate_content_score(
                content, 
                user_skill_profile, 
                target_difficulty,
                recent_answered
            )
            
            if score > 0:  # Only consider viable content
                scored_content.append((score, content))
        
        if not scored_content:
            logger.warning("No content scored above 0, selecting random fallback")
            return available_content.first()
        
        # Sort by score (highest first)
        scored_content.sort(key=lambda x: x[0], reverse=True)
        
        # Add some randomness - select from top 10% to maintain variety
        top_count = max(1, len(scored_content) // 10)
        top_candidates = scored_content[:top_count]
        
        # Select randomly from top candidates
        selected_score, selected_content = random.choice(top_candidates)
        
        logger.info(f"Selected content ID {selected_content.id}: "
                   f"score={selected_score:.1f}, "
                   f"difficulty={selected_content.calibrated_difficulty:.2f}, "
                   f"category={selected_content.ai_category}")
        
        return selected_content
    
    @staticmethod
    def _calculate_content_score(
        content: 'PDFCodexEntry', 
        user_profile: 'UserSkillProfile',
        target_difficulty: float,
        recent_answered: List['TriviaQuestionAnswered']
    ) -> float:
        """
        AI-driven scoring algorithm for content selection
        
        Returns:
            float: Content suitability score (higher = better match)
        """
        
        score = 0.0
        
        # 1. DIFFICULTY MATCH (Most Important - 40% of score)
        # Perfect match gets full points, linear decay for distance
        difficulty_difference = abs(content.calibrated_difficulty - target_difficulty)
        difficulty_score = max(0, 100 * (1 - difficulty_difference * 2))  # *2 makes it more selective
        score += difficulty_score * 0.4
        
        # 2. PREREQUISITE READINESS (25% of score)
        prereq_score = AdaptiveQuestionSelector._check_prerequisite_readiness(
            user_profile, 
            content.ai_prerequisites or []
        )
        score += prereq_score * 25
        
        # 3. SUCCESS PROBABILITY OPTIMIZATION (20% of score)
        # Target 60-75% success rate (sweet spot for learning)
        success_probability = user_profile.predict_success_probability(content.calibrated_difficulty)
        
        if 0.6 <= success_probability <= 0.75:
            probability_score = 100  # Perfect range
        elif 0.5 <= success_probability < 0.6 or 0.75 < success_probability <= 0.8:
            probability_score = 75   # Good range
        elif 0.4 <= success_probability < 0.5 or 0.8 < success_probability <= 0.9:
            probability_score = 50   # Acceptable range
        else:
            probability_score = 20   # Too easy or too hard
        
        score += probability_score * 0.2
        
        # 4. CATEGORY DIVERSITY BONUS (10% of score)
        category = content.ai_category
        if category:
            user_category_skill = user_profile.get_category_skill(category)
            
            # Bonus for underexplored categories (encourage breadth)
            if user_category_skill < user_profile.overall_skill - 50:
                score += 30 * 0.1  # Significant bonus for weak categories
            elif user_category_skill < user_profile.overall_skill:
                score += 15 * 0.1  # Small bonus for slightly weak categories
            else:
                score += 5 * 0.1   # Small bonus for maintaining strong categories
        
        # 5. CONTENT FRESHNESS BONUS (5% of score)
        # Prefer content that hasn't been asked much
        if content.times_asked == 0:
            freshness_score = 20  # Never asked before
        elif content.times_asked < 5:
            freshness_score = 15  # Asked few times
        elif content.times_asked < 15:
            freshness_score = 10  # Moderately asked
        else:
            freshness_score = 5   # Frequently asked
        
        score += freshness_score * 0.05
        
        # 6. PERFORMANCE CALIBRATION BONUS (Extra consideration)
        # Boost content that has good performance data for calibration
        if content.times_asked >= 10:
            # Well-calibrated content gets small bonus
            actual_difficulty = content.actual_difficulty
            ai_difficulty = content.ai_difficulty_score or 0.5
            calibration_accuracy = 1 - abs(actual_difficulty - ai_difficulty)
            score += calibration_accuracy * 5  # Small bonus for well-calibrated content
        
        # 7. RECENCY PENALTY
        # Slightly penalize content from same category as recent questions
        recent_list = list(recent_answered)  # Convert QuerySet to list
        recent_categories = [ans.source_fact.ai_category for ans in recent_list[-5:] 
                           if ans.source_fact and ans.source_fact.ai_category]
        
        if content.ai_category in recent_categories:
            recent_count = recent_categories.count(content.ai_category)
            score -= recent_count * 3  # Small penalty for repeated categories
        
        return max(0, score)  # Ensure non-negative score
    
    @staticmethod
    def _check_prerequisite_readiness(
        user_profile: 'UserSkillProfile', 
        prerequisites: List[str]
    ) -> float:
        """
        Check if user has mastered prerequisite concepts
        
        Args:
            user_profile: User's skill profile
            prerequisites: List of prerequisite concept names
            
        Returns:
            float: Readiness score (0-100)
        """
        
        if not prerequisites:
            return 100.0  # No prerequisites needed
        
        readiness_scores = []
        
        for prereq in prerequisites:
            # Check user's skill level in prerequisite category
            prereq_skill = user_profile.get_category_skill(prereq)
            
            # Calculate mastery level (relative to user's overall skill)
            if user_profile.overall_skill > 0:
                mastery_ratio = prereq_skill / user_profile.overall_skill
                
                # Convert to readiness score
                if mastery_ratio >= 1.1:
                    readiness = 100  # Exceeds overall skill
                elif mastery_ratio >= 1.0:
                    readiness = 90   # Matches overall skill
                elif mastery_ratio >= 0.9:
                    readiness = 75   # Slightly below overall skill
                elif mastery_ratio >= 0.8:
                    readiness = 50   # Significantly below
                else:
                    readiness = 25   # Much weaker area
            else:
                readiness = 50  # Default for new users
            
            readiness_scores.append(readiness)
        
        # Return average readiness across all prerequisites
        return sum(readiness_scores) / len(readiness_scores)
    
    @staticmethod
    def generate_feedback_message(
        is_correct: bool, 
        skill_change: float, 
        user_profile: 'UserSkillProfile',
        question_difficulty: float
    ) -> str:
        """
        AI-generated personalized feedback message
        
        Args:
            is_correct: Whether user answered correctly
            skill_change: How much skill changed
            user_profile: User's skill profile
            question_difficulty: Difficulty of the question
            
        Returns:
            str: Personalized feedback message
        """
        
        if is_correct:
            if skill_change > 15:
                return f"🎉 Excellent! That was a challenging question (difficulty: {question_difficulty*100:.0f}%). Your skill jumped significantly (+{skill_change:.1f} points)!"
            elif skill_change > 8:
                return f"✨ Great job! You handled that well and your skill increased (+{skill_change:.1f}). Keep up the momentum!"
            elif skill_change > 3:
                return f"👍 Correct! Nice steady progress (+{skill_change:.1f}). You're building solid understanding."
            else:
                return f"✓ Right answer! You're mastering this difficulty level. Ready for more challenge?"
        else:
            if abs(skill_change) > 15:
                return f"💪 That was quite challenging (difficulty: {question_difficulty*100:.0f}%). Learning from tough questions builds strength! Review the explanation."
            elif abs(skill_change) > 8:
                return f"📚 Not quite right, but you're in your learning zone ({skill_change:.1f}). Study the explanation and try similar questions."
            elif abs(skill_change) > 3:
                return f"🎯 Close attempt! This is within your skill range. Review the concept and you'll get it next time."
            else:
                return f"🔄 Keep practicing! This should be manageable for your current skill level. Focus on the key concepts."
    
    @staticmethod
    def get_learning_insights(user_profile: 'UserSkillProfile') -> dict:
        """
        Generate AI-driven learning insights and recommendations
        
        Args:
            user_profile: User's skill profile
            
        Returns:
            dict: Learning insights and recommendations
        """
        
        insights = {
            'overall_progress': '',
            'strength_areas': [],
            'improvement_areas': [],
            'recommended_focus': '',
            'difficulty_trend': '',
            'learning_pace': ''
        }
        
        # Analyze overall progress
        if user_profile.total_questions < 10:
            insights['overall_progress'] = "Just getting started! Complete more questions to see detailed progress."
        elif user_profile.accuracy >= 0.8:
            insights['overall_progress'] = f"Excellent performance! {user_profile.accuracy*100:.1f}% accuracy shows strong mastery."
        elif user_profile.accuracy >= 0.6:
            insights['overall_progress'] = f"Good progress with {user_profile.accuracy*100:.1f}% accuracy. Building solid foundations."
        else:
            insights['overall_progress'] = f"Learning in progress. {user_profile.accuracy*100:.1f}% accuracy shows room for growth."
        
        # Analyze category strengths and weaknesses
        if user_profile.category_skills:
            sorted_categories = sorted(
                user_profile.category_skills.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Top 2 categories are strengths
            insights['strength_areas'] = [cat for cat, skill in sorted_categories[:2] 
                                        if skill >= user_profile.overall_skill]
            
            # Bottom 2 categories are improvement areas  
            insights['improvement_areas'] = [cat for cat, skill in sorted_categories[-2:] 
                                           if skill < user_profile.overall_skill - 50]
        
        # Recommend focus area
        if insights['improvement_areas']:
            insights['recommended_focus'] = f"Focus on {insights['improvement_areas'][0].replace('_', ' ')} to strengthen weak areas."
        elif user_profile.overall_skill < 1000:
            insights['recommended_focus'] = "Continue with basic character recognition and vowel systems."
        else:
            insights['recommended_focus'] = "Explore advanced topics like historical context and cultural significance."
        
        # Analyze recent performance trend
        if len(user_profile.recent_performance) >= 10:
            recent_10 = user_profile.recent_performance[-10:]
            recent_accuracy = sum(1 for r in recent_10 if r['correct']) / 10
            
            if recent_accuracy >= 0.8:
                insights['difficulty_trend'] = "Ready for more challenging content!"
            elif recent_accuracy >= 0.6:
                insights['difficulty_trend'] = "Maintaining good performance at current difficulty."
            else:
                insights['difficulty_trend'] = "Consider reviewing basics before advancing."
        
        # Learning pace analysis
        if user_profile.learning_rate > 1.2:
            insights['learning_pace'] = "Fast learner! You're progressing quickly through concepts."
        elif user_profile.learning_rate > 0.8:
            insights['learning_pace'] = "Steady learning pace - consistent progress over time."
        else:
            insights['learning_pace'] = "Take your time to master each concept thoroughly."
        
        return insights
