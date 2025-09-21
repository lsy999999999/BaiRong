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

class IndividualAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "form_initial_judgment")
        self.register_event("InfluenceExertedEvent", "decide_conformity")
        self.register_event("LeaderInfluenceUpdatedEvent", "update_internal_belief")

    async def form_initial_judgment(self, event: Event) -> List[Event]:
        conformity_tendency = self.profile.get_data("conformity_tendency", 0.0)
        self_confidence = self.profile.get_data("self_confidence", 0.0)
        opinion_visibility = self.profile.get_data("opinion_visibility", False)
        environmental_factors = await self.get_env_data("environmental_factors", {})

        group_agents = await self.env.get_agent_data_by_type('GroupAgent', 'id')

        observation = f"""Conformity tendency: {conformity_tendency}, 
        Self-confidence: {self_confidence}, 
        Opinion visibility: {opinion_visibility}, 
        Environmental factors: {environmental_factors},
        IDs of candidate GroupAgents: {group_agents}"""

        instruction = """Based on the provided attributes and environmental context, 
        form an initial judgment for the individual. Return the result in the following JSON format:
        {
            "initial_judgment": "<The initial judgment formed>",
            "target_ids": ["<The string ID(s) of GroupAgent(s) to receive the initial judgment>"]
        }
        Ensure to include the individual's ID and the initial judgment in the response."""

        result = await self.generate_reaction(instruction, observation)

        initial_judgment = result.get('initial_judgment', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("initial_judgment", initial_judgment)

        events = []
        individual_id = self.profile_id
        for target_id in target_ids:
            initial_judgment_event = InitialJudgmentFormedEvent(
                self.profile_id, target_id, individual_id=individual_id, initial_judgment=initial_judgment)
            events.append(initial_judgment_event)

        return events


    async def decide_conformity(self, event: Event) -> List[Event]:
        try:
            # Get social_pressure with default value 0.0 if None
            social_pressure = await self.get_env_data("social_pressure", 0.0) or 0.0
            
            # Get leader_influence with proper validation
            leader_influence = getattr(event, 'influence_strength', None)
            if leader_influence is None:
                return []
            
            # Ensure leader_influence is a number
            try:
                leader_influence = float(leader_influence)
            except (TypeError, ValueError):
                return []

            # Get conformity_threshold with default value
            conformity_threshold = float(self.profile.get_data("conformity_threshold", 1.0))

            conformity_tendency = self.profile.get_data("conformity_tendency", 0.0)

            observation = f"Social pressure: {social_pressure}, Leader influence: {leader_influence}, Conformity threshold: {conformity_threshold}, Conformity tendency: {conformity_tendency}"
            instruction = """Update the conformity_tendengcy value (must be different from initial value). Evaluate whether the individual's conformity threshold is surpassed by the combined influence of social pressure and leader influence. 
            Please return the information in the following JSON format:
            {
            "conformity_tendency": <a new float to relfect the individual's current conformity>,
            "conformity_decision": <true if the individual decides to conform, false otherwise>,
            "target_ids": ["<The string ID(s) of the GroupAgent(s) to inform about the decision>"]
            }
            """

            result = await self.generate_reaction(instruction, observation)

            conformity_tendency = result.get('conformity_tendency', 0.0)
            conformity_decision = result.get('conformity_decision', False)
            target_ids = result.get('target_ids', None)
            if not isinstance(target_ids, list):
                target_ids = [target_ids] if target_ids is not None else []

            self.profile.update_data("conformity_decision", conformity_decision)
            self.profile.update_data("conformity_tendency", conformity_tendency)


            events = []
            individual_id = self.profile_id
            for target_id in target_ids:
                conformity_event = ConformityDecisionEvent(
                    self.profile_id, target_id, 
                    individual_id=individual_id, 
                    conformity_decision=conformity_decision
                )
                events.append(conformity_event)

            return events

        except Exception as e:
            print(f"Error in decide_conformity: {str(e)}")
            return []


    async def update_internal_belief(self, event: Event) -> List[Event]:
        new_information = getattr(event, 'updated_belief', None)
        if new_information is None:
            return []

        belief_certainty = self.profile.get_data("belief_certainty", 0.0)

        instruction = """
        You need to update the individual's internal belief based on new social pressure information and their current belief certainty.
        Please calculate the new belief and specify the target_ids for any agents that should be informed about this belief update.
        Return the response in the following JSON format:
        {
            "updated_belief": "<The updated belief string>",
            "target_ids": ["<The string ID(s) of the GroupAgent(s) to be informed>"]
        }
        """
        observation = f"New Information: {new_information}, Belief Certainty: {belief_certainty}"

        result = await self.generate_reaction(instruction, observation)

        updated_belief = result.get('updated_belief', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("updated_belief", updated_belief)

        events = []
        individual_id = self.profile_id
        for target_id in target_ids:
            belief_updated_event = BeliefUpdatedEvent(
                self.profile_id, target_id, individual_id=individual_id, updated_belief=updated_belief
            )
            events.append(belief_updated_event)

        return events

