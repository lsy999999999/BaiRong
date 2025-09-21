from typing import Any, List
import json
import asyncio
from loguru import logger
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import *

class MerchantAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initialize_merchant")
        self.register_event("CustomerInitializedEvent", "collect_feedback")
        self.register_event("PurchaseDecisionEvent", "collect_feedback")
        self.register_event("FeedbackCollectedEvent", "adjust_quality")

    async def initialize_merchant(self, event: Event) -> List[Event]:
        # Access environment variables for initial baseline service and product quality
        baseline_service_quality = await self.get_env_data("baseline_service_quality", 0.0)
        baseline_product_quality = await self.get_env_data("baseline_product_quality", 0.0)

        # Initialize baseline service and product quality levels with random values between 0.3 and 0.7
        import random
        service_quality = random.uniform(0.3, 0.7)
        product_quality = random.uniform(0.3, 0.7)

        # Update agent profile with the initialized values
        self.profile.update_data("service_quality", service_quality)
        self.profile.update_data("product_quality", product_quality)

        customer_agents = await self.env.get_agent_data_by_type('CustomerAgent', 'id')

        # Prepare instruction for LLM to generate reaction
        instruction = """
        Initialize the merchant's baseline service and product quality levels.
        Ensure to return the target_ids for the next event.
        Please return the information in the following JSON format:

        {
        "merchant_id": "<Unique identifier for the merchant>",
        "baseline_service_quality": <The initialized baseline service quality level>,
        "baseline_product_quality": <The initialized baseline product quality level>,
        "target_ids": ["<The string ID(s) of the CustomerAgent(s)>"]
        }
        """

        # Generate reaction using LLM
        observation = f"Service Quality: {service_quality}, Product Quality: {product_quality}, Candidate IDs of Customer Agents: {customer_agents}"
        result = await self.generate_reaction(instruction, observation)

        # Extract results from LLM response
        merchant_id = result.get('merchant_id', None)
        target_ids = result.get('target_ids', [])

        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and send MerchantInitializedEvent to each target_id
        events = []
        for target_id in target_ids:
            merchant_initialized_event = MerchantInitializedEvent(
                self.profile_id, target_id,
                merchant_id=merchant_id,
                baseline_service_quality=service_quality,
                baseline_product_quality=product_quality
            )
            events.append(merchant_initialized_event)

        return events

    async def collect_feedback(self, event: Event) -> List[Event]:
        # Extract the purchase decision from the event
        purchase_decision = getattr(event, 'purchase_decision', False)

        # Calculate the feedback score based on the purchase decision
        feedback_score = 1.0 if purchase_decision else 0.0

        # Retrieve current average feedback score and customer count from the agent profile
        current_feedback_score = self.profile.get_data("average_feedback_score", 0.0)
        customer_count = self.profile.get_data("customer_count", 1)

        # Update the average feedback score
        new_average_feedback_score = ((current_feedback_score * customer_count) + feedback_score) / (customer_count + 1)
        self.profile.update_data("average_feedback_score", new_average_feedback_score)
        self.profile.update_data("customer_count", customer_count + 1)

        # Prepare the instruction for the LLM to generate the reaction
        instruction = """
        Calculate the average feedback score from customer purchase decisions and determine the target_ids for sending the FeedbackCollectedEvent. 
        Please return the information in the following JSON format:
        {
            "average_feedback_score": <calculated average feedback score>,
            "target_ids": ["<The string ID(s) of the MerchantAgent(s)>"]
        }
        """

        # Generate the reaction using the LLM
        observation = f"Current feedback score: {new_average_feedback_score}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the result
        average_feedback_score = result.get('average_feedback_score', new_average_feedback_score)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Create and return the FeedbackCollectedEvent for each target_id
        events = []
        for target_id in target_ids:
            feedback_event = FeedbackCollectedEvent(self.profile_id, target_id, average_feedback_score)
            events.append(feedback_event)

        return events

    async def adjust_quality(self, event: Event) -> List[Event]:
        # Condition check: Every 3 time steps
        current_time_step = self.profile.get_data("current_time_step", 0)
        if current_time_step % 3 != 0:
            self.profile.update_data("current_time_step", current_time_step + 1)
            return []

        # Update the current time step in the agent profile
        self.profile.update_data("current_time_step", current_time_step + 1)

        # Accessing the average feedback score from the event
        average_feedback_score = event.average_feedback_score

        # Instruction for LLM to adjust qualities and decide target_ids
        instruction = f"""
        Context: The MerchantAgent needs to adjust service and product quality levels based on average customer feedback.
        Average feedback score received: {average_feedback_score}
    
        Please calculate the new service quality and product quality based on the feedback score.
        Return the results in the following JSON format:

        {{
            "new_service_quality": "<Calculated new service quality>",
            "new_product_quality": "<Calculated new product quality>",
            "target_ids": ["<The string ID of the CustomerAgent>", "ENV"]
        }}
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction)

        # Extract new quality levels and target_ids
        new_service_quality = result.get("new_service_quality", 0.0)
        new_product_quality = result.get("new_product_quality", 0.0)
        target_ids = result.get("target_ids", [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with new quality levels
        self.profile.update_data("service_quality", new_service_quality)
        self.profile.update_data("product_quality", new_product_quality)

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            if target_id == "ENV":
                # Send EndEvent to EnvAgent
                end_event = EndEvent(self.profile_id, target_id, completion_status="Completed")
                events.append(end_event)
            else:
                # Send QualityAdjustedEvent to CustomerAgent
                quality_event = QualityAdjustedEvent(
                    self.profile_id, target_id,
                    new_service_quality=new_service_quality,
                    new_product_quality=new_product_quality
                )
                events.append(quality_event)

        return events