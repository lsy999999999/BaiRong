from typing import Any, List, Optional
import json
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

class DefenseLawyer(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "prepare_defense")
        self.register_event("ProsecutionDecisionEvent", "negotiate_plea")

    async def prepare_defense(self, event: Event) -> List[Event]:
        # Check if the case details and evidence are available
        case_details = self.profile.get_data("case_details", None)
        evidence = self.profile.get_data("evidence", None)
    
        if case_details is None or evidence is None:
            return []  # Condition not met, exit handler
    
        # Retrieve the current defense strategy if available
        defense_strategy = self.profile.get_data("defense_strategy", "")

        # Prepare the observation and instruction for the LLM
        observation = f"Case details: {case_details}, Evidence: {evidence}, Defense strategy: {defense_strategy}"
        instruction = """
        Formulate a comprehensive defense strategy for the client based on the available case details and evidence.
        Ensure that the strategy considers all relevant legal precedents and procedural rules.
        Please return the information in the following JSON format:
    
        {
        "prepared_defense": "<The completed defense strategy>",
        "target_ids": ["<The string ID of the Judge agent>"]
        }
        """

        # Generate the reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract the prepared defense strategy and target IDs from the LLM's response
        prepared_defense = result.get('prepared_defense', None)
        target_ids = result.get('target_ids', None)
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the prepared defense strategy
        self.profile.update_data("prepared_defense", prepared_defense)

        # Prepare and send the DefensePreparedEvent to the Judge
        events = []
        for target_id in target_ids:
            defense_prepared_event = DefensePreparedEvent(self.profile_id, target_id, prepared_defense)
            events.append(defense_prepared_event)

        return events

    async def negotiate_plea(self, event: Event) -> List[Event]:
        # Condition Check: Ensure Prosecution decision received
        prosecution_decision = event.prosecution_decision
        if prosecution_decision == "undecided":
            return []

        # Access required variables
        plea_terms = self.profile.get_data("plea_terms", "")
    
        # Prepare observation and instruction for decision making
        observation = f"Prosecution decision: {prosecution_decision}, Plea terms: {plea_terms}"
        instruction = """Engage in plea negotiation based on the prosecution decision and proposed plea terms.
        Please return the information in the following JSON format:

        {
        "negotiated_plea": "<Outcome of the plea negotiation>",
        "target_ids": ["<The string ID(s) of the Defendant agent>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        negotiated_plea = result.get('negotiated_plea', "")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent state with negotiated plea
        self.profile.update_data("negotiated_plea", negotiated_plea)

        # Prepare and send PleaNegotiationEvent to Defendant
        events = []
        for target_id in target_ids:
            plea_event = PleaNegotiationEvent(self.profile_id, target_id, negotiated_plea)
            events.append(plea_event)

        return events