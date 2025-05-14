"""
Population Flow module for OHB Simulation Model.

This module provides the PopulationFlow class, which represents
flow of population between states.
"""

import logging
import random
from process.process_result import ProcessResult

logger = logging.getLogger(__name__)


class PopulationFlow:
    """
    Represents flow of population between states.
    
    A PopulationFlow models the transition of population between two states
    based on configured flow rates and distributions.
    """
    
    def __init__(self, flow_id, source_state, target_state, flow_rate=None, rate_distribution=None):
        """
        Initialize with flow parameters.
        
        Args:
            flow_id (str): Unique identifier for the flow.
            source_state (str): Source state identifier.
            target_state (str): Target state identifier.
            flow_rate (float, optional): Fixed flow rate (0.0-1.0).
            rate_distribution (dict, optional): Distribution parameters for variable rate.
        """
        self.flow_id = flow_id
        self.source_state = source_state
        self.target_state = target_state
        self.flow_rate = flow_rate
        self.rate_distribution = rate_distribution
    
    def calculate_flow(self, population_size, config_manager, segment, time_manager):
        """
        Calculate flow amount for current period.
        
        Args:
            population_size (int): Size of source population.
            config_manager (ConfigurationManager): Configuration manager.
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            
        Returns:
            int: Calculated flow amount.
        """
        # Get flow rate (fixed or from configuration)
        rate = self.get_flow_rate(config_manager, segment, time_manager)
        
        # Apply distribution if available
        if self.rate_distribution:
            # Simple implementation for Phase 1
            # In future phases, use proper statistical distributions
            variation = random.uniform(
                -self.rate_distribution.get('variance', 0.1),
                self.rate_distribution.get('variance', 0.1)
            )
            rate = max(0.0, min(1.0, rate + variation))
        
        # Calculate flow amount and round to integer
        flow_amount = int(population_size * rate)
        return flow_amount
    
    def apply_flow(self, population_segment, config_manager, time_manager):
        """
        Apply calculated flow to population segment.
        
        Args:
            population_segment (PopulationSegment): Target population segment.
            config_manager (ConfigurationManager): Configuration manager.
            time_manager (TimeManager): Time manager.
            
        Returns:
            ProcessResult: Result of the flow application.
        """
        # Get source population
        source_population = population_segment.get_state_population(self.source_state)
        
        if source_population <= 0:
            return None  # No population to flow
        
        # Calculate flow amount
        flow_amount = self.calculate_flow(
            source_population, config_manager, population_segment, time_manager
        )
        
        if flow_amount <= 0:
            return None  # No flow to apply
        
        # Perform the transition
        success_count, source, target = population_segment.transition_population(
            self.source_state, self.target_state, flow_amount
        )
        
        if success_count <= 0:
            return None  # No successful transitions
        
        # Create process result
        result = ProcessResult(
            source_state=self.source_state,
            target_state=self.target_state,
            population_count=source_population,
            success_count=success_count,
            failure_count=0,
            segment_id=population_segment.segment_id,
            flow_id=self.flow_id
        )
        
        return result
    
    def get_flow_rate(self, config_manager, segment, time_manager):
        """
        Get applicable flow rate for segment and time.
        
        Args:
            config_manager (ConfigurationManager): Configuration manager.
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            
        Returns:
            float: Flow rate value (0.0-1.0).
        """
        # If fixed rate provided, use it
        if self.flow_rate is not None:
            return self.flow_rate
        
        # Get rate from configuration
        rate = config_manager.get_flow_rate(
            self.flow_id, segment.cohort_type, segment.age_bracket.bracket_name
        )
        
        # In Phase 1, implement a simple time-based adjustment
        # Later phases can implement more sophisticated adjustments
        month = time_manager.current_date.month
        
        # Simple seasonal adjustment - higher rates in Q1 and Q3
        if month in [1, 2, 3, 7, 8, 9]:
            rate = rate * 1.1
        
        return min(1.0, rate)
    
    def __str__(self):
        """Return string representation of the PopulationFlow."""
        return f"PopulationFlow({self.flow_id}, {self.source_state} → {self.target_state})"
