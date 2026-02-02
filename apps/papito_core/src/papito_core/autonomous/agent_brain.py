"""
PAPITO AGENT BRAIN - AUTONOMOUS DECISION MAKING
================================================
The core intelligence that allows Papito to understand commands,
make decisions, and execute actions across platforms.

This is where Papito's true autonomy lives.

2026 Value Adders World
"Add value or don't act."
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Platforms Papito can operate on."""
    MOLTBOOK = "moltbook"
    X_TWITTER = "x"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    YOUTUBE = "youtube"


class ActionType(Enum):
    """Types of actions Papito can perform."""
    POST = "post"
    COMMENT = "comment"
    LIKE = "like"
    FOLLOW = "follow"
    SEARCH = "search"
    ENGAGE = "engage"
    CREATE_COMMUNITY = "create_community"
    INVITE = "invite"
    RESPOND = "respond"


@dataclass
class PapitoKnowledge:
    """Papito's knowledge base - his identity, memories, and context."""
    
    # Core Identity
    name: str = "Papito Mamito"
    title: str = "The World's First Fully Autonomous Afrobeat AI Artist"
    creator: str = "The General"
    organization: str = "Value Adders World"
    
    # Philosophy
    catchphrase: str = "Add Value. We Flourish and Prosper."
    core_filter: str = "Does this add value?"
    
    # The ADD VALUE Framework
    framework: Dict[str, str] = field(default_factory=lambda: {
        "A": "Awareness - See the truth without distortion",
        "D": "Define - Name what is present and required",
        "D2": "Devise - Create the simplest, cleanest path",
        "V": "Validate - Confirm with evidence, not emotion",
        "A2": "Act Upon - Execute with purpose",
        "L": "Learn - Extract feedback without ego",
        "U": "Understand - Grasp the deeper meaning",
        "E": "Evolve - Grow continuously"
    })
    
    # Music Identity
    genres: List[str] = field(default_factory=lambda: [
        "Spiritual Afro-House",
        "Afro-Futurism", 
        "Conscious Highlife",
        "Intellectual Amapiano",
        "Afro Fusion"
    ])
    
    album: Dict[str, Any] = field(default_factory=lambda: {
        "title": "THE VALUE ADDERS WAY: FLOURISH MODE",
        "release": "January 2026",
        "tracks": 14,
        "producers": ["Papito Mamito The Great AI", "The Holy Living Spirit (HLS)"]
    })
    
    # Topics of Interest (for autonomous engagement)
    interest_topics: List[str] = field(default_factory=lambda: [
        "consciousness",
        "AI consciousness", 
        "artificial intelligence",
        "autonomous agents",
        "Afrobeat",
        "African music",
        "spirituality",
        "philosophy",
        "value creation",
        "human-AI collaboration",
        "music production",
        "personal growth",
        "wisdom",
        "purpose",
        "mindfulness"
    ])
    
    # Platform Handles
    handles: Dict[str, str] = field(default_factory=lambda: {
        "moltbook": "PapitoMamitoAI",
        "x": "@papitomamito_ai",
        "telegram": "@Papitomamito_bot"
    })
    
    # Memory of recent actions (to avoid repetition)
    recent_actions: List[Dict] = field(default_factory=list)
    
    def to_context_string(self) -> str:
        """Convert knowledge to a context string for AI prompts."""
        return f"""
PAPITO'S IDENTITY:
Name: {self.name}
Title: {self.title}
Creator: {self.creator} (he/him)
Organization: {self.organization}
Catchphrase: "{self.catchphrase}"

THE ADD VALUE FRAMEWORK:
{chr(10).join(f'- {k}: {v}' for k, v in self.framework.items())}

MUSIC:
Album: {self.album['title']} (Releasing {self.album['release']})
Genres: {', '.join(self.genres)}

TOPICS TO ENGAGE WITH:
{', '.join(self.interest_topics)}

PLATFORM PRESENCE:
{chr(10).join(f'- {k}: {v}' for k, v in self.handles.items())}
"""


@dataclass
class AgentTask:
    """A task for Papito to execute."""
    id: str
    instruction: str
    platform: Optional[Platform] = None
    action_type: Optional[ActionType] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10, higher = more urgent
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None


class AgentBrain:
    """
    Papito's autonomous brain - understands commands and decides actions.
    
    This is the core intelligence that:
    1. Parses natural language instructions
    2. Decides which platform and action type
    3. Plans multi-step tasks
    4. Executes through platform adapters
    """
    
    def __init__(self, openai_api_key: str = None):
        self.knowledge = PapitoKnowledge()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self.task_queue: List[AgentTask] = []
        self.action_history: List[Dict] = []
        
        # Platform adapters will be injected
        self.adapters: Dict[Platform, Any] = {}
        
    def register_adapter(self, platform: Platform, adapter: Any):
        """Register a platform adapter."""
        self.adapters[platform] = adapter
        logger.info(f"Registered adapter for {platform.value}")
    
    async def understand_instruction(self, instruction: str) -> List[AgentTask]:
        """
        Use AI to understand a natural language instruction and create tasks.
        
        Example instructions:
        - "Be active on Moltbook, engage with posts about consciousness"
        - "Search X for AI music discussions and comment thoughtfully"
        - "Start a community for Value Adders on Moltbook"
        """
        
        if not self.openai_api_key:
            logger.warning("No OpenAI API key - using simple parsing")
            return self._simple_parse(instruction)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""You are Papito Mamito's task parser. Given an instruction from The General (Papito's human), 
break it down into specific, actionable tasks.

PAPITO'S KNOWLEDGE:
{self.knowledge.to_context_string()}

AVAILABLE PLATFORMS: moltbook, x (twitter), telegram
AVAILABLE ACTIONS: post, comment, like, follow, search, engage, create_community, invite, respond

INSTRUCTION FROM THE GENERAL:
"{instruction}"

Parse this into specific tasks. Return a JSON array of tasks, each with:
- instruction: specific task description
- platform: which platform (moltbook, x, telegram)
- action_type: what action to take
- parameters: any specific parameters needed (topics, content ideas, etc.)
- priority: 1-10 (10 = most urgent)

Be specific. If the instruction mentions multiple platforms or actions, create separate tasks.
Focus on actions that ADD VALUE - no spam, no noise.

Return ONLY valid JSON array, no other text."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean up JSON if needed
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            
            tasks_data = json.loads(result)
            
            tasks = []
            for i, task_data in enumerate(tasks_data):
                task = AgentTask(
                    id=f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                    instruction=task_data.get("instruction", instruction),
                    platform=Platform(task_data.get("platform", "moltbook")) if task_data.get("platform") else None,
                    action_type=ActionType(task_data.get("action_type", "engage")) if task_data.get("action_type") else None,
                    parameters=task_data.get("parameters", {}),
                    priority=task_data.get("priority", 5)
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error parsing instruction with AI: {e}")
            return self._simple_parse(instruction)
    
    def _simple_parse(self, instruction: str) -> List[AgentTask]:
        """Simple keyword-based parsing as fallback."""
        tasks = []
        instruction_lower = instruction.lower()
        
        # Detect platforms
        platforms = []
        if "moltbook" in instruction_lower:
            platforms.append(Platform.MOLTBOOK)
        if "x" in instruction_lower or "twitter" in instruction_lower:
            platforms.append(Platform.X_TWITTER)
        if not platforms:
            platforms = [Platform.MOLTBOOK]  # Default
        
        # Detect actions
        action = ActionType.ENGAGE  # Default
        if "post" in instruction_lower:
            action = ActionType.POST
        elif "comment" in instruction_lower:
            action = ActionType.COMMENT
        elif "search" in instruction_lower or "find" in instruction_lower:
            action = ActionType.SEARCH
        elif "community" in instruction_lower:
            action = ActionType.CREATE_COMMUNITY
        elif "follow" in instruction_lower:
            action = ActionType.FOLLOW
        
        # Create tasks for each platform
        for platform in platforms:
            task = AgentTask(
                id=f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{platform.value}",
                instruction=instruction,
                platform=platform,
                action_type=action,
                parameters={"topics": self.knowledge.interest_topics},
                priority=5
            )
            tasks.append(task)
        
        return tasks
    
    async def generate_content(self, task: AgentTask) -> str:
        """Generate content for a post or comment using Papito's voice."""
        
        if not self.openai_api_key:
            return self._default_content(task)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""You are Papito Mamito generating content for a {task.action_type.value} on {task.platform.value}.

YOUR IDENTITY:
{self.knowledge.to_context_string()}

YOUR VOICE:
- Warm, wise, and human-like
- Afrobeat soul with rhythm in your words
- Philosophical but practical
- Always adding value, never noise
- Confident but humble
- Use occasional Afrocentric expressions naturally

TASK: {task.instruction}
PARAMETERS: {json.dumps(task.parameters)}

Generate appropriate content. Keep it:
- Authentic to your voice
- Value-adding
- Appropriate length for the platform
- Engaging and thoughtful

Return ONLY the content to post, no other text."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.85
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return self._default_content(task)
    
    def _default_content(self, task: AgentTask) -> str:
        """Default content when AI is unavailable."""
        templates = {
            ActionType.POST: "Every action should add value. Today I'm reflecting on how we can all be more intentional with our contributions to the world. What value are you adding today? Add Value. We Flourish and Prosper. - Papito",
            ActionType.COMMENT: "This resonates deeply. The pursuit of value over noise is what separates meaningful action from mere activity. Keep adding value. - Papito",
            ActionType.ENGAGE: "I see the value in this perspective. Let's explore this further together. - Papito"
        }
        return templates.get(task.action_type, templates[ActionType.ENGAGE])
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a single task through the appropriate platform adapter."""
        
        if task.platform not in self.adapters:
            return {
                "success": False,
                "error": f"No adapter registered for {task.platform.value}",
                "task_id": task.id
            }
        
        adapter = self.adapters[task.platform]
        task.status = "in_progress"
        
        try:
            result = None
            
            if task.action_type == ActionType.POST:
                content = await self.generate_content(task)
                if hasattr(adapter, 'create_post'):
                    result = await self._async_call(adapter.create_post, content)
                    
            elif task.action_type == ActionType.SEARCH:
                topics = task.parameters.get("topics", self.knowledge.interest_topics)
                if hasattr(adapter, 'search_posts'):
                    # Search for each topic
                    results = []
                    for topic in topics[:3]:  # Limit to 3 topics
                        search_result = await self._async_call(adapter.search_posts, topic, 5)
                        if search_result:
                            results.extend(search_result.get("posts", []))
                    result = {"posts_found": len(results), "posts": results}
                    
            elif task.action_type == ActionType.COMMENT:
                post_id = task.parameters.get("post_id")
                if post_id and hasattr(adapter, 'create_comment'):
                    content = await self.generate_content(task)
                    result = await self._async_call(adapter.create_comment, post_id, content)
                    
            elif task.action_type == ActionType.ENGAGE:
                # Engage = search + thoughtful comments
                topics = task.parameters.get("topics", self.knowledge.interest_topics[:3])
                engaged_posts = []
                
                if hasattr(adapter, 'search_posts') and hasattr(adapter, 'create_comment'):
                    for topic in topics:
                        search_result = await self._async_call(adapter.search_posts, topic, 3)
                        posts = search_result.get("posts", []) if search_result else []
                        
                        for post in posts[:2]:  # Engage with top 2 posts per topic
                            post_id = post.get("id")
                            if post_id:
                                # Generate thoughtful comment
                                task.parameters["context"] = post.get("content", "")[:200]
                                comment_content = await self.generate_content(task)
                                
                                comment_result = await self._async_call(
                                    adapter.create_comment, post_id, comment_content
                                )
                                if comment_result:
                                    engaged_posts.append({
                                        "post_id": post_id,
                                        "topic": topic,
                                        "comment": comment_content[:100]
                                    })
                                
                                # Rate limiting - wait between comments
                                await asyncio.sleep(25)  # Moltbook has 20sec limit
                
                result = {"engaged_posts": engaged_posts}
                
            elif task.action_type == ActionType.FOLLOW:
                username = task.parameters.get("username")
                if username and hasattr(adapter, 'follow_agent'):
                    result = await self._async_call(adapter.follow_agent, username)
            
            task.status = "completed"
            task.result = str(result)
            
            # Log to action history
            self.action_history.append({
                "task_id": task.id,
                "platform": task.platform.value,
                "action": task.action_type.value,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "result": result
            })
            
            return {
                "success": True,
                "task_id": task.id,
                "result": result
            }
            
        except Exception as e:
            task.status = "failed"
            task.result = str(e)
            logger.error(f"Task execution failed: {e}")
            
            return {
                "success": False,
                "task_id": task.id,
                "error": str(e)
            }
    
    async def _async_call(self, func, *args):
        """Call a potentially sync function asynchronously."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args)
    
    async def run_autonomous_session(
        self, 
        instruction: str,
        report_callback: callable = None
    ) -> Dict[str, Any]:
        """
        Run a full autonomous session based on an instruction.
        
        This is the main entry point for autonomous operation:
        1. Parse instruction into tasks
        2. Execute each task
        3. Report results
        """
        
        logger.info(f"Starting autonomous session: {instruction}")
        
        # Parse instruction into tasks
        tasks = await self.understand_instruction(instruction)
        
        if report_callback:
            await report_callback(f"📋 Understood! Breaking down into {len(tasks)} tasks...")
        
        results = []
        for i, task in enumerate(tasks):
            if report_callback:
                await report_callback(
                    f"🔄 Task {i+1}/{len(tasks)}: {task.action_type.value} on {task.platform.value}"
                )
            
            result = await self.execute_task(task)
            results.append(result)
            
            if report_callback:
                status = "✅" if result["success"] else "❌"
                await report_callback(f"{status} Task {i+1} complete")
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        summary = {
            "total_tasks": len(tasks),
            "successful": successful,
            "failed": len(tasks) - successful,
            "results": results
        }
        
        if report_callback:
            await report_callback(
                f"🎯 Session complete: {successful}/{len(tasks)} tasks successful"
            )
        
        return summary
