"""
Process Step module for OHB Simulation Model.

This module provides the ProcessStep base class, which serves as a foundation
for specific process step implementations.
"""

import logging
from abc import ABC, abstractmethod
from .process_result import ProcessResult

logger = logging.getLogger(__name__)


class ProcessStep(ABC):
    """
    Base class for process steps.
    
    A ProcessStep represents a specific step in the overall process flow,
    such as application generation, application processing, claim generation, etc.
    """
    
    def __init__(self, step_id, step_name, source_state, target_state):
        """
        Initialize with step parameters.
        
        Args:
            step_id (str): Unique identifier for the step.
            step_name (str): Descriptive name for the step.
            source_state (str): Source state identifier.
            target_state (str): Target state identifier.
        """
        self.step_id = step_id
        self.step_name = step_name
        self.source_state = source_state
        self.target_state = target_state
    
    @abstractmethod
    def execute(self, population_segments, time_manager, config_manager):
        """
        Execute process step for all segments.
        
        Args:
            population_segments (list): List of population segments to process.
            time_manager (TimeManager): Time manager for current period.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            list: List of ProcessResult objects.
        """
        pass
    
    def get_rate(self, segment, time_manager, config_manager):
        """
        Get applicable rate for segment and time.
        
        Args:
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            float: Rate value (0.0-1.0).
        """
        # Base implementation - specific steps will override as needed
        return config_manager.get_flow_rate(
            self.step_id, segment.cohort_type, segment.age_bracket.bracket_name
        )
    
    def apply_adjustments(self, base_rate, factors):
        """
        Apply adjustment factors to base rate.
        
        Args:
            base_rate (float): Base rate value.
            factors (dict): Dictionary of adjustment factors.
            
        Returns:
            float: Adjusted rate.
        """
        adjusted_rate = base_rate
        
        for factor_name, factor_value in factors.items():
            adjusted_rate *= factor_value
        
        # Ensure rate is within valid range
        return max(0.0, min(1.0, adjusted_rate))
    
    def create_process_result(self, source_state, target_state, population_count, 
                             success_count, segment_id=None, financial_impact=0):
        """
        Create result object for process execution.
        
        Args:
            source_state (str): Source state identifier.
            target_state (str): Target state identifier.
            population_count (int): Total population processed.
            success_count (int): Number of successful transitions.
            segment_id (str, optional): Population segment identifier.
            financial_impact (float, optional): Financial impact of the process.
            
        Returns:
            ProcessResult: Created process result.
        """
        result = ProcessResult(
            source_state=source_state,
            target_state=target_state,
            population_count=population_count,
            success_count=success_count,
            segment_id=segment_id,
            flow_id=self.step_id
        )
        
        if financial_impact > 0:
            # For Phase 1, assume all financial impact is program payment
            result.add_financial_impact(
                total=financial_impact,
                program_payment=financial_impact,
                patient_payment=0.0
            )
        
        return result
    
    def __str__(self):
        """Return string representation of the ProcessStep."""
        return f"ProcessStep({self.step_id}, {self.step_name}, {self.source_state} → {self.target_state})"
