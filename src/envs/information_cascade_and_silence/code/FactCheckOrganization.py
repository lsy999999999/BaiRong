from typing import Any, List
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class FactCheckOrganization(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "monitor_rumors")
        self.register_event("ContentPublishedEvent", "verify_information")
        self.register_event("RumorDetectedEvent", "verify_information")

    async def monitor_rumors(self, event: Event) -> List[Event]:
        observation = "The fact-check organization is monitoring rumors on the social network. No specific condition is required to trigger this action."

        instruction = """
        You are tasked with detecting rumors on the social network as part of a fact-check organization's monitoring process. 
        Please identify the rumors, their content, and the detection confidence. Additionally, determine the appropriate target_ids 
        (other FactCheckOrganization agents) for initiating the verification process. The response must be in the following JSON format:

        {
            "detected_rumors": [ 
                {"rumor_content": "<Content of the detected rumor>", "detection_confidence": <Confidence level as a float>} 
            ],
            "target_ids": ["<List of target agent IDs to send RumorDetectedEvent>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        detected_rumors = result.get('detected_rumors', [])
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        current_rumors = self.profile.get_data("detected_rumors", [])
        unique_rumors = []
        for rumor in detected_rumors:
            existing_rumor = next((r for r in current_rumors if r['rumor_content'] == rumor['rumor_content']), None)
            if existing_rumor:
                existing_rumor.update(rumor)
            else:
                unique_rumors.append(rumor)

        self.profile.update_data("detected_rumors", current_rumors + unique_rumors)

        events = []
        for rumor in unique_rumors:
            rumor_content = rumor.get("rumor_content", "")
            detection_confidence = rumor.get("detection_confidence", 0.0)
            for target_id in target_ids:
                rumor_event = RumorDetectedEvent(
                    self.profile_id, 
                    target_id, 
                    rumor_content=rumor_content, 
                    detection_confidence=detection_confidence
                )
                events.append(rumor_event)

        return events

    async def verify_information(self, event: Event) -> List[Event]:
        if event.__class__.__name__ not in ["ContentPublishedEvent", "RumorDetectedEvent"]:
            return []

        if event.__class__.__name__ == "ContentPublishedEvent":
            observation = f"Event Type: ContentPublishedEvent; Published content: {event.published_content}; Fact-check organization ID: {event.fact_check_org_id}"
        elif event.__class__.__name__ == "RumorDetectedEvent":
            observation = f"Event Type: RumorDetectedEvent; Rumor content: {event.rumor_content}; Detection confidence: {event.detection_confidence}"

        instruction = """Analyze the given content and detection confidence to verify the accuracy of the information.
        Based on the analysis, generate a verification result ('verified', 'false', or 'unverified') and decide the target platform regulators to notify.
        Please return the information in the following JSON format:
        {
            "verification_result": "<Result of verification: 'verified', 'false', or 'unverified'>",
            "target_ids": ["<The string ID(s) of the PlatformRegulator agents>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)

        verification_result = result.get('verification_result', "unverified")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("verification_result", verification_result)

        events = []
        for target_id in target_ids:
            verification_event = VerificationCompleteEvent(self.profile_id, target_id, verification_result)
            events.append(verification_event)

        return events