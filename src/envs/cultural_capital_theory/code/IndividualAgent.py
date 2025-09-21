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
        self.register_event("StartEvent", "evaluate_cultural_capital")
        self.register_event("SocialClassAssessedEvent", "evaluate_cultural_capital")
        self.register_event("CulturalCapitalEvaluatedEvent", "pursue_education")
        self.register_event("EducationCompletedEvent", "seek_job_opportunities")

    async def evaluate_cultural_capital(self, event: Event) -> List[Event]:
        social_class = getattr(event, 'social_class', 'unknown')
        influence_on_cultural_capital = getattr(event, 'influence_on_cultural_capital', 'neutral')

        observation = f"Social class: {social_class}, Influence: {influence_on_cultural_capital}"
        instruction = """
        Evaluate the individual's cultural capital based on the provided social class and influence.
        Determine the new level of cultural capital and decide if the individual should pursue further education.
        Please return the information in the following JSON format:
    
        {
        "cultural_capital_level": <The evaluated float level of cultural capital>,
        "education_decision": <True or False based on whether to pursue further education>
        }
        """
        
        result = await self.generate_reaction(instruction, observation)

        cultural_capital_level = result.get('cultural_capital_level', 0.0)
        education_decision = result.get('education_decision', False)

        self.profile.update_data("cultural_capital_level", cultural_capital_level)
        self.profile.update_data("education_decision", education_decision)

        events = []
        cultural_capital_evaluated_event = CulturalCapitalEvaluatedEvent(
            self.profile_id, self.profile_id, cultural_capital_level, education_decision
        )
        events.append(cultural_capital_evaluated_event)

        return events

    async def pursue_education(self, event: Event) -> List[Event]:
        cultural_capital_level = event.cultural_capital_level
        education_decision = event.education_decision

        # if cultural_capital_level < 0.5 or not education_decision:
        #     return []

        education_level = self.profile.get_data("education_level", "None")
        job_search_status = self.profile.get_data("job_search_status", "not_started")

        instruction = """You are tasked with deciding the next steps for pursuing education based on cultural capital evaluation.
        Please generate the outcome in the following JSON format:
    
        {
        "education_level": "<The updated level of education completed>",
        "job_search_status": "<The updated status of job search>"
        }
        """
        observation = f"Cultural Capital Level: {cultural_capital_level}, Current Education Level: {education_level}, Job Search Status: {job_search_status}"
        
        result = await self.generate_reaction(instruction, observation)

        education_level = result.get('education_level', "None")
        job_search_status = result.get('job_search_status', "not_started")

        self.profile.update_data("education_level", education_level)
        self.profile.update_data("job_search_status", job_search_status)

        events = []
        education_completed_event = EducationCompletedEvent(
            self.profile_id, self.profile_id, education_level, job_search_status
        )
        events.append(education_completed_event)

        return events

    async def seek_job_opportunities(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "EducationCompletedEvent":
            return []

        education_level = event.education_level
        job_search_status = event.job_search_status

        if job_search_status == "completed":
            return []

        self.profile.update_data("education_level", education_level)
        self.profile.update_data("job_search_status", job_search_status)

        observation = f"Education level: {education_level}, Job search status: {job_search_status}"
        instruction = """Based on the received education level and job search status, determine the job position the agent should seek. 
        Return the following JSON format:
        {
            "job_position": "<The job position found by the agent>",
            "workflow_completion_status": "<Status indicating completion of job search workflow>",
            "target_ids": ["ENV"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)

        job_position = result.get('job_position', "None")
        workflow_completion_status = result.get('workflow_completion_status', "incomplete")
        target_ids = result.get('target_ids', ["ENV"])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("job_position", job_position)
        self.profile.update_data("workflow_completion_status", workflow_completion_status)

        events = []
        for target_id in target_ids:
            job_event = JobOpportunityFoundEvent(self.profile_id, target_id, job_position, workflow_completion_status)
            events.append(job_event)

        return events