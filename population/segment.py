"""
Population Segment module for OHB Simulation Model.

This module provides the AgeBracket and PopulationSegment classes, which
represent demographic segments of the population being modeled.
"""

import logging
from datetime import date
from .state import ProcessState

logger = logging.getLogger(__name__)


class AgeBracket:
    """
    Represents an age range for population segmentation.
    
    An AgeBracket defines a specific age range that can be used for
    targeting specific demographic groups in the simulation.
    """
    
    def __init__(self, age_min, age_max, bracket_name, eligibility_start_date=None):
        """
        Initialize with age range and name.
        
        Args:
            age_min (int): Minimum age (inclusive).
            age_max (int): Maximum age (inclusive).
            bracket_name (str): Descriptive name for the age bracket.
            eligibility_start_date (date, optional): Date when this age bracket
                becomes eligible. If None, eligibility determined by rollout schedule.
        """
        self.age_min = age_min
        self.age_max = age_max
        self.bracket_name = bracket_name
        self.eligibility_start_date = eligibility_start_date
    
    def is_eligible(self, current_date):
        """
        Check if age bracket is eligible at current date.
        
        Args:
            current_date (date): Current date in the simulation.
            
        Returns:
            bool: True if age bracket is eligible at the current date.
        """
        if self.eligibility_start_date is None:
            # If no specific eligibility date, assume eligible
            return True
        
        return current_date >= self.eligibility_start_date
    
    def __str__(self):
        """Return string representation of the AgeBracket."""
        if self.age_max >= 100:
            return f"{self.bracket_name} ({self.age_min}+)"
        return f"{self.bracket_name} ({self.age_min}-{self.age_max})"


class PopulationSegment:
    """
    Represents a demographic segment of the population.
    
    A PopulationSegment defines a specific demographic group with characteristics
    such as cohort type and age bracket. It tracks the population across different
    process states.
    """
    
    def __init__(self, segment_id, cohort_type, age_bracket, region_id, population_size):
        """
        Initialize with segment parameters.
        
        Args:
            segment_id (str): Unique identifier for the segment.
            cohort_type (str): Type of cohort (e.g., 'general', 'pwd', etc.).
            age_bracket (AgeBracket): Age bracket for this segment.
            region_id (str): Identifier for the region this segment belongs to.
            population_size (int): Total population size for this segment.
        """
        self.segment_id = segment_id
        self.cohort_type = cohort_type
        self.age_bracket = age_bracket
        self.region_id = region_id
        self.population_size = population_size
        self.states = {}  # Maps state_id to ProcessState objects
        
        # For Phase 1, we'll use a simple income distribution (can be extended later)
        self.income_distribution = {"low": 0.3, "medium": 0.5, "high": 0.2}
    
    def initialize_states(self, state_definitions):
        """
        Initialize all process states for this segment.
        
        Args:
            state_definitions (dict): Dictionary of state definitions from configuration.
            
        Returns:
            dict: Dictionary of initialized ProcessState objects.
        """
        # Log the states we're initializing
        logger.debug(f"Initializing states for segment {self.segment_id}")
        logger.debug(f"State definitions: {state_definitions}")
        
        for state_key, state_def in state_definitions.items():
            # Get the inner ID from the state definition
            state_id = state_def['id']
            
            # Log the state we're creating
            logger.debug(f"Creating state {state_id} from definition {state_key}")
            
            reset_on_fiscal_year = state_def.get('reset_on_fiscal_year', False)
            state = ProcessState(
                state_id=state_id,  # Use the inner ID ("eligible")
                state_name=state_def['name'],
                reset_on_fiscal_year=reset_on_fiscal_year
            )
            
            # Store using the inner ID
            self.states[state_id] = state
        
        # Initially place entire population in eligible state
        if 'eligible' in self.states:
            self.states['eligible'].set_population(self.population_size)
            logger.debug(f"Set initial population for 'eligible' state: {self.population_size}")
        else:
            logger.warning(f"'eligible' state not found for segment {self.segment_id}")
        
        # Verify we have all required states
        self.verify_required_states()
        
        return self.states
    
    def verify_required_states(self):
        """
        Verify that all required states are initialized.
        
        Returns:
            bool: True if all required states are present, False otherwise.
        """
        required_states = ['eligible', 're_enrollment_eligible', 'applied', 
                          'enrolled_inactive', 'active_claimant']
        
        missing_states = [state for state in required_states if state not in self.states]
        
        if missing_states:
            logger.error(f"Segment {self.segment_id} missing required states: {missing_states}")
            logger.error(f"Available states: {list(self.states.keys())}")
            return False
        
        return True
    
    def get_state_population(self, state_id):
        """
        Get population count in specific state.
        
        Args:
            state_id (str): Identifier for the state.
            
        Returns:
            int: Population count in the specified state.
        """
        if state_id in self.states:
            return self.states[state_id].get_population()
        else:
            logger.warning(f"Requested unknown state {state_id} in segment {self.segment_id}")
            return 0
    
    def transition_population(self, from_state_id, to_state_id, count):
        """
        Move population between states.
        
        Args:
            from_state_id (str): Source state identifier.
            to_state_id (str): Target state identifier.
            count (int): Number of population to transition.
            
        Returns:
            tuple: (success_count, source_state, target_state)
        """
        print(f"DEBUG TRANSITION: {from_state_id} → {to_state_id}, count={count}")
        
        if from_state_id not in self.states:
            print(f"DEBUG: Source state {from_state_id} not found in {list(self.states.keys())}")
            return 0, None, None
        
        if to_state_id not in self.states:
            print(f"DEBUG: Target state {to_state_id} not found in {list(self.states.keys())}")
            return 0, None, None
        
        source_state = self.states[from_state_id]
        target_state = self.states[to_state_id]
        
        available = source_state.get_population()
        print(f"DEBUG: Available population in {from_state_id}: {available}")
        
        if count > available:
            count = available
            print(f"DEBUG: Reducing count to available: {count}")
        
        if count <= 0:
            print(f"DEBUG: No population to move")
            return 0, source_state, target_state
        
        # BEFORE transition
        print(f"DEBUG BEFORE: {from_state_id}={source_state.get_population()}, {to_state_id}={target_state.get_population()}")
        
        # Perform the transition
        source_state.update_population(-count)
        target_state.update_population(count)
        
        # AFTER transition
        print(f"DEBUG AFTER: {from_state_id}={source_state.get_population()}, {to_state_id}={target_state.get_population()}")
        
        return count, source_state, target_state
    
    def record_state_history(self, period_id):
        """
        Record historical values for all states.
        
        Args:
            period_id (str): Identifier for the time period.
        """
        for state in self.states.values():
            state.record_historical_value(period_id)
    
    def reset_annual_states(self):
        """
        Reset states that should reset on fiscal year change.
        
        Returns:
            dict: Dictionary mapping state_id to population count before reset.
        """
        reset_populations = {}
        
        for state_id, state in self.states.items():
            if state.should_reset_on_fiscal_year():
                previous = state.reset_population()
                reset_populations[state_id] = previous
                
                # If there's a re-enrollment state, move reset population there
                if 're_enrollment_eligible' in self.states and previous > 0:
                    self.states['re_enrollment_eligible'].update_population(previous)
        
        return reset_populations
    
    def get_currently_eligible_population(self, current_date, rollout_schedule=None):
        """
        Get population eligible at current date.
        
        Args:
            current_date (date): Current date in the simulation.
            rollout_schedule (RolloutSchedule, optional): Rollout schedule for eligibility check.
            
        Returns:
            int: Eligible population count.
        """
        # Check age bracket eligibility
        if not self.age_bracket.is_eligible(current_date):
            return 0
        
        # Check rollout schedule eligibility if provided
        if rollout_schedule is not None:
            # Get age from segment's age bracket (midpoint for simplicity)
            age = (self.age_bracket.age_min + self.age_bracket.age_max) // 2
            
            # Check if cohort and age are eligible at current date
            if not rollout_schedule.is_cohort_age_eligible(
                self.cohort_type, age, current_date
            ):
                return 0
        
        # Return eligible population count
        eligible_count = self.get_state_population('eligible')
        re_enroll_count = self.get_state_population('re_enrollment_eligible')
        
        return eligible_count + re_enroll_count
    
    def get_population_by_income_bracket(self, bracket_id):
        """
        Get population count in specific income bracket.
        
        Args:
            bracket_id (str): Income bracket identifier.
            
        Returns:
            int: Population count in the specified income bracket.
        """
        if bracket_id not in self.income_distribution:
            return 0
        
        # In Phase 1, return a simple proportion of total segment population
        return int(self.population_size * self.income_distribution[bracket_id])
    
    def __str__(self):
        """Return string representation of the PopulationSegment."""
        return (f"PopulationSegment({self.segment_id}, {self.cohort_type}, "
                f"{self.age_bracket}, population={self.population_size})")