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

class ManagerAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_workflow_design")
        self.register_event("WorkflowDesignedEvent", "allocate_tasks")
        self.register_event("PerformanceEvaluatedEvent", "provide_feedback_and_incentives")
        self.register_event("TasksExecutedEvent", "evaluate_performance")
        self.register_event("PerformanceAdjustedEvent", "finalize_workflow")

    async def initiate_workflow_design(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "StartEvent":
            return []

        instruction = """Begin the process of designing a workflow by analyzing tasks and determining optimal task allocation strategies.
        Please return the information in the following JSON format:
        {
            "workflow_design_status": "Initiated",
            "workflow_id": "<Unique identifier for the workflow>",
            "designer_id": "<Identifier of the manager who designed the workflow>",
            "design_details": "<Details of the workflow design>",
            "target_ids": ["<The string ID of the Manager agent for task allocation>"]
        }
        """

        result = await self.generate_reaction(instruction)

        workflow_design_status = result.get("workflow_design_status", "Initiated")
        workflow_id = result.get("workflow_id", "")
        designer_id = result.get("designer_id", "")
        design_details = result.get("design_details", "")
        target_ids = result.get("target_ids", [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("workflow_design_status", workflow_design_status)

        events = []
        for target_id in target_ids:
            workflow_event = WorkflowDesignedEvent(
                self.profile_id,
                target_id,
                workflow_id=workflow_id,
                designer_id=designer_id,
                design_details=design_details
            )
            events.append(workflow_event)

        return events

    async def allocate_tasks(self, event: Event) -> List[Event]:
        workflow_id = event.workflow_id
        design_details = event.design_details

        worker_skills = self.profile.get_data("worker_skills", [])

        instruction = f"""
        You are tasked with allocating tasks to workers based on their skills and the designed workflow.
        Workflow ID: {workflow_id}
        Design Details: {design_details}
        Worker Skills: {worker_skills}
    
        Please determine the most suitable worker(s) for the tasks and return the target_ids in the following JSON format:
        {{
            "task_list": ["<task1>", "<task2>", ...],
            "target_ids": ["<worker_id1>", "<worker_id2>", ...]
        }}
        """

        result = await self.generate_reaction(instruction)

        task_list = result.get('task_list', [])
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("task_allocation_status", "completed")

        events = []
        for target_id in target_ids:
            allocation_strategy = "skill_based"
            tasks_allocated_event = TasksAllocatedEvent(
                self.profile_id,
                str(target_id),
                task_list=task_list,
                worker_ids=target_ids,
                allocation_strategy=allocation_strategy
            )
            events.append(tasks_allocated_event)

        return events

    async def evaluate_performance(self, event: Event) -> List[Event]:
        task_results = event.task_results
        worker_ids = event.worker_ids

        received_worker_ids = self.profile.get_data("received_worker_ids", [])
        received_worker_ids.extend(worker_ids)
        self.profile.update_data("received_worker_ids", list(set(received_worker_ids)))

        observation = f"Task results: {task_results}, Worker IDs: {worker_ids}"

        worker_performance = self.profile.get_data("worker_performance", [])

        instruction = f"""Evaluate the performance based on the task results provided by the Worker Agents. 
        Use scientific management principles to analyze the effectiveness and productivity of the workers. 
        Generate a performance evaluation report, update the worker performance, and decide which ManagerAgent(s) should receive the evaluation (including yourself).
        Current worker performance: {worker_performance}
        Please return the information in the following JSON format:

        {{
        "evaluation_report": "<A detailed evaluation report>",
        "updated_worker_performance": [
            {{
                "worker_id": "<The string ID of the worker>",
                "performance": "<The performance score of the worker>"
            }}
        ],
        "target_ids": ["<The string ID(s) of the Manager agent(s)>"]
        }}
        """

        result = await self.generate_reaction(instruction, observation)

        logger.info(f"Result: {result}")

        evaluation_report = result.get('evaluation_report', "")
        updated_worker_performance = result.get('updated_worker_performance', [])
        for performance_item in updated_worker_performance:
            performance_item['worker_id'] = int(performance_item['worker_id'])
        self.profile.update_data("worker_performance", updated_worker_performance)
        logger.info(f"Updated worker performance: {updated_worker_performance}")
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            performance_event = PerformanceEvaluatedEvent(
                self.profile_id, target_id,
                evaluation_report=evaluation_report,
                evaluator_id=self.profile_id
            )
            events.append(performance_event)

        return events

    async def provide_feedback_and_incentives(self, event: Event) -> List[Event]:
        evaluation_report = event.evaluation_report
        worker_performance = self.profile.get_data("worker_performance", [])

        if not evaluation_report or not worker_performance:
            return []

        observation = f"Evaluation Report: {evaluation_report}\nWorker Performance: {worker_performance}"
        instruction = """Based on the evaluation report and worker performance metrics provided, generate feedback and an incentive plan for the workers.
        Please return the information in the following JSON format:

        {
            "feedback": "<Feedback message for the workers>",
            "incentives": ["<List of incentives for the workers>"],
            "target_ids": ["<List of worker IDs to receive feedback and incentives>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)

        feedback = result.get('feedback', "")
        incentives = result.get('incentives', [])
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("incentive_plan", incentives)

        events = []
        for target_id in target_ids:
            feedback_event = FeedbackAndIncentivesProvidedEvent(
                self.profile_id,
                target_id,
                feedback=feedback,
                incentives=incentives,
                worker_ids=target_ids
            )
            events.append(feedback_event)

        return events

    async def finalize_workflow(self, event: Event) -> List[Event]:
        adjustments = event.adjustments

        observation = f"Adjustments received: {adjustments}"
        instruction = """
        Please generate a final report summarizing the workflow adjustments and completion status.
        Ensure the report includes a summary of the adjustments and specifies the target_ids for the final event.
        The target_ids should be a list of IDs, which will include 'ENV' for the terminal event.
        Return the information in the following JSON format:

        {
        "final_report": "<Summary of adjustments and final status>",
        "target_ids": ["ENV"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        final_report = result.get('final_report', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("workflow_final_status", "completed")

        events = []
        for target_id in target_ids:
            workflow_finalized_event = WorkflowFinalizedEvent(
                self.profile_id, target_id, completion_status="completed", final_report=final_report
            )
            events.append(workflow_finalized_event)

        return events
