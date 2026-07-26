"""Execution layer: turns an ExecutionPlan into real ActionResults."""

from .plan_executor import PlanExecutionError, PlanExecutor

__all__ = ["PlanExecutor", "PlanExecutionError"]
