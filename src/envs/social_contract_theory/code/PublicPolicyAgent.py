
from typing import Any, List,Optional
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


class PublicPolicyAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("SocialContractApprovalEvent", "evaluate_policy_impacts")

    async def evaluate_policy_impacts(self, event: Event) -> List[Event]:
        # Condition check for the action
        if event.__class__.__name__ != "SocialContractApprovalEvent":
            return []
    
        # Retrieve necessary event data
        policy_details = event.contract_terms
        approval_status = event.approval_status
    
        # Retrieve agent-specific data
        impact_analysis_results = self.profile.get_data("impact_analysis_results", {})
    
        # Generate instruction for decision making
        observation = f"Policy Details: {policy_details}, Approval Status: {approval_status}, Impact Analysis Results: {impact_analysis_results}"
        instruction = """Evaluate the impacts of the given policy details following the approval of social contract terms. 
        Return the analysis results in the following JSON format:
        
        {
        "policy_details": "<Details of the policy being analyzed>",
        "impact_analysis_results": <Results of the policy impact analysis as a dictionary>,
        "analysis_status": "<Status of the policy impact analysis>",
        "target_ids": ["ENV"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the response
        policy_details = result.get('policy_details', policy_details)
        impact_analysis_results = result.get('impact_analysis_results', impact_analysis_results)
        analysis_status = result.get('analysis_status', 'completed')
        target_ids = result.get('target_ids', 'ENV')
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update agent's profile with analysis results
        self.profile.update_data("impact_analysis_results", impact_analysis_results)
        self.profile.update_data("analysis_status", analysis_status)
    
        # Prepare and send PolicyImpactAnalysisEvent to the EnvAgent(s)
        events = []
        for target_id in target_ids:
            policy_impact_event = PolicyImpactAnalysisEvent(
                self.profile_id, target_id, policy_details, impact_analysis_results, analysis_status)
            events.append(policy_impact_event)
    
        return events
