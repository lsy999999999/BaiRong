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

class VoterAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "decide_participation")
        self.register_event("ParticipationDecisionEvent", "select_candidate")

    async def decide_participation(self, event: Event) -> List[Event]:
        # Retrieve necessary data
        voter_id = self.profile.get_data("voter_id", "unknown")
        external_influences = await self.get_env_data("external_influences", [])
        personal_preferences = self.profile.get_data("personal_preferences", [])
    
        # Prepare instruction for decision making
        instruction = """
        You are a voter deciding whether to participate in the voting process.
        Consider your personal preferences and any external influences.
        Return your decision in the following JSON format:
        {
        "participation_decision": <true or false>,
        "reason_for_non_participation": "<Reason if not participating>"
        }
        """
    
        observation = f"External influences: {external_influences}, Personal preferences: {personal_preferences}"
        
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        participation_decision = result.get('participation_decision', False)
        reason_for_non_participation = result.get('reason_for_non_participation', "none")
        if participation_decision:
            target_ids = [self.profile_id]
        else:
            target_ids = ["ENV"]
    
        # Prepare events based on participation decision
        events = []
        if participation_decision:
            for target_id in target_ids:
                participation_event = ParticipationDecisionEvent(self.profile_id, target_id, voter_id, participation_decision)
                events.append(participation_event)
        else:
            for target_id in target_ids:
                non_participation_event = NonParticipationEvent(self.profile_id, target_id, voter_id, reason_for_non_participation)
                events.append(non_participation_event)
    
        return events

    async def select_candidate(self, event: Event) -> List[Event]:
        # Check if the event is of type ParticipationDecisionEvent and if the voter has decided to participate
        if not isinstance(event, ParticipationDecisionEvent) or not event.participation_decision:
            logger.warning("Event type is not ParticipationDecisionEvent or participation decision is False.")
            return []
    
        # Retrieve necessary data
        voter_id = self.profile.get_data("voter_id", "unknown")
        candidate_list = await self.get_env_data("candidate_list", [])
        personal_preferences = self.profile.get_data("personal_preferences", [])
    
        # Prepare observation and instruction for decision making
        observation = f"Voter ID: {voter_id}, Candidate List: {candidate_list}, Preferences: {personal_preferences}"
        instruction = """Based on the voter's preferences and the available candidates, select the most suitable candidate.
    Please return the information in the following JSON format:
    
    {
        "selected_candidate_id": "<The string ID of the selected candidate>",
        "preference_score": <The float score representing the preference>,
        "target_ids": ["ENV"]
    }
    """
    
        # Generate the reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Extract the results from the LLM's response
        selected_candidate_id = result.get('selected_candidate_id', "none")
        preference_score = result.get('preference_score', 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the agent's state with the selected candidate and preference score
        self.profile.update_data("selected_candidate_id", selected_candidate_id)
        self.profile.update_data("preference_score", preference_score)
    
        # Prepare and send the CandidateSelectionEvent to the EnvAgent
        events = []
        for target_id in target_ids:
            candidate_selection_event = CandidateSelectionEvent(self.profile_id, target_id, voter_id, selected_candidate_id, preference_score)
            events.append(candidate_selection_event)
    
        return events