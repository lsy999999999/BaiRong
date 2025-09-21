from typing import Any, List, Optional
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

class SocialNetworkAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "analyze_relationships")
        self.register_event("CooperationDecisionEvent", "update_network")
        self.register_event("RelationshipsAnalyzedEvent", "update_network")

    async def analyze_relationships(self, event: Event) -> List[Event]:
        network_id = self.profile.get_data("network_id", "")
        observation = f"Network ID: {network_id}"
        instruction = """
        You are tasked with analyzing the relationships within a social network to identify potential connections and resource flow.
        Based on this analysis, generate a summary and list potential updates to the network.
        Please return the information in the following JSON format:

        {
        "analysis_summary": "<Summary of the relationship analysis>",
        "potential_updates": ["<List of potential updates>"],
        "target_ids": ["<List of target agent IDs for network update>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)
        analysis_summary = result.get('analysis_summary', "Analysis pending")
        potential_updates = result.get('potential_updates', [])
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        self.profile.update_data("analysis_summary", analysis_summary)
        self.profile.update_data("potential_updates", potential_updates)
        events = []
        for target_id in target_ids:
            event = RelationshipsAnalyzedEvent(
                self.profile_id,
                target_id,
                network_id=network_id,
                analysis_summary=analysis_summary,
                potential_updates=potential_updates
            )
            events.append(event)
        return events

    async def update_network(self, event: Event) -> List[Event]:
        cooperation_decision_received = self.profile.get_data("cooperation_decision_received", False)
        relationships_analyzed_received = self.profile.get_data("relationships_analyzed_received", False)

        individual_id = ""
        decision = ""
        impact_on_network = ""
        network_id = ""
        analysis_summary = ""
        potential_updates = []

        if isinstance(event, CooperationDecisionEvent):
            cooperation_decision_received = True
            self.profile.update_data("cooperation_decision_received", True)
            individual_id = event.individual_id
            decision = event.decision
            impact_on_network = event.impact_on_network
        elif isinstance(event, RelationshipsAnalyzedEvent):
            relationships_analyzed_received = True
            self.profile.update_data("relationships_analyzed_received", True)
            network_id = event.network_id
            analysis_summary = event.analysis_summary
            potential_updates = event.potential_updates
        else:
            return []

        if not (cooperation_decision_received and relationships_analyzed_received):
            return []

        observation = f"Individual ID: {individual_id}, Decision: {decision}, Impact: {impact_on_network}, " \
                      f"Network ID: {network_id}, Analysis Summary: {analysis_summary}, " \
                      f"Potential Updates: {potential_updates}"
        instruction = """Based on the observation, update the network accordingly. 
        Ensure to decide on the target_ids which can be a single ID or a list of IDs. 
        Provide the results in the following JSON format:
        
        {
            "target_ids": ["ENV"],
            "update_status": "<Status of the update>",
            "changes_applied": ["<List of changes applied to the network>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)
        update_status = result.get('update_status', 'incomplete')
        changes_applied = result.get('changes_applied', [])
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("update_status", update_status)
        self.profile.update_data("changes_applied", changes_applied)
        self.profile.update_data("cooperation_decision_received", False)
        self.profile.update_data("relationships_analyzed_received", False)

        events = []
        for target_id in target_ids:
            network_updated_event = NetworkUpdatedEvent(
                self.profile_id, target_id, network_id=network_id,
                update_status=update_status, changes_applied=changes_applied
            )
            events.append(network_updated_event)

        return events