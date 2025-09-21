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

class RecruitmentChannel(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("JobMarketEntryEvent", "distribute_job_postings")
        self.register_event("JobPostingEvent", "distribute_job_postings")

    async def distribute_job_postings(self, event: Event) -> List[Event]:
        # Condition Check Implementation
        if isinstance(event, JobMarketEntryEvent):
            # Check specific fields for JobMarketEntryEvent
            if not hasattr(event, 'skills') or not hasattr(event, 'education') or not hasattr(event, 'experience'):
                return []
        elif isinstance(event, JobPostingEvent):
            # Check specific fields for JobPostingEvent
            if not hasattr(event, 'job_id') or not hasattr(event, 'required_skills'):
                return []
        else:
            return []

        # Data Access
        job_id = event.job_id if hasattr(event, 'job_id') else None
        channel_type = event.channel_type if hasattr(event, 'channel_type') else 'online'
        application_cost = event.application_cost if hasattr(event, 'application_cost') else 0.0
        distributed_jobs = await self.get_env_data("distributed_jobs", [])

        # Decision Making
        instruction = """
        The recruitment channel is tasked with distributing job postings to job seekers. 
        Please identify the target job seeker IDs who should receive the job posting based on their skills, education, experience, and job preferences.
        Ensure to return the information in the following JSON format:
        {
            "target_ids": ["<A list of job seeker IDs>"],
            "job_id": "<The unique identifier for the job>",
            "channel_type": "<The type of recruitment channel>"
        }
        """
        observation = f"Job ID: {job_id}, Channel Type: {channel_type}, Event Type: {event.__class__.__name__}"
        result = await self.generate_reaction(instruction, observation)

        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Response Processing
        events = []
        for target_id in target_ids:
            job_posting_event = JobPostingDistributionEvent(
                self.profile_id, target_id, channel_type=channel_type, job_id=job_id, application_cost=application_cost
            )
            events.append(job_posting_event)

        # Update Environment Data
        if job_id is not None:
            distributed_jobs.append(job_id)
            self.env.update_data("distributed_jobs", distributed_jobs)

        return events