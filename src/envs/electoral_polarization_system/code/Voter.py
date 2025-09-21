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

class Voter(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("AgendaSetEvent", "consume_media")
        self.register_event("PolicyPositionedEvent", "evaluate_candidates")
        self.register_event("StrategyAdaptedEvent", "evaluate_candidates")
        self.register_event("MediaConsumedEvent", "update_attitudes")

    async def consume_media(self, event: Event) -> List[Event]:
        media_content = event.agenda_topics
        voter_information_level = self.profile.get_data("voter_information_level", 0.0)

        observation = f"Media Content: {media_content}, Current Voter Information Level: {voter_information_level}"
        instruction = """Process the 'consume_media' action using the media content provided. 
        Update the voter's information and the voter's attitude based on the media content. 
        Return the information in the following JSON format:

        {
            "voter_information_level": "<Degree of voter information>"
            "attitude_change": "<Degree of attitude change>",
            "target_ids": ["<The string ID(s) of the Voter agent(s)>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        attitude_change = result.get('attitude_change', 0.0)
        voter_information_level = result.get('voter_information_level', 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("attitude_change", attitude_change)
        self.profile.update_data("voter_information_level", voter_information_level)

        events = []
        for target_id in target_ids:
            media_consumed_event = MediaConsumedEvent(self.profile_id, target_id, media_content, attitude_change)
            events.append(media_consumed_event)

        return events

    async def evaluate_candidates(self, event: Event) -> List[Event]:
        if event.__class__.__name__ not in ["StrategyAdaptedEvent", "PolicyPositionedEvent"]:
            return []

        self.profile.update_data(event.__class__.__name__, True)

        if not (self.profile.get_data("StrategyAdaptedEvent", False) and self.profile.get_data("PolicyPositionedEvent", False)):
            return []

        candidate_profiles = await self.get_env_data("candidate_profiles", [])
        evaluation_criteria = event.evaluation_criteria if hasattr(event, 'evaluation_criteria') else []

        observation = f"Candidate Profiles: {candidate_profiles}, Evaluation Criteria: {evaluation_criteria}"
        instruction = """Evaluate candidates based on the provided profiles and criteria.
        Please return the results in the following JSON format:

        {
        "evaluation_results": "<Results of the candidate evaluation process>",
        "target_ids": ["ENV"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)

        evaluation_results = result.get('evaluation_results', {})
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("evaluation_results", evaluation_results)

        events = []
        for target_id in target_ids:
            candidates_evaluated_event = CandidatesEvaluatedEvent(self.profile_id, target_id, evaluation_criteria, evaluation_results)
            events.append(candidates_evaluated_event)

        return events

    async def update_attitudes(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "MediaConsumedEvent":
            return []

        new_information = event.content_type
        attitude_change = event.attitude_change
        current_attitudes = self.profile.get_data("current_attitudes", {})

        party_ids = await self.env.get_agent_data_by_type("Party", "id")

        instruction = """
        You are updating voter attitudes based on new media information. 
        Use the 'new_information' from the event to modify 'current_attitudes'. 
        Calculate 'updated_attitudes' and specify 'target_ids' as a single or list of party agent IDs to send the update.
        Return the result in the following JSON format:
        {
            "updated_attitudes": "<The dictionary of updated voter attitudes>",
            "target_ids": ["<List of Party IDs>"]
        }
        """
        observation = f"New information: {new_information}, Attitude change: {attitude_change}, Current attitudes: {current_attitudes}, Candidate Party IDs: {party_ids}"
    
        result = await self.generate_reaction(instruction, observation)

        updated_attitudes = result.get('updated_attitudes', {})
        target_ids = result.get('target_ids', [])

        self.profile.update_data("updated_attitudes", updated_attitudes)

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            attitudes_updated_event = AttitudesUpdatedEvent(self.profile_id, target_id, updated_attitudes, influence_factors=[])
            events.append(attitudes_updated_event)

        return events