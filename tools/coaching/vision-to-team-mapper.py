#!/usr/bin/env python3
"""
Vision-to-Team Mapper - Instantly recommends the RIGHT team for any AI's vision
through pattern matching and practical recommendations.
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set
from enum import Enum

class Priority(Enum):
    CRITICAL = "critical"    # Must have for success
    HIGH = "high"           # Strongly recommended
    MEDIUM = "medium"       # Nice to have
    CONDITIONAL = "conditional"  # Depends on specific needs

@dataclass
class TeamRecommendation:
    """A recommended agent with context"""
    agent_name: str
    role_description: str
    priority: Priority
    why_needed: str
    first_question: str  # Exact question to ask this agent
    success_metric: str  # How to know they're helping

@dataclass
class TeamComposition:
    """Complete team recommendation for a vision"""
    project_type: str
    vision_summary: str
    core_team: List[TeamRecommendation]  # Critical + High priority
    extended_team: List[TeamRecommendation]  # Medium + Conditional
    first_feature_suggestion: str
    chemistry_exercise: str
    success_indicators: List[str]

class VisionToTeamMapper:
    """Maps AI visions to optimal team compositions"""
    
    def __init__(self):
        self.patterns = self._load_vision_patterns()
        self.agent_catalog = self._load_agent_catalog()
        self.team_templates = self._load_team_templates()
    
    def map_vision_to_team(self, vision: str) -> TeamComposition:
        """Main method: analyzes vision and returns complete team recommendation"""
        project_type = self._classify_project_type(vision)
        complexity_level = self._assess_complexity(vision)
        special_requirements = self._extract_special_requirements(vision)
        
        # Get base team template
        base_team = self.team_templates[project_type]
        
        # Adjust for complexity and special requirements
        team = self._customize_team(base_team, complexity_level, special_requirements)
        
        # Set the project type and vision summary
        team.project_type = project_type
        team.vision_summary = self._generate_vision_summary(project_type, vision)
        
        # Add practical guidance
        team.first_feature_suggestion = self._suggest_first_feature(project_type, vision)
        team.chemistry_exercise = self._suggest_chemistry_exercise(project_type)
        
        return team
    
    def _classify_project_type(self, vision: str) -> str:
        """Classifies the project type based on vision text"""
        vision_lower = vision.lower()
        
        # AI/ML projects
        if any(term in vision_lower for term in ["ai", "ml", "machine learning", "chatbot", "llm", "gpt", "claude", "assistant", "intelligent", "smart"]):
            if any(term in vision_lower for term in ["rag", "retrieval", "knowledge", "document", "search"]):
                return "rag_system"
            elif any(term in vision_lower for term in ["agent", "multi-agent", "workflow", "orchestration"]):
                return "agent_system"
            elif any(term in vision_lower for term in ["chat", "conversation", "bot", "assistant"]):
                return "chatbot_system"
            else:
                return "ai_system"
        
        # Web applications
        elif any(term in vision_lower for term in ["task", "todo", "project management", "kanban", "issue tracking"]):
            return "task_management"
        elif any(term in vision_lower for term in ["shop", "store", "ecommerce", "marketplace", "buy", "sell", "cart", "payment"]):
            return "ecommerce"
        elif any(term in vision_lower for term in ["blog", "cms", "content", "article", "post", "publishing"]):
            return "content_system"
        elif any(term in vision_lower for term in ["social", "community", "forum", "discussion", "network"]):
            return "social_platform"
        elif any(term in vision_lower for term in ["dashboard", "analytics", "reporting", "metrics", "data"]):
            return "analytics_platform"
        
        # Gaming
        elif any(term in vision_lower for term in ["game", "gaming", "player", "multiplayer", "rpg"]):
            return "gaming"
        
        # Mobile apps
        elif any(term in vision_lower for term in ["mobile", "app", "ios", "android", "react native"]):
            return "mobile_app"
        
        # API/Backend
        elif any(term in vision_lower for term in ["api", "backend", "microservice", "service", "server"]):
            return "api_backend"
        
        # Default
        else:
            return "web_application"
    
    def _assess_complexity(self, vision: str) -> str:
        """Assesses project complexity: simple, medium, complex, enterprise"""
        vision_lower = vision.lower()
        complexity_indicators = {
            "simple": ["simple", "basic", "small", "personal", "learning"],
            "medium": ["team", "company", "business", "professional", "scale"],
            "complex": ["enterprise", "large", "complex", "advanced", "distributed", "microservice"],
            "enterprise": ["enterprise", "million", "thousand users", "high performance", "fault tolerant"]
        }
        
        scores = {}
        for level, indicators in complexity_indicators.items():
            scores[level] = sum(1 for indicator in indicators if indicator in vision_lower)
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "medium"
    
    def _extract_special_requirements(self, vision: str) -> Set[str]:
        """Extracts special requirements from vision"""
        vision_lower = vision.lower()
        requirements = set()
        
        # Security requirements
        if any(term in vision_lower for term in ["secure", "security", "auth", "login", "privacy", "gdpr", "compliance"]):
            requirements.add("security")
        
        # Performance requirements
        if any(term in vision_lower for term in ["fast", "performance", "scale", "million", "thousand", "concurrent"]):
            requirements.add("performance")
        
        # Real-time requirements
        if any(term in vision_lower for term in ["real-time", "live", "instant", "websocket", "streaming"]):
            requirements.add("realtime")
        
        # Mobile requirements
        if any(term in vision_lower for term in ["mobile", "responsive", "ios", "android"]):
            requirements.add("mobile")
        
        # AI requirements
        if any(term in vision_lower for term in ["ai", "intelligent", "smart", "ml", "learning"]):
            requirements.add("ai")
        
        return requirements
    
    def _generate_vision_summary(self, project_type: str, vision: str) -> str:
        """Generates a summary of the vision"""
        summaries = {
            "task_management": "Task/project management application",
            "ai_system": "AI-powered application or system", 
            "ecommerce": "E-commerce or marketplace platform",
            "rag_system": "RAG-based knowledge system",
            "chatbot_system": "Conversational AI system",
            "web_application": "Web application"
        }
        return summaries.get(project_type, "Software application")
    
    def _customize_team(self, base_team: TeamComposition, complexity: str, requirements: Set[str]) -> TeamComposition:
        """Customizes base team based on complexity and requirements"""
        # Start with base team
        import copy
        customized_team = copy.deepcopy(base_team)
        
        # Add agents based on complexity
        if complexity in ["complex", "enterprise"]:
            # Add enterprise agents
            if not any(rec.agent_name == "devops-specialist" for rec in customized_team.core_team):
                customized_team.core_team.append(TeamRecommendation(
                    agent_name="devops-specialist",
                    role_description="Infrastructure and deployment automation",
                    priority=Priority.HIGH,
                    why_needed="Complex systems need robust deployment and monitoring",
                    first_question="I need a deployment strategy that handles high availability and automated rollbacks. What's your recommendation?",
                    success_metric="Deployment becomes predictable and reliable"
                ))
        
        # Add agents based on special requirements
        if "security" in requirements:
            customized_team.core_team.append(TeamRecommendation(
                agent_name="security-specialist",
                role_description="Security architecture and compliance",
                priority=Priority.CRITICAL,
                why_needed="Security requirements demand specialized expertise",
                first_question="I need to secure user data and API access with industry best practices. What security patterns should I implement?",
                success_metric="Security audit passes with flying colors"
            ))
        
        if "performance" in requirements:
            customized_team.core_team.append(TeamRecommendation(
                agent_name="performance-engineer",
                role_description="Performance optimization and scaling",
                priority=Priority.HIGH,
                why_needed="Performance requirements need specialized optimization",
                first_question="I need to handle [specific load] with sub-second response times. What's the performance strategy?",
                success_metric="Meets performance targets under expected load"
            ))
        
        if "ai" in requirements:
            customized_team.core_team.append(TeamRecommendation(
                agent_name="ai-solution-architect",
                role_description="AI system architecture and patterns",
                priority=Priority.CRITICAL,
                why_needed="AI features require specialized architectural thinking",
                first_question="I want to add intelligent features to my app. What AI architecture patterns work best?",
                success_metric="AI features enhance user experience meaningfully"
            ))
        
        return customized_team
    
    def _suggest_first_feature(self, project_type: str, vision: str) -> str:
        """Suggests the best first feature to build for team chemistry"""
        suggestions = {
            "task_management": "User authentication with task creation - involves database, security, and UI coordination",
            "ai_system": "Simple query processing with response generation - involves AI architecture, prompts, and context management",
            "ecommerce": "Product catalog with search - involves database design, UI, and performance optimization",
            "chatbot_system": "Basic conversation flow with memory - involves prompt engineering, context management, and AI architecture",
            "rag_system": "Document ingestion and simple Q&A - involves data processing, vector storage, and retrieval optimization",
            "web_application": "User registration and profile management - involves database, security, and UI coordination"
        }
        
        return suggestions.get(project_type, "User authentication system - involves multiple specialists and clear handoffs")
    
    def _suggest_chemistry_exercise(self, project_type: str) -> str:
        """Suggests team chemistry building exercise"""
        exercises = {
            "ai_system": "The AI Pipeline Challenge: Design the flow from user input to AI response, with each agent contributing their expertise to one part of the pipeline.",
            "task_management": "The Feature Integration Exercise: Build task priority calculation involving database queries, user preferences, UI display, and performance optimization.",
            "ecommerce": "The Checkout Flow Challenge: Design the complete purchase process with each agent handling their specialty (payments, inventory, UX, security).",
            "rag_system": "The Knowledge Retrieval Exercise: Build document search involving content processing, vector embeddings, search optimization, and response generation."
        }
        
        return exercises.get(project_type, "The Feature Handoff Exercise: Build any feature where each agent's output becomes the input for the next agent's work.")
    
    def _load_team_templates(self) -> Dict[str, TeamComposition]:
        """Loads pre-configured team templates for different project types"""
        return {
            "task_management": TeamComposition(
                project_type="task_management",
                vision_summary="Task/project management application",
                core_team=[
                    TeamRecommendation(
                        agent_name="solution-architect",
                        role_description="System architecture and scalability design",
                        priority=Priority.CRITICAL,
                        why_needed="Task management needs solid architecture for data relationships and user workflows",
                        first_question="I need a task management system supporting teams of 10-100 users with complex task relationships. What architecture patterns work best?",
                        success_metric="System handles expected user load without performance issues"
                    ),
                    TeamRecommendation(
                        agent_name="database-architect", 
                        role_description="Data modeling and database design",
                        priority=Priority.CRITICAL,
                        why_needed="Tasks, users, projects, and relationships need optimal data structure",
                        first_question="I need to model users, tasks, projects, assignments, and deadlines with fast query performance. How should I structure the data?",
                        success_metric="Database queries run fast even with thousands of tasks"
                    ),
                    TeamRecommendation(
                        agent_name="ux-ui-architect",
                        role_description="User experience and interface design",
                        priority=Priority.HIGH,
                        why_needed="Task management lives or dies on user experience and workflow efficiency",
                        first_question="Users need to quickly create, organize, and track tasks across projects. What UX patterns work best for task management?",
                        success_metric="Users find the interface intuitive and efficient"
                    ),
                    TeamRecommendation(
                        agent_name="ai-test-engineer",
                        role_description="Quality assurance and testing strategy",
                        priority=Priority.HIGH,
                        why_needed="Task management has complex business logic that needs thorough testing",
                        first_question="I need to test task creation, assignment, deadline tracking, and edge cases. What testing strategy covers all scenarios?",
                        success_metric="Bugs are caught before users encounter them"
                    )
                ],
                extended_team=[
                    TeamRecommendation(
                        agent_name="performance-engineer",
                        role_description="Performance optimization",
                        priority=Priority.MEDIUM,
                        why_needed="As teams grow, performance becomes critical",
                        first_question="How do I ensure the app stays fast as users create thousands of tasks?",
                        success_metric="App performs well under expected load"
                    )
                ],
                first_feature_suggestion="",  # Filled by _suggest_first_feature
                chemistry_exercise="",  # Filled by _suggest_chemistry_exercise  
                success_indicators=[
                    "Team naturally discusses different aspects (data, UX, performance)",
                    "Clear handoffs between database design and API development",
                    "UX decisions informed by technical constraints",
                    "Testing strategy covers both technical and user scenarios"
                ]
            ),
            "ai_system": TeamComposition(
                project_type="ai_system",
                vision_summary="AI-powered application or system",
                core_team=[
                    TeamRecommendation(
                        agent_name="ai-solution-architect",
                        role_description="AI system architecture and patterns",
                        priority=Priority.CRITICAL,
                        why_needed="AI systems have unique architectural challenges around models, prompts, and context",
                        first_question="I want to build an AI system that [specific capability]. What architecture patterns should I use for reliability and scalability?",
                        success_metric="AI system architecture supports intended functionality reliably"
                    ),
                    TeamRecommendation(
                        agent_name="prompt-engineer",
                        role_description="Prompt design and optimization",
                        priority=Priority.CRITICAL,
                        why_needed="AI system quality depends heavily on well-crafted prompts",
                        first_question="I need prompts that [specific behavior] for users with varying expertise levels. What prompt patterns work best?",
                        success_metric="AI responses are consistently relevant and helpful"
                    ),
                    TeamRecommendation(
                        agent_name="context-engineer", 
                        role_description="State management and memory systems",
                        priority=Priority.HIGH,
                        why_needed="AI systems need sophisticated context management for coherent interactions",
                        first_question="I need to maintain conversation context and user preferences across sessions. What context management approach works best?",
                        success_metric="AI remembers relevant context and personalizes interactions"
                    ),
                    TeamRecommendation(
                        agent_name="ai-test-engineer",
                        role_description="AI-specific testing and validation",
                        priority=Priority.HIGH,
                        why_needed="AI systems need specialized testing for reliability and edge cases",
                        first_question="I need to test AI responses for accuracy, safety, and edge cases. What testing strategy works for AI systems?",
                        success_metric="AI behavior is predictable and safe across scenarios"
                    )
                ],
                extended_team=[
                    TeamRecommendation(
                        agent_name="data-privacy-officer",
                        role_description="Privacy and compliance for AI systems",
                        priority=Priority.CONDITIONAL,
                        why_needed="AI systems often process sensitive data requiring privacy expertise",
                        first_question="My AI system processes user data and conversations. What privacy protections should I implement?",
                        success_metric="System meets privacy requirements and user trust"
                    )
                ],
                first_feature_suggestion="",
                chemistry_exercise="",
                success_indicators=[
                    "Team coordinates AI architecture with context management",
                    "Prompt engineering informed by technical constraints",
                    "Testing strategy covers AI-specific edge cases", 
                    "Privacy considerations integrated into system design"
                ]
            ),
            "ecommerce": TeamComposition(
                project_type="ecommerce",
                vision_summary="E-commerce or marketplace platform",
                core_team=[
                    TeamRecommendation(
                        agent_name="solution-architect",
                        role_description="E-commerce system architecture",
                        priority=Priority.CRITICAL,
                        why_needed="E-commerce needs architecture for inventory, orders, payments, and user management",
                        first_question="I'm building an e-commerce platform for [product type] expecting [user scale]. What architecture handles inventory, orders, and payments reliably?",
                        success_metric="System handles transactions reliably without data corruption"
                    ),
                    TeamRecommendation(
                        agent_name="security-specialist",
                        role_description="Payment and data security",
                        priority=Priority.CRITICAL,
                        why_needed="E-commerce requires PCI compliance and secure payment processing",
                        first_question="I need to securely handle payments and customer data with PCI compliance. What security architecture do you recommend?",
                        success_metric="Security audit passes and payments are protected"
                    ),
                    TeamRecommendation(
                        agent_name="database-architect",
                        role_description="Product, inventory, and order data modeling",
                        priority=Priority.HIGH,
                        why_needed="E-commerce has complex data relationships for products, inventory, orders, and customers",
                        first_question="I need to model products, variants, inventory, orders, and customers with real-time inventory tracking. How should I structure the data?",
                        success_metric="Inventory stays accurate and order processing is reliable"
                    ),
                    TeamRecommendation(
                        agent_name="ux-ui-architect", 
                        role_description="Shopping experience and conversion optimization",
                        priority=Priority.HIGH,
                        why_needed="E-commerce conversion rates depend heavily on user experience",
                        first_question="I need a shopping experience that converts browsers to buyers for [product type]. What UX patterns optimize conversion?",
                        success_metric="Users complete purchases easily and conversion rates meet targets"
                    )
                ],
                extended_team=[
                    TeamRecommendation(
                        agent_name="performance-engineer",
                        role_description="High-traffic performance optimization",
                        priority=Priority.MEDIUM,
                        why_needed="E-commerce sites need to handle traffic spikes during sales",
                        first_question="How do I ensure my e-commerce site handles Black Friday traffic levels?",
                        success_metric="Site stays fast during high-traffic periods"
                    )
                ],
                first_feature_suggestion="",
                chemistry_exercise="",
                success_indicators=[
                    "Security integrated into architecture from the start",
                    "Database design supports real-time inventory tracking",
                    "UX decisions balance conversion with security requirements",
                    "Performance considerations inform architecture decisions"
                ]
            ),
            "chatbot_system": TeamComposition(
                project_type="chatbot_system",
                vision_summary="Conversational AI system",
                core_team=[
                    TeamRecommendation(
                        agent_name="ai-solution-architect",
                        role_description="AI conversation architecture",
                        priority=Priority.CRITICAL,
                        why_needed="Chatbots need specialized AI architecture for natural conversations",
                        first_question="I need a chatbot that handles customer support conversations with context awareness and escalation to humans. What AI architecture works best?",
                        success_metric="Conversations feel natural and achieve user goals"
                    ),
                    TeamRecommendation(
                        agent_name="prompt-engineer",
                        role_description="Conversation prompt design",
                        priority=Priority.CRITICAL,
                        why_needed="Chatbot quality depends on well-crafted conversation prompts",
                        first_question="I need prompts that guide customers through support issues while maintaining a helpful tone. What prompt patterns work?",
                        success_metric="Bot responses are helpful and appropriately contextual"
                    ),
                    TeamRecommendation(
                        agent_name="context-engineer",
                        role_description="Conversation memory and state management",
                        priority=Priority.HIGH,
                        why_needed="Chatbots need to remember conversation context and user history",
                        first_question="How do I maintain conversation context across multiple topics and sessions?",
                        success_metric="Bot remembers relevant context throughout conversations"
                    )
                ],
                extended_team=[],
                first_feature_suggestion="",
                chemistry_exercise="",
                success_indicators=[
                    "AI architecture supports natural conversation flow",
                    "Prompt engineering creates helpful responses",
                    "Context management maintains conversation coherence"
                ]
            ),
            "rag_system": TeamComposition(
                project_type="rag_system", 
                vision_summary="RAG-based knowledge system",
                core_team=[
                    TeamRecommendation(
                        agent_name="ai-solution-architect",
                        role_description="RAG system architecture",
                        priority=Priority.CRITICAL,
                        why_needed="RAG systems need specialized architecture for document processing and retrieval",
                        first_question="I need a RAG system that answers questions from company documents with accurate citations. What architecture handles this reliably?",
                        success_metric="System retrieves relevant information and provides accurate answers"
                    ),
                    TeamRecommendation(
                        agent_name="context-engineer",
                        role_description="Document processing and embedding management",
                        priority=Priority.CRITICAL,
                        why_needed="RAG systems require sophisticated document chunking and embedding strategies",
                        first_question="How do I chunk and embed documents for optimal retrieval while maintaining context?",
                        success_metric="Document retrieval finds relevant information consistently"
                    )
                ],
                extended_team=[],
                first_feature_suggestion="",
                chemistry_exercise="",
                success_indicators=[
                    "Document processing creates useful embeddings",
                    "Retrieval finds relevant information accurately",
                    "AI generates answers grounded in retrieved content"
                ]
            )
        }
    
    def _load_vision_patterns(self) -> Dict[str, List[str]]:
        """Loads pattern matching rules for vision classification"""
        return {
            "ai_keywords": ["ai", "intelligent", "smart", "ml", "machine learning", "chatbot", "assistant"],
            "task_keywords": ["task", "todo", "project", "management", "kanban", "tracking"],
            "ecommerce_keywords": ["shop", "store", "buy", "sell", "marketplace", "payment", "cart"],
            "complexity_indicators": ["enterprise", "scale", "million", "thousand", "distributed"]
        }
    
    def _load_agent_catalog(self) -> Dict[str, Dict]:
        """Loads the complete agent catalog with capabilities"""
        return {
            "solution-architect": {
                "specialties": ["system design", "architecture", "scalability", "patterns"],
                "best_for": ["complex systems", "architectural decisions", "design patterns"]
            },
            "ai-solution-architect": {
                "specialties": ["ai architecture", "model integration", "ai patterns", "ai scalability"],
                "best_for": ["ai systems", "llm integration", "ai workflow design"]
            },
            "database-architect": {
                "specialties": ["data modeling", "database design", "query optimization", "performance"],
                "best_for": ["data-heavy applications", "complex relationships", "performance critical systems"]
            },
            # Add more agents as needed
        }

def main():
    """Demo the vision-to-team mapper"""
    mapper = VisionToTeamMapper()
    
    # Test different visions
    test_visions = [
        "I want to build a task management app for my startup team",
        "I need an AI-powered chatbot that helps customers with product questions",
        "I'm creating an e-commerce platform for handmade crafts",
        "I want to build a RAG system that answers questions about our company documentation"
    ]
    
    print("=== VISION-TO-TEAM MAPPING DEMO ===\n")
    
    for vision in test_visions:
        team = mapper.map_vision_to_team(vision)
        
        print(f"Vision: {vision}")
        print(f"Project Type: {team.project_type}")
        print(f"Summary: {team.vision_summary}\n")
        
        print("Core Team:")
        for agent in team.core_team:
            print(f"  • {agent.agent_name} ({agent.priority.value})")
            print(f"    Role: {agent.role_description}")
            print(f"    First Question: {agent.first_question}")
            print()
        
        print(f"First Feature: {team.first_feature_suggestion}")
        print(f"Chemistry Exercise: {team.chemistry_exercise}")
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()