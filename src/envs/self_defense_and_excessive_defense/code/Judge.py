from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class Judge(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("DefenseActionEvent", "evaluate_defense")

    async def evaluate_defense(self, event: Event) -> List[Event]:
        # Condition Check: Ensure defense action and threat level data are available
        if not event.defensive_action_type or not event.defense_intensity:
            return []
    
        # Access event data
        defensive_action_type = event.defensive_action_type
        defense_intensity = event.defense_intensity
        evidence_collected = event.evidence_collected
        defender_id = event.defender_id
        judge_id = self.profile.id
    
        # Construct observation and instruction for decision making
        observation = f"Defensive action: {defensive_action_type}, Intensity: {defense_intensity}, Evidence: {evidence_collected}"
        instruction = """Evaluate the defense based on legal standards, considering proportionality and necessity. 
        Determine if the defense is justified or excessive. Return the following JSON format:
    
        {
            "judgment_result": "<justified/excessive/unjustified>",
            "legal_reasons": "<Explanation of the legal rationale>",
            "threat_assessment": <Integer threat level assessment>,
            "defense_assessment": <Integer defense action assessment>,
            "completion_status": "<completed/pending>",
            "target_ids": ["ENV"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Extract results from LLM output
        judgment_result = result.get('judgment_result', 'undecided')
        legal_reasons = result.get('legal_reasons', '')
        threat_assessment = result.get('threat_assessment', 0)
        defense_assessment = result.get('defense_assessment', 0)
        completion_status = result.get('completion_status', 'pending')
        target_ids = result.get('target_ids', ['ENV'])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's state with LLM's returned results
        self.profile.update_data("judgment_result", judgment_result)
        self.profile.update_data("legal_reasons", legal_reasons)
        self.profile.update_data("threat_assessment", threat_assessment)
        self.profile.update_data("defense_assessment", defense_assessment)
        self.profile.update_data("completion_status", completion_status)
    
        # Prepare and send the JudgmentEvent to the EnvAgent
        events = []
        for target_id in target_ids:
            judgment_event = JudgmentEvent(
                from_agent_id=self.profile.id,
                to_agent_id=target_id,
                judgment_result=judgment_result,
                legal_reasons=legal_reasons,
                threat_assessment=threat_assessment,
                defense_assessment=defense_assessment,
                judge_id=judge_id,
                completion_status=completion_status
            )
            events.append(judgment_event)
    
        return events