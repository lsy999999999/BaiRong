from typing import Any, List, Optional
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class JobSeeker(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "enter_market")
        self.register_event("JobPostingDistributionEvent", "evaluate_job_applications")
        self.register_event("CandidateScreeningEvent", "negotiate_salaries")
        self.register_event("InterviewEvent", "decide_on_job_offers")

    async def enter_market(self, event: Event) -> List[Event]:
        skills = self.profile.get_data("skills", [])
        education = self.profile.get_data("education", "")
        experience = self.profile.get_data("experience", 0)
        job_preferences = self.profile.get_data("job_preferences", [])
        network = self.profile.get_data("network", [])
        risk_attitude = self.profile.get_data("risk_attitude", "neutral")
        job_search_strategy = self.profile.get_data("job_search_strategy", "active")
    
        self.profile.update_data("market_status", "active")
    
        instruction = """
        The job seeker is entering the labor market. Please provide a list of target_ids for the RecruitmentChannel agents that should be notified about this entry. 
        The response should be in the following JSON format:
        {
            "target_ids": ["<List of RecruitmentChannel agent IDs>"]
        }
        """
        observation = f"Skills: {skills}, Education: {education}, Experience: {experience}, Job Preferences: {job_preferences}, Network: {network}, Risk Attitude: {risk_attitude}, Job Search Strategy: {job_search_strategy}"
    
        result = await self.generate_reaction(instruction, observation)
    
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        events = []
        for target_id in target_ids:
            job_market_entry_event = JobMarketEntryEvent(
                self.profile_id, target_id,
                skills=skills,
                education=education,
                experience=experience,
                job_preferences=job_preferences,
                network=network,
                risk_attitude=risk_attitude,
                job_search_strategy=job_search_strategy
            )
            events.append(job_market_entry_event)
    
        return events

    async def evaluate_job_applications(self, event: Event) -> List[Event]:
        job_id = event.job_id
        application_cost = event.application_cost

        instruction = f"""
        Evaluate the job application for the job with Employer ID {job_id}.
        Consider the application cost of {application_cost}. 
        Please return the information in the following JSON format:

        {{
            "target_ids": ["<The string ID(s) of the Employer agent(s)>"],
            "application_value": <Calculated value of the job application>
        }}
        """

        observation = f"Job ID: {job_id}, Application Cost: {application_cost}"
        result = await self.generate_reaction(instruction, observation)

        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        application_value = result.get('application_value', 0.0)

        applications_submitted = self.profile.get_data("applications_submitted", [])
        applications_submitted.append(job_id)
        self.profile.update_data("applications_submitted", applications_submitted)

        events = []
        for target_id in target_ids:
            application_event = JobApplicationEvaluationEvent(
                self.profile_id,
                target_id,
                job_seeker_id=self.profile_id,
                job_id=job_id,
                application_value=application_value,
                candidate_id=self.profile_id
            )
            events.append(application_event)

        return events

    async def negotiate_salaries(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "CandidateScreeningEvent":
            return []

        employer_id = event.employer_id
        proposed_salary = event.proposed_salary

        observation = f"Employer ID: {employer_id}, Proposed Salary: {proposed_salary}"
        instruction = """You are engaging in salary negotiation with a potential employer. 
        Your negotiation strategy should consider your negotiation_style and reservation_wage. 
        Please generate negotiation outcomes and decide on target_ids for the next step. 
        Return the information in the following JSON format:

        {
        "negotiation_outcomes": "<List of outcomes from the negotiation>",
        "target_ids": ["<The string ID(s) of the Employer agent(s)>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        negotiation_outcomes = result.get('negotiation_outcomes', [])
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("negotiation_outcomes", negotiation_outcomes)

        events = []
        for target_id in target_ids:
            negotiation_event = SalaryNegotiationEvent(
                self.profile_id,
                target_id,
                job_seeker_id=self.profile_id,
                employer_id=employer_id,
                proposed_salary=proposed_salary
            )
            events.append(negotiation_event)

        return events

    async def decide_on_job_offers(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "InterviewEvent":
            return []

        employer_id = event.employer_id
        interview_outcome = event.interview_outcome
        offer_details = event.offer_details

        instruction = """You are a job seeker with multiple job offers. Evaluate each offer based on your preferences, skills match, and salary expectations. Decide whether to accept or reject each offer.
        Please return the decision in the following JSON format:

        {
        "offer_accepted": <True or False>,
        "offer_details": <Details of the job offer you decided on>,
        "target_ids": ["ENV"]
        }
        """

        observation = f"Employer ID: {employer_id}, Interview Outcome: {interview_outcome}, Offer Details: {offer_details}"

        result = await self.generate_reaction(instruction, observation)

        offer_accepted = result.get('offer_accepted', False)
        decision_offer_details = result.get('offer_details', {})
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        employment_status = 'employed' if offer_accepted else 'unemployed'
        self.profile.update_data("employment_status", employment_status)

        events = []
        for target_id in target_ids:
            job_offer_decision_event = JobOfferDecisionEvent(
                self.profile_id,
                target_id,
                job_seeker_id=self.profile_id,
                offer_accepted=offer_accepted,
                offer_details=decision_offer_details
            )
            events.append(job_offer_decision_event)

        return events