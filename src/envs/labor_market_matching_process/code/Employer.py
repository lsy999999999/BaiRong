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

class Employer(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "post_job_vacancies")
        self.register_event("JobApplicationEvaluationEvent", "screen_candidates")
        self.register_event("SalaryNegotiationEvent", "conduct_interviews")

    async def post_job_vacancies(self, event: Event) -> List[Event]:
        # Since there is no condition, proceed directly to the handler logic

        # Retrieve necessary data from the agent's profile
        job_id = self.profile.get_data("id", 0)
        job_description = self.profile.get_data("job_description", "")
        required_skills = self.profile.get_data("required_skills", [])

        # Prepare instruction for LLM to decide on target_ids
        instruction = """You are posting job vacancies to recruitment channels. 
        Please determine the target recruitment channels based on the current context and agent relationships. 
        Ensure to return the information in the following JSON format:

        {
        "target_ids": ["<A list of string IDs representing the recruitment channels>"]
        }
        """

        # Generate the reaction using the LLM
        result = await self.generate_reaction(instruction)

        # Extract target_ids from the LLM's response
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's posted_jobs list
        posted_jobs = self.profile.get_data("posted_jobs", [])
        posted_jobs.append(job_id)
        self.profile.update_data("posted_jobs", posted_jobs)

        # Prepare and send JobPostingEvent to each target_id
        events = []
        for target_id in target_ids:
            job_posting_event = JobPostingEvent(
                employer_id=self.profile_id,
                job_id=job_id,
                job_description=job_description,
                required_skills=required_skills,
                from_agent_id=self.profile_id,
                to_agent_id=target_id
            )
            events.append(job_posting_event)

        return events

    async def screen_candidates(self, event: Event) -> List[Event]:
        # Condition Check: Applications received
        if event.application_value <= 0:
            return []

        # Access required variables from event
        candidate_id = event.job_seeker_id
        application_value = event.application_value

        # Prepare observation and instruction for generate_reaction
        observation = f"Candidate ID: {candidate_id}, Application Value: {application_value}"
        instruction = """
        You are screening candidates for job vacancies. Based on the provided application value and candidate details, decide whether to proceed with the candidate and propose a salary for negotiation. Please return the information in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the JobSeeker agent(s)>"],
        "screening_result": "<Result of the screening process>",
        "proposed_salary": <Proposed salary for negotiation>
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        target_ids = result.get('target_ids', [])
        screening_result = result.get('screening_result', "pending")
        proposed_salary = result.get('proposed_salary', 0.0)

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update screened_candidates in agent profile
        screened_candidates = self.profile.get_data("screened_candidates", [])
        if candidate_id not in screened_candidates:
            screened_candidates.append(candidate_id)
        self.profile.update_data("screened_candidates", screened_candidates)
        logger.info(f"Employer: Screened candidates: {screened_candidates}")

        # Prepare and send CandidateScreeningEvent(s) to the target JobSeeker(s)
        events = []
        for target_id in target_ids:
            screening_event = CandidateScreeningEvent(
                employer_id=self.profile_id,
                candidate_id=candidate_id,
                screening_result=screening_result,
                proposed_salary=proposed_salary,
                from_agent_id=self.profile_id,
                to_agent_id=target_id
            )
            events.append(screening_event)

        return events

    async def conduct_interviews(self, event: Event) -> List[Event]:
        # Check condition: Candidate passed screening
        if not isinstance(event, SalaryNegotiationEvent):
            return []

        # Access required variables from the event
        candidate_id = event.job_seeker_id
        proposed_salary = event.proposed_salary

        # Generate reaction for conducting interviews
        instruction = """
        You are conducting interviews for candidates who have passed screening.
        Please determine the outcome for each candidate and decide on the appropriate next steps.
        Return the result in the following JSON format:
        {
            "target_ids": ["<The string ID(s) of the JobSeeker agent(s)>"],
            "interview_outcome": "<The result of the interview>",
            "offer_details": {"salary": <salary>, "position": "<position>", "benefits": "<benefits>"}
        }
        """
        observation = f"Candidate ID: {candidate_id}, Proposed Salary: {proposed_salary}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        target_ids = result.get('target_ids', [])
        interview_outcome = result.get('interview_outcome', 'pending')
        offer_details = result.get('offer_details', {})

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's interview results
        interview_results = self.profile.get_data('interview_results', [])
        interview_results.append({'candidate_id': candidate_id, 'outcome': interview_outcome})
        self.profile.update_data('interview_results', interview_results)

        # Prepare and send InterviewEvent to the relevant JobSeeker(s)
        events = []
        for target_id in target_ids:
            interview_event = InterviewEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                employer_id=self.profile_id,
                candidate_id=candidate_id,
                interview_outcome=interview_outcome,
                offer_details=offer_details
            )
            events.append(interview_event)

        return events