"""
Process Result module for OHB Simulation Model.

This module provides the ProcessResult class, which represents
the result of a process step execution.
"""

import logging

logger = logging.getLogger(__name__)


class ProcessResult:
    """
    Represents the result of a process step execution.
    
    A ProcessResult captures the outcome of a process step, including the
    population movement, success/failure counts, and any financial impacts.
    """
    
    def __init__(self, source_state, target_state, population_count, 
                success_count=0, failure_count=0, segment_id=None, flow_id=None,
                region_id=None, cohort_type=None, age_bracket=None):
        """
        Initialize with process result data.
        
        Args:
            source_state (str): Source state identifier.
            target_state (str): Target state identifier.
            population_count (int): Total population processed.
            success_count (int, optional): Number of successful transitions.
            failure_count (int, optional): Number of failed transitions.
            segment_id (str, optional): Population segment identifier.
            flow_id (str, optional): Flow identifier.
            region_id (str, optional): Region identifier.
            cohort_type (str, optional): Cohort type.
            age_bracket (str, optional): Age bracket.
        """
        self.source_state = source_state
        self.target_state = target_state
        self.population_count = population_count
        self.success_count = success_count
        self.failure_count = failure_count
        self.segment_id = segment_id
        self.flow_id = flow_id
        self.region_id = region_id
        self.cohort_type = cohort_type
        self.age_bracket = age_bracket
        
        # Financial impact data (to be set later if applicable)
        self.financial_impact = 0.0
        self.program_payment = 0.0
        self.patient_payment = 0.0
        
        # Service mix data (to be set later if applicable)
        self.service_mix = {}  # Maps service_code to count
    
    def add_financial_impact(self, total, program_payment, patient_payment):
        """
        Add financial impact data to result.
        
        Args:
            total (float): Total financial impact.
            program_payment (float): Program payment portion.
            patient_payment (float): Patient payment portion.
            
        Returns:
            self: For method chaining.
        """
        self.financial_impact = total
        self.program_payment = program_payment
        self.patient_payment = patient_payment
        return self
    
    def add_service_mix(self, service_mix):
        """
        Add service mix data to result.
        
        Args:
            service_mix (dict): Dictionary mapping service_code to count.
            
        Returns:
            self: For method chaining.
        """
        self.service_mix = service_mix
        return self
    
    def add_to_statistics(self, statistics_tracker, time_manager):
        """
        Add this result to statistics tracker.
        
        Args:
            statistics_tracker (StatisticsTracker): Statistics tracker to update.
            time_manager (TimeManager): Time manager for current period.
        """
        # For Phase 1, implement a simple update of basic metrics
        period = time_manager.get_current_period()
        
        # Update flow metrics
        if self.flow_id:
            statistics_tracker.update_flow_metric(
                flow_id=self.flow_id, 
                period=period, 
                count=self.success_count, 
                segment_id=self.segment_id,
                region_id=self.region_id,
                cohort_type=self.cohort_type,
                age_bracket=self.age_bracket
            )
        
        # Update financial metrics if applicable
        if self.financial_impact > 0:
            statistics_tracker.update_financial_metric(
                metric_id='claim_expenditure',
                period=period, 
                amount=self.financial_impact, 
                segment_id=self.segment_id,
                region_id=self.region_id,
                cohort_type=self.cohort_type,
                age_bracket=self.age_bracket
            )
            
            if self.program_payment > 0:
                statistics_tracker.update_financial_metric(
                    metric_id='program_expenditure',
                    period=period, 
                    amount=self.program_payment, 
                    segment_id=self.segment_id,
                    region_id=self.region_id,
                    cohort_type=self.cohort_type,
                    age_bracket=self.age_bracket
                )
            
            if self.patient_payment > 0:
                statistics_tracker.update_financial_metric(
                    metric_id='patient_expenditure',
                    period=period, 
                    amount=self.patient_payment, 
                    segment_id=self.segment_id,
                    region_id=self.region_id,
                    cohort_type=self.cohort_type,
                    age_bracket=self.age_bracket
                )
    
    def __str__(self):
        """Return string representation of the ProcessResult."""
        result = (f"ProcessResult({self.source_state} → {self.target_state}, "
                 f"population={self.population_count}, "
                 f"success={self.success_count}, "
                 f"failure={self.failure_count})")
        
        if self.segment_id:
            result += f", segment={self.segment_id}"
        
        if self.flow_id:
            result += f", flow={self.flow_id}"
        
        if self.financial_impact > 0:
            result += f", financial_impact={self.financial_impact:.2f}"
        
        return result
