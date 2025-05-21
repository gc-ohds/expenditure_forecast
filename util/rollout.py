"""
Rollout Schedule module for OHB Simulation Model.

This module provides the RolloutSchedule and RolloutPhase classes,
which manage the program rollout schedule and eligibility determination.
"""

import logging
import datetime
from datetime import date

logger = logging.getLogger(__name__)


class RolloutPhase:
    """
    Represents a phase in the rollout schedule.
    
    A RolloutPhase defines when a specific cohort and age bracket
    becomes eligible for the program.
    """
    
    def __init__(self, phase_id, cohort_id, age_min, age_max, start_date, description=''):
        """
        Initialize with phase parameters.
        
        Args:
            phase_id (str): Unique identifier for the phase.
            cohort_id (str): Cohort type identifier (e.g., 'seniors', 'pwd').
            age_min (int): Minimum age for eligibility.
            age_max (int): Maximum age for eligibility.
            start_date (date): Date when this phase becomes active.
            description (str, optional): Description of the phase.
        """
        self.phase_id = phase_id
        self.cohort_id = cohort_id
        self.age_min = age_min
        self.age_max = age_max
        
        # Convert string date to datetime.date if needed
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        self.start_date = start_date
        
        self.description = description
    
    def is_active(self, current_date):
        """
        Check if phase is active at current date.
        
        Args:
            current_date (date): Current date to check against.
            
        Returns:
            bool: True if the phase is active at the current date.
        """
        # Convert string date to datetime.date if needed
        if isinstance(current_date, str):
            current_date = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
            
        return current_date >= self.start_date
    
    def matches_cohort_and_age(self, cohort_id, age):
        """
        Check if the phase matches the specified cohort and age.
        
        Args:
            cohort_id (str): Cohort identifier to check.
            age (int): Age to check.
            
        Returns:
            bool: True if the phase matches the cohort and age.
        """
        return (self.cohort_id == cohort_id and 
                age >= self.age_min and 
                age <= self.age_max)
    
    def to_dict(self):
        """
        Convert to dictionary representation.
        
        Returns:
            dict: Dictionary representation of the phase.
        """
        return {
            'phase_id': self.phase_id,
            'cohort_id': self.cohort_id,
            'age_min': self.age_min,
            'age_max': self.age_max,
            'start_date': self.start_date.isoformat(),
            'description': self.description
        }
    
    def __str__(self):
        """Return string representation of the RolloutPhase."""
        return (f"RolloutPhase({self.phase_id}, {self.cohort_id}, "
                f"ages {self.age_min}-{self.age_max}, start: {self.start_date})")


class RolloutSchedule:
    """
    Manages program rollout schedule.
    
    The RolloutSchedule determines when different population segments
    become eligible for the program based on defined phases.
    """
    
    def __init__(self):
        """Initialize empty rollout schedule."""
        self.phases = []
    
    def load_from_config(self, config_manager):
        """
        Load rollout schedule from configuration.
        
        Args:
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            bool: True if loading was successful, False otherwise.
        """
        rollout_config = config_manager.get_rollout_schedule()
        
        if not rollout_config:
            logger.warning("No rollout schedule configuration found")
            
            # Create a default rollout that makes everything eligible
            # This ensures the simulation can still run without a rollout schedule
            default_phase = RolloutPhase(
                phase_id="default",
                cohort_id="ALL",
                age_min=0,
                age_max=120,
                start_date=config_manager.get_simulation_parameters().get(
                    'start_date', "2025-04-01"),
                description="Default rollout (all cohorts eligible)"
            )
            self.add_phase(default_phase)
            logger.info("Created default rollout schedule (all cohorts eligible)")
            return True
        
        # Clear existing phases
        self.phases = []
        
        # Add phases from configuration
        for phase_config in rollout_config:
            phase = RolloutPhase(
                phase_id=phase_config.get('phase_id'),
                cohort_id=phase_config.get('cohort_id'),
                age_min=phase_config.get('age_min', 0),
                age_max=phase_config.get('age_max', 120),
                start_date=phase_config.get('start_date'),
                description=phase_config.get('description', '')
            )
            self.add_phase(phase)
        
        logger.info(f"Loaded {len(self.phases)} rollout phases")
        return True
    
    def get_eligible_cohorts(self, current_date):
        """
        Get cohorts eligible at current date.
        
        Args:
            current_date (date): Current date in the simulation.
            
        Returns:
            list: List of eligible cohort IDs.
        """
        eligible_cohorts = set()
        
        for phase in self.phases:
            if phase.is_active(current_date):
                eligible_cohorts.add(phase.cohort_id)
        
        return list(eligible_cohorts)
    
    def get_eligible_age_brackets(self, cohort_id, current_date):
        """
        Get eligible age brackets for cohort at current date.
        
        Args:
            cohort_id (str): Cohort identifier.
            current_date (date): Current date in the simulation.
            
        Returns:
            list: List of tuples (age_min, age_max) for eligible age ranges.
        """
        eligible_brackets = []
        
        for phase in self.phases:
            if phase.is_active(current_date) and phase.cohort_id == cohort_id:
                eligible_brackets.append((phase.age_min, phase.age_max))
        
        return eligible_brackets
    
    def is_cohort_age_eligible(self, cohort_id, age, current_date):
        """
        Check if a specific cohort and age is eligible at current date.
        
        Args:
            cohort_id (str): Cohort identifier.
            age (int): Age to check.
            current_date (date): Current date in the simulation.
            
        Returns:
            bool: True if eligible, False otherwise.
        """
        for phase in self.phases:
            if (phase.is_active(current_date) and 
                phase.matches_cohort_and_age(cohort_id, age)):
                return True
        
        return False
    
    def add_phase(self, phase):
        """
        Add rollout phase to schedule.
        
        Args:
            phase (RolloutPhase): Phase to add.
            
        Returns:
            RolloutPhase: The added phase.
        """
        self.phases.append(phase)
        return phase
    
    def get_phases_by_cohort(self, cohort_id):
        """
        Get phases for a specific cohort.
        
        Args:
            cohort_id (str): Cohort identifier.
            
        Returns:
            list: List of RolloutPhase objects for the cohort.
        """
        return [phase for phase in self.phases if phase.cohort_id == cohort_id]
    
    def __str__(self):
        """Return string representation of the RolloutSchedule."""
        return f"RolloutSchedule(phases={len(self.phases)})"