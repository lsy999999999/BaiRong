from typing import Any, List
import asyncio
from loguru import logger
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
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "manage_trial")
        self.register_event("EvidenceEvaluatedEvent", "rule_on_evidence")
        self.register_event("DefensePreparedEvent", "manage_trial")
        self.register_event("PleaDecisionEvent", "manage_trial")
        self.register_event("TestimonyPreparedEvent", "manage_trial")

    async def manage_trial(self, event: Event) -> List[Event]:
        # Condition Check: "Defense prepared and evidence ruled admissible"
        defense_strategy = self.profile.get_data("defense_strategy", None)
        evidence_admissible = self.profile.get_data("evidence_admissibility", "pending")
    
        if not (defense_strategy and evidence_admissible == "admissible"):
            return []

        # Retrieve trial phase from agent profile
        trial_phase = self.profile.get_data("trial_phase", "initiation")

        # Generate reaction with instruction and observation
        instruction = """Please decide on the appropriate targets for managing the trial proceedings. 
        Ensure the trial phase is updated correctly and return the target_ids in a JSON format:
    
        {
        "trial_phase": "<Updated trial phase>",
        "trial_status": "<Current status of the trial>",
        "target_ids": ["<List of target agent IDs>"]
        }
        """
        observation = f"Current trial phase: {trial_phase}, Defense strategy: {defense_strategy}, Evidence admissible: {evidence_admissible}"
    
        result = await self.generate_reaction(instruction, observation)

        # Extracting results
        trial_phase = result.get('trial_phase', trial_phase)
        trial_status = result.get('trial_status', "ongoing")
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent profile with new trial phase and status
        self.profile.update_data("trial_phase", trial_phase)
        self.profile.update_data("trial_status", trial_status)

        # Prepare outgoing events based on the updated trial phase and target IDs
        events = []
        for target_id in target_ids:
            if trial_phase == "ongoing":
                trial_event = TrialManagementEvent(self.profile_id, target_id, trial_phase)
                events.append(trial_event)
            elif trial_phase == "witness_call":
                witness_event = WitnessCallEvent(self.profile_id, target_id, "")
                events.append(witness_event)

        return events

    async def rule_on_evidence(self, event: Event) -> List[Event]:
        # Check if the condition "Evaluated evidence presented by prosecutor" is met
        if not event.evidence_details:
            return []

        # Access the required variables from the event
        evidence_details = event.evidence_details
        ruling_request = event.ruling_request

        # Construct the observation and instruction for generate_reaction
        observation = f"Evidence Details: {evidence_details}, Ruling Request: {ruling_request}"
        instruction = """Evaluate the presented evidence and decide on its admissibility in court.
        Consider the details and request provided. Return the ruling decision and target_ids in the following JSON format:

        {
        "evidence_admissibility": "<Admissibility decision of the evidence>",
        "target_ids": ["<The string ID(s) of the Jury agent(s)>"]
        }
        """

        # Generate a reaction using the LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Extract the admissibility decision and target_ids from the result
        evidence_admissibility = result.get('evidence_admissibility', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the new evidence admissibility
        self.profile.update_data("evidence_admissibility", evidence_admissibility)

        # Prepare and send the EvidenceRulingEvent to the target(s)
        events = []
        for target_id in target_ids:
            ruling_event = EvidenceRulingEvent(self.profile_id, target_id, evidence_admissibility)
            events.append(ruling_event)

        return events