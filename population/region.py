"""
Region module for OHB Simulation Model.

This module provides the Region class, which represents a geographic region
with population segments.
"""

import logging

logger = logging.getLogger(__name__)


class Region:
    """
    Represents a geographic region with population segments.
    
    A Region groups together population segments that share geographical
    characteristics and can have region-specific adjustment factors.
    """
    
    def __init__(self, region_id, region_name):
        """
        Initialize with region identifier and name.
        
        Args:
            region_id (str): Unique identifier for the region.
            region_name (str): Descriptive name for the region.
        """
        self.region_id = region_id
        self.region_name = region_name
        self.population_segments = []
        self.regional_factors = {}  # For adjustment factors specific to this region
    
    def add_population_segment(self, segment):
        """
        Add a population segment to the region.
        
        Args:
            segment (PopulationSegment): Population segment to add.
            
        Returns:
            PopulationSegment: The added segment.
        """
        if segment.region_id != self.region_id:
            logger.warning(
                f"Adding segment with mismatched region_id {segment.region_id} "
                f"to region {self.region_id}"
            )
            # Update the segment's region_id to match this region
            segment.region_id = self.region_id
        
        self.population_segments.append(segment)
        return segment
    
    def initialize_segments(self, segment_definitions, state_definitions):
        """
        Initialize population segments from definitions.
        
        Args:
            segment_definitions (list): List of segment definitions.
            state_definitions (dict): Dictionary of state definitions.
            
        Returns:
            list: List of initialized population segments.
        """
        from .segment import PopulationSegment, AgeBracket
        
        # Filter segment definitions for this region
        region_segments = [s for s in segment_definitions if s.get('region_id') == self.region_id]
        
        for segment_def in region_segments:
            # Create age bracket
            age_bracket = AgeBracket(
                age_min=segment_def.get('age_min', 0),
                age_max=segment_def.get('age_max', 100),
                bracket_name=segment_def.get('age_bracket_name', 'Default'),
                eligibility_start_date=segment_def.get('eligibility_start_date')
            )
            
            # Create population segment
            segment = PopulationSegment(
                segment_id=segment_def.get('segment_id'),
                cohort_type=segment_def.get('cohort_type', 'general'),
                age_bracket=age_bracket,
                region_id=self.region_id,
                population_size=segment_def.get('population_size', 0)
            )
            
            # Initialize states for segment
            segment.initialize_states(state_definitions)
            
            # Add segment to region
            self.add_population_segment(segment)
        
        return self.population_segments
    
    def process_population_flows(self, time_manager, config_manager):
        """
        Process all population flows for the current time period.
        
        In Phase 1, we'll implement a simple flow processing that moves
        population between states based on flow rates.
        
        Args:
            time_manager (TimeManager): Manager for the current time.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            list: List of process results from flow processing.
        """
        from population.flow import PopulationFlow
        
        flow_definitions = config_manager.get_flow_definitions()
        flow_results = []
        
        # Process each flow for each segment
        for segment in self.population_segments:
            for flow_id, flow_def in flow_definitions.items():
                source_id = flow_def.get('source')
                target_id = flow_def.get('target')
                
                # Create flow
                flow = PopulationFlow(
                    flow_id=flow_id,
                    source_state=source_id,
                    target_state=target_id
                )
                
                # Calculate and apply flow
                result = flow.apply_flow(
                    population_segment=segment,
                    config_manager=config_manager,
                    time_manager=time_manager
                )
                
                if result and result.success_count > 0:
                    flow_results.append(result)
        
        return flow_results
    
    def calculate_regional_statistics(self):
        """
        Calculate region-level statistics.
        
        Returns:
            dict: Dictionary of regional statistics.
        """
        stats = {
            'region_id': self.region_id,
            'region_name': self.region_name,
            'total_population': self.get_total_population(),
            'segment_count': len(self.population_segments),
            'state_populations': {}
        }
        
        # Aggregate state populations across all segments
        if self.population_segments:
            # Get state IDs from first segment
            state_ids = list(self.population_segments[0].states.keys())
            
            for state_id in state_ids:
                total = sum(segment.get_state_population(state_id) 
                           for segment in self.population_segments)
                stats['state_populations'][state_id] = total
        
        return stats
    
    def apply_regional_factors(self, base_rates, factor_type):
        """
        Apply regional adjustment factors to base rates.
        
        Args:
            base_rates (dict): Dictionary of base rates to adjust.
            factor_type (str): Type of adjustment factor to apply.
            
        Returns:
            dict: Dictionary of adjusted rates.
        """
        # In Phase 1, implement a simple adjustment
        adjusted_rates = base_rates.copy()
        
        # Apply regional factors if available
        if factor_type in self.regional_factors:
            adjustment = self.regional_factors[factor_type]
            
            for rate_id, rate in adjusted_rates.items():
                if isinstance(rate, (int, float)):
                    adjusted_rates[rate_id] = rate * adjustment
        
        return adjusted_rates
    
    def get_total_population(self):
        """
        Get total population in the region.
        
        Returns:
            int: Total population across all segments.
        """
        return sum(segment.population_size for segment in self.population_segments)
    
    def get_segment_by_id(self, segment_id):
        """
        Get population segment by its identifier.
        
        Args:
            segment_id (str): Segment identifier to find.
            
        Returns:
            PopulationSegment: Found segment, or None if not found.
        """
        for segment in self.population_segments:
            if segment.segment_id == segment_id:
                return segment
        return None
    
    def record_state_history(self, period_id):
        """
        Record historical state values for all segments.
        
        Args:
            period_id (str): Identifier for the time period.
        """
        for segment in self.population_segments:
            segment.record_state_history(period_id)
    
    def reset_annual_states(self):
        """
        Reset states that should reset on fiscal year change for all segments.
        
        Returns:
            dict: Dictionary mapping segment_id to reset results.
        """
        reset_results = {}
        
        for segment in self.population_segments:
            reset_populations = segment.reset_annual_states()
            if reset_populations:
                reset_results[segment.segment_id] = reset_populations
        
        return reset_results
    
    def __str__(self):
        """Return string representation of the Region."""
        return f"Region({self.region_id}, {self.region_name}, segments={len(self.population_segments)})"
