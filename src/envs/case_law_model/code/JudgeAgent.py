from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import PrecedentInterpretedEvent, JudgmentAppliedEvent

class JudgeAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "interpret_precedents")
        self.register_event("PrinciplesStoredEvent", "interpret_precedents")
        self.register_event("InfluencesAnalyzedEvent", "apply_judgment")

    async def interpret_precedents(self, event: Event) -> List[Event]:
        # No condition specified, proceed directly
        stored_principles = getattr(event, 'stored_principles', "")
        
        # Prepare observation and instruction for decision making
        observation = f"Stored principles: {stored_principles}"
        instruction = """Interpret the given legal principles to generate a detailed description of the interpreted precedents. 
        The description should be ready for application in current cases. 
        Please return the information in the following JSON format:

        {
        "interpreted_precedents": "<Details of the interpreted precedents>",
        "target_ids": ["<The string ID(s) of the CaseAgent(s)>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's response
        interpreted_precedents = result.get('interpreted_precedents', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's state with interpreted precedents
        self.profile.update_data("interpreted_precedents", interpreted_precedents)

        # Prepare and send PrecedentInterpretedEvent to each target
        events = []
        for target_id in target_ids:
            precedent_event = PrecedentInterpretedEvent(self.profile_id, target_id, interpreted_precedents)
            events.append(precedent_event)

        return events

    async def apply_judgment(self, event: Event) -> List[Event]:
        # Check if the required conditions are met
        interpreted_precedents = self.profile.get_data("interpreted_precedents", "")
        socio_political_influences = getattr(event, 'socio_political_influences', "")
        
        if not interpreted_precedents or not socio_political_influences:
            return []

        # Prepare the instruction for generate_reaction
        observation = f"Interpreted Precedents: {interpreted_precedents}, Socio-Political Influences: {socio_political_influences}"
        instruction = """Please apply the judgment based on the given interpreted precedents and socio-political influences.
        Return the result in the following JSON format:

        {
        "judgment_result": "<The result of the applied judgment>",
        "target_ids": ["<The ID(s) of the agent(s) to send the JudgmentAppliedEvent>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        judgment_result = result.get('judgment_result', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the profile with the judgment result
        self.profile.update_data("judgment_result", judgment_result)

        # Create and send JudgmentAppliedEvent(s)
        events = []
        for target_id in target_ids:
            judgment_event = JudgmentAppliedEvent(self.profile_id, target_id, judgment_result, "completed")
            events.append(judgment_event)

        return events