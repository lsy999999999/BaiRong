from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import DefenseSubmissionEvent, OvertimeRequestEvent, JudgmentEvent

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
        self.register_event("DefenseSubmissionEvent", "evaluate_overtime_claim")
        self.register_event("OvertimeRequestEvent", "evaluate_overtime_claim")

    async def evaluate_overtime_claim(self, event: Event) -> List[Event]:
        # Retrieve necessary data
        judge_id = self.profile.get_data("judge_id", "")
        defense_arguments = event.defense_arguments
        evidence_documents = event.evidence_documents

        # Prepare observation and instruction for generate_reaction
        observation = f"""Judge ID: {judge_id}, Defense Arguments: {defense_arguments}, Evidence Documents: {evidence_documents}"""
        instruction = """Please evaluate the overtime claim based on the provided arguments and evidence. 
        Generate a ruling, legal references, and completion status. 
        Return the information in the following JSON format:
    
        {
        "ruling": "<The decision regarding the overtime pay dispute>",
        "legal_references": ["<List of legal references or statutes cited>"],
        "completion_status": "<Current status of the judgment process>",
        "target_ids": ["ENV"]
        }
        """
    
        # Generate the reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's JSON response
        ruling = result.get('ruling', "")
        legal_references = result.get('legal_references', [])
        completion_status = result.get('completion_status', "Pending")
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare and send the JudgmentEvent to each target
        events = []
        for target_id in target_ids:
            judgment_event = JudgmentEvent(self.profile_id, target_id, judge_id, ruling, legal_references, completion_status)
            events.append(judgment_event)
    
        return events