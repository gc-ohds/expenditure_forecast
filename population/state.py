"""
Process State module for OHB Simulation Model.

This module provides the ProcessState class, which represents a state
in the process flow and tracks the population in that state.
"""

import logging

logger = logging.getLogger(__name__)


class ProcessState:
    """
    Represents a state in the process flow.
    
    A ProcessState tracks the population count in a specific state within
    the simulation, such as 'eligible', 'applied', 'enrolled_inactive', etc.
    """
    
    def __init__(self, state_id, state_name, reset_on_fiscal_year=False):
        """
        Initialize with state identifier and name.
        
        Args:
            state_id (str): Unique identifier for the state.
            state_name (str): Descriptive name of the state.
            reset_on_fiscal_year (bool): Whether state population resets at fiscal year change.
        """
        self.state_id = state_id
        self.state_name = state_name
        self.population = 0
        self.reset_on_fiscal_year = reset_on_fiscal_year
        
        # For tracking historical population values
        self.historical_values = {}
    
    def get_population(self):
        """
        Get current population in this state.
        
        Returns:
            int: Current population count.
        """
        return self.population
    
    def update_population(self, delta):
        """
        Update population by delta amount.
        
        Args:
            delta (int): Amount to change population by (positive or negative).
            
        Returns:
            int: New population count.
        """
        # Check if delta would make population negative
        if self.population + delta < 0:
            logger.warning(
                f"Attempted to decrease population of {self.state_name} below zero. "
                f"Current: {self.population}, Delta: {delta}"
            )
            # Limit reduction to available population
            delta = -self.population
        
        self.population += delta
        return self.population
    
    def set_population(self, count):
        """
        Set population to a specific count.
        
        Args:
            count (int): New population count.
            
        Returns:
            int: New population count.
        """
        if count < 0:
            logger.warning(
                f"Attempted to set negative population for {self.state_name}. "
                f"Requested: {count}"
            )
            count = 0
            
        self.population = count
        return self.population
    
    def reset_population(self):
        """
        Reset population to zero.
        
        Returns:
            int: Previous population count before reset.
        """
        previous = self.population
        self.population = 0
        return previous
    
    def record_historical_value(self, period_id):
        """
        Record current population value for historical tracking.
        
        Args:
            period_id (str): Identifier for the time period.
        """
        self.historical_values[period_id] = self.population
    
    def get_historical_value(self, period_id):
        """
        Get historical population value for a period.
        
        Args:
            period_id (str): Identifier for the time period.
            
        Returns:
            int: Historical population count, or None if not recorded.
        """
        return self.historical_values.get(period_id)
    
    def should_reset_on_fiscal_year(self):
        """
        Check if state should reset on fiscal year change.
        
        Returns:
            bool: True if population should reset at fiscal year change.
        """
        return self.reset_on_fiscal_year
    
    def __str__(self):
        """Return string representation of the ProcessState."""
        return f"ProcessState({self.state_id}, population={self.population})"
