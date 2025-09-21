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

class OpinionLeaderAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "exert_influence")

    async def exert_influence(self, event: Event) -> List[Event]:
        # Retrieve charisma and credibility from the agent's profile
        charisma = self.profile.get_data("charisma", 0.0)
        credibility = self.profile.get_data("credibility", 0.0)
    
        # Calculate influence strength based on charisma and credibility
        influence_strength = charisma * credibility
    
        # Update the agent's profile with the calculated influence strength
        self.profile.update_data("influence_strength", influence_strength)
    
        # Construct the instruction for generate_reaction
        instruction = """
        As an opinion leader, exert influence on individual agents to sway their opinions or conformity decisions.
        Use your charisma and credibility to determine the influence strength. The new generated influence strength must be different from before.
        Please return the information in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the Individual agents>"],
        "influence_strength": <calculated influence strength>
        }
        """
        
        # Construct observation context
        observation = f"Charisma: {charisma}, Credibility: {credibility}, Previous Influence Strength: {influence_strength}"
    
        # Generate reaction and get the result
        result = await self.generate_reaction(instruction, observation)
    
        # Extract target_ids and influence_strength from the result
        target_ids = result.get('target_ids', [])
        influence_strength = result.get('influence_strength', 0.0)
        self.profile.update_data('influence_strength', influence_strength)
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare and send the InfluenceExertedEvent and LeaderInfluenceUpdatedEvent to each target
        events = []
        for target_id in target_ids:
            influence_event = InfluenceExertedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                leader_id=self.profile_id,
                target_individual_id=target_id,
                influence_strength=influence_strength
            )
            belief_update_event = LeaderInfluenceUpdatedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                leader_id=self.profile_id,
                target_individual_id=target_id,
                updated_belief=f"Updated belief after influence with strength {influence_strength}"
            )
            events.append(influence_event)
            events.append(belief_update_event)
    
        return events