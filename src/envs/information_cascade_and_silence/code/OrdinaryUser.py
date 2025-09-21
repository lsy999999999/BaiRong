
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


class OrdinaryUser(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "receive_information")
        self.register_event("InformationReceivedEvent", "evaluate_information")
        self.register_event("EvaluationCompleteEvent", "express_opinion")
        self.register_event("OpinionExpressedEvent", "spread_information")

    async def receive_information(self, event: Event) -> List[Event]:
        instruction = """
        You are an OrdinaryUser in a social network simulation.
        Your task is to decide which user(s) to forward some information to based on the social network structure and the information's credibility.
        Please return the response in the following JSON format:
    
        {
            "target_ids": ["<List of target user IDs>"],
            "information_content": "<Some information content>",
            "credibility_score": <Optional: Adjusted credibility score as a float>
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction)

        # Parse response
        target_ids = result.get("target_ids", [])
        information_content = result.get("information_content", "some information content")
        credibility_score = result.get("credibility_score", 1.0)
        self.profile.update_data("credibility_score", credibility_score)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            outgoing_event = InformationReceivedEvent(
                self.profile_id,
                target_id,
                information_content=information_content,
                source_user_id=self.profile_id,
                credibility_score=credibility_score
            )
            events.append(outgoing_event)
    
        return events

    async def evaluate_information(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event matches the required condition
        if not event.information_content or event.__class__.__name__ != "InformationReceivedEvent":
            return []

        # Retrieve required variables from agent profile and event
        information_content = event.information_content
        credibility_score = event.credibility_score
        verification_tendency = self.profile.get_data("verification_tendency", 0.0)

        # Prepare observation and instruction for generate_reaction
        observation = f"Information content: {information_content}, Credibility score: {credibility_score}, Verification tendency: {verification_tendency}"
        instruction = """Evaluate the credibility of the received information based on the user's verification tendency and perceived credibility score. 
        Return the evaluation result ('credible', 'not credible', or 'undecided') and the target_ids for the outgoing event in the following JSON format:
        {
            "evaluation_result": "<Evaluation result>",
            "expression_willingness": <A float value indicating willingness to express opinion>,
            "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the result
        evaluation_result = result.get("evaluation_result", "undecided")
        expression_willingness = result.get("expression_willingness", 0.0)
        target_ids = result.get("target_ids", [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the evaluation result
        self.profile.update_data("evaluation_result", evaluation_result)

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            outgoing_event = EvaluationCompleteEvent(
                self.profile_id, target_id, evaluation_result, expression_willingness
            )
            events.append(outgoing_event)

        return events

    async def express_opinion(self, event: Event) -> List[Event]:
        # Check if the condition "Credibility evaluation and isolation risk assessment complete" is met
        evaluation_result = self.profile.get_data("evaluation_result", "undecided")
        isolation_fear = self.profile.get_data("isolation_fear", 0.0)
        expression_willingness = self.profile.get_data("expression_willingness", 0.0)

        if evaluation_result == "undecided" or isolation_fear is None:
            return []

        # Generate reaction to decide whether to express opinion
        observation = f"Evaluation Result: {evaluation_result}, Isolation Fear: {isolation_fear}, Expression Willingness: {expression_willingness}"
        instruction = """Based on the evaluation result and isolation fear, decide whether to express an opinion publicly. 
        Consider the expression willingness and evaluate the situation. 
        Return the information in the following JSON format:
        {
            "opinion_content": "<The content of the opinion expressed>",
            "target_ids": ["<The string ID or list of IDs of the target audience>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        opinion_content = result.get('opinion_content', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the expressed opinion in the agent's profile
        self.profile.update_data("expressed_opinion", opinion_content)

        # Prepare and send the OpinionExpressedEvent to the target audience
        events = []
        for target_id in target_ids:
            opinion_event = OpinionExpressedEvent(self.profile_id, target_id, opinion_content, target_ids)
            events.append(opinion_event)

        return events

    async def spread_information(self, event: Event) -> List[Event]:
        # Condition check (no specific condition defined, so always proceed)
    
        # Access required variables from the event
        opinion_content = event.opinion_content
        target_audience = event.target_audience

        # Validate required fields
        if not opinion_content or not target_audience:
            return []  # Return empty list if required fields are missing

        # Generate reaction to determine target IDs and outgoing event content
        observation = f"Opinion Content: {opinion_content}, Target Audience: {target_audience}"
        instruction = """You are simulating an Ordinary User spreading information in a social network. 
        Based on the provided opinion content and target audience, decide the appropriate target IDs for spreading the information. 
        The target IDs can be a single ID or a list of IDs. Ensure the information content aligns with the provided opinion content. 
        Return the result in the following JSON format:

        {
        "information_content": "<The content of the information being spread>",
        "target_ids": ["<String ID(s) of the target audience>"]
        }
        """
    
        result = await self.generate_reaction(instruction, observation)
    
        information_content = result.get('information_content', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send InformationSpreadEvent to each target
        events = []
        for target_id in target_ids:
            spread_event = InformationSpreadEvent(self.profile_id, target_id, information_content)
            events.append(spread_event)
    
        return events
