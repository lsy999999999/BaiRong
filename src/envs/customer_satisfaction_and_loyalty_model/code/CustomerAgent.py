from typing import Any, List, Optional
import json
import asyncio
import random
from loguru import logger
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class CustomerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initialize_customer")
        self.register_event("MerchantInitializedEvent", "perceive_quality")
        self.register_event("QualityAdjustedEvent", "perceive_quality")
        self.register_event("QualityPerceptionEvent", "evaluate_satisfaction")
        self.register_event("SatisfactionEvaluatedEvent", "update_loyalty")
        self.register_event("LoyaltyUpdatedEvent", "make_purchase_decision")

    async def initialize_customer(self, event: Event) -> List[Event]:
        # Prepare the instruction with observation context
        observation = "Initial setup for customer attributes."
        instruction = """
        Please generate the initialized values for 'service_sensitivity_coefficient', 'product_sensitivity_coefficient', and 'initial_loyalty'.
        Additionally, specify target_ids, which can be a single ID or a list, depending on the scenario.
        Return the information in the following JSON format:
        {
            "service_sensitivity_coefficient": <initialized service sensitivity coefficient>,
            "product_sensitivity_coefficient": <initialized product sensitivity coefficient>,
            "initial_loyalty": <initialized loyalty>,
            "target_ids": ["<The string ID of the MerchantAgent>"]
        }
        """
        # Generate the reaction from the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        service_sensitivity_coefficient = result.get('service_sensitivity_coefficient', random.uniform(0.8, 1.2))
        product_sensitivity_coefficient = result.get('product_sensitivity_coefficient', random.uniform(0.8, 1.2))
        initial_loyalty = result.get('initial_loyalty', 0.0)
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update agent's profile with the initialized values
        self.profile.update_data("service_sensitivity_coefficient", service_sensitivity_coefficient)
        self.profile.update_data("product_sensitivity_coefficient", product_sensitivity_coefficient)
        self.profile.update_data("loyalty", initial_loyalty)

        # Create and send the CustomerInitializedEvent to the MerchantAgent
        events = []
        for target_id in target_ids:
            customer_initialized_event = CustomerInitializedEvent(self.profile_id, target_id, initial_loyalty=initial_loyalty)
            events.append(customer_initialized_event)

        return events

    async def perceive_quality(self, event: Event) -> List[Event]:
        # Retrieve required data from event and agent profile
        if event.__class__.__name__ == "MerchantInitializedEvent":
            baseline_service_quality = event.baseline_service_quality
            baseline_product_quality = event.baseline_product_quality
        elif event.__class__.__name__ == "QualityAdjustedEvent":
            baseline_service_quality = eval(event.new_service_quality)
            baseline_product_quality = eval(event.new_product_quality)
        else:
            logger.warning(f"Unexpected event type: {event.__class__.__name__}")
            return []

        service_sensitivity_coefficient = self.profile.get_data("service_sensitivity_coefficient", 1.0)
        product_sensitivity_coefficient = self.profile.get_data("product_sensitivity_coefficient", 1.0)

        # Calculate perceived service quality and product experience score
        perceived_service_quality = baseline_service_quality * service_sensitivity_coefficient * (1 + 0.1 * (2 * random.random() - 1))
        product_experience_score = baseline_product_quality * product_sensitivity_coefficient * (1 + 0.1 * (2 * random.random() - 1))

        # Update agent profile with calculated values
        self.profile.update_data("perceived_service_quality", perceived_service_quality)
        self.profile.update_data("product_experience_score", product_experience_score)

        # Generate reaction instruction
        instruction = """Calculate perceived quality scores and return target_ids. 
        The event must include the calculated perceived_service_quality and product_experience_score.
        The JSON format should be:
        {
            "target_ids": ["<The string ID of the Customer agent>"]
        }
        """
        observation = f"Perceived service quality: {perceived_service_quality}, Product experience score: {product_experience_score}"

        result = await self.generate_reaction(instruction, observation)
        # target_ids = result.get('target_ids', None)
        target_ids = [self.profile_id]
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send QualityPerceptionEvent to the next action 'evaluate_satisfaction'
        events = []
        for target_id in target_ids:
            quality_perception_event = QualityPerceptionEvent(self.profile_id, target_id, perceived_service_quality, product_experience_score)
            events.append(quality_perception_event)

        return events

    async def evaluate_satisfaction(self, event: Event) -> List[Event]:
        # Retrieve required data from the event
        perceived_service_quality = event.perceived_service_quality
        product_experience_score = event.product_experience_score

        # Calculate satisfaction based on the provided formula
        satisfaction = 0.6 * perceived_service_quality + 0.4 * product_experience_score

        # Prepare the instruction for generating the reaction
        instruction = """
        Evaluate customer satisfaction based on perceived quality and product experience.
        Please return the information in the following JSON format:

        {
        "satisfaction_score": "<Calculated satisfaction score>"
        }
        """

        # Generate the reaction using the instruction and current context
        observation = f"Perceived Service Quality: {perceived_service_quality}, Product Experience Score: {product_experience_score}"
        result = await self.generate_reaction(instruction, observation)

        # Extract satisfaction score and target_ids from the result
        satisfaction_score = result.get('satisfaction_score', satisfaction)
        # target_ids = result.get('target_ids', None)
        target_ids = [self.profile_id]
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the new satisfaction score
        self.profile.update_data("satisfaction", satisfaction_score)

        # Prepare and send the SatisfactionEvaluatedEvent to the next action
        events = []
        for target_id in target_ids:
            satisfaction_event = SatisfactionEvaluatedEvent(self.profile_id, target_id, satisfaction_score)
            events.append(satisfaction_event)

        return events

    async def update_loyalty(self, event: Event) -> List[Event]:
        # Retrieve the satisfaction score from the incoming event
        if event.satisfaction_score.__class__.__name__ == 'str':
            satisfaction_score = eval(event.satisfaction_score)
        else:
            satisfaction_score = event.satisfaction_score
        

        # Retrieve the current loyalty score of the agent
        current_loyalty = self.profile.get_data("loyalty", 0.0)

        # Calculate the updated loyalty score based on satisfaction trends
        decay_factor = 0.1
        neutral_satisfaction = 0.5
        loyalty_update = (satisfaction_score - neutral_satisfaction) * decay_factor
        updated_loyalty = max(0.0, min(1.0, current_loyalty + loyalty_update))  # Constrain loyalty to [0, 1]

        # Update the loyalty score in the agent's profile
        self.profile.update_data("loyalty", updated_loyalty)

        # Prepare instruction for generating the next action's target IDs
        observation = f"Satisfaction score: {satisfaction_score}, Updated loyalty: {updated_loyalty}"
        instruction = """Based on the updated loyalty score, determine the target agent(s) for the next action 'make_purchase_decision'.
        Please return the information in the following JSON format:
        {
            "target_ids": ["<The string ID of the target agent(s)>"]
        }
        """

        # Generate reaction to determine target IDs for the next action
        result = await self.generate_reaction(instruction, observation)
        # target_ids = result.get("target_ids", [])
        target_ids = [self.profile_id]
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the LoyaltyUpdatedEvent to the target agents
        events = []
        for target_id in target_ids:
            loyalty_event = LoyaltyUpdatedEvent(self.profile_id, target_id, updated_loyalty)
            events.append(loyalty_event)

        return events

    async def make_purchase_decision(self, event: Event) -> List[Event]:
        # Retrieve required agent data
        satisfaction = self.profile.get_data("satisfaction", 0.5)
        loyalty = self.profile.get_data("loyalty", 0.0)

        # Generate observation for the LLM
        observation = f"Satisfaction: {satisfaction}, Loyalty: {loyalty}"

        # Craft instruction for the LLM
        instruction = """Calculate the purchase probability using the sigmoid function with inputs 2 * loyalty + 1.5 * satisfaction.
        Determine if a purchase is made by generating a random number and checking if it is less than the calculated purchase probability.
        Return the results in the following JSON format:
        {
            "purchase_decision": <true or false>,
            "purchase_probability": <a float between 0.0 and 1.0>,
            "target_ids": ["<The string ID(s) of the agent(s) for the next action>"]
        }
        """

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction, observation)

        # Parse the results
        purchase_decision = result.get('purchase_decision', False)
        purchase_probability = result.get('purchase_probability', 0.0)
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Handle cases where target_ids might be empty or invalid
        if not target_ids:
            logger.warning("No valid target IDs found for the next action.")
            return []

        # Update agent's state
        self.profile.update_data("purchase_decision", purchase_decision)
        self.profile.update_data("purchase_probability", purchase_probability)

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            if target_id == "MerchantAgent":
                purchase_event = PurchaseDecisionEvent(self.profile_id, target_id, purchase_decision, purchase_probability)
                events.append(purchase_event)
            elif target_id == "EnvAgent":
                end_event = EndEvent(self.profile_id, target_id, "Completed")
                events.append(end_event)

        return events