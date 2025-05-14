"""
Statistics Tracker module for OHB Simulation Model.

This module provides the StatisticsTracker class, which tracks all statistics
during simulation.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class StatisticsTracker:
    """
    Tracks all statistics during simulation.
    
    The StatisticsTracker aggregates and maintains metrics throughout the
    simulation, including state metrics, flow metrics, and financial metrics.
    """
    
    def __init__(self):
        """Initialize statistics tracker with empty collections."""
        # Use defaultdict for automatic initialization of missing keys
        
        # State metrics - track population in different states
        self.state_metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        # Flow metrics - track population flows between states
        self.flow_metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        # Financial metrics - track financial impacts
        self.financial_metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        
        # Derived metrics - calculated from other metrics
        self.derived_metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    def update_state_metrics(self, regions, time_manager):
        """
        Update state metrics based on current population states.
        
        Args:
            regions (list): List of regions with population segments.
            time_manager (TimeManager): Time manager for current period.
            
        Returns:
            dict: Updated state metrics.
        """
        period = time_manager.get_current_period()
        
        # Aggregate state populations across all regions and segments
        for region in regions:
            for segment in region.population_segments:
                segment_id = segment.segment_id
                
                for state_id, state in segment.states.items():
                    population = state.get_population()
                    
                    # Update state metric at different aggregation levels
                    
                    # Overall total
                    self.state_metrics[state_id][period]['total'] += population
                    
                    # By region
                    self.state_metrics[state_id][period][f'region:{region.region_id}'] += population
                    
                    # By segment
                    self.state_metrics[state_id][period][f'segment:{segment_id}'] = population
                    
                    # By cohort type
                    self.state_metrics[state_id][period][f'cohort:{segment.cohort_type}'] += population
                    
                    # By age bracket
                    self.state_metrics[state_id][period][f'age:{segment.age_bracket.bracket_name}'] += population
        
        # Calculate derived state metrics
        self.calculate_derived_state_metrics(period)
        
        return self.state_metrics
    
    def update_flow_metric(self, flow_id, period, count, segment_id=None):
        """
        Update a specific flow metric.
        
        Args:
            flow_id (str): Flow identifier.
            period (str): Time period identifier.
            count (int): Flow count to add.
            segment_id (str, optional): Segment identifier for segmented metrics.
            
        Returns:
            int: Updated flow count.
        """
        # Update overall total
        self.flow_metrics[flow_id][period]['total'] += count
        
        # Update by segment if provided
        if segment_id:
            self.flow_metrics[flow_id][period][f'segment:{segment_id}'] += count
            
            # Extract cohort and age from segment_id if available
            # For Phase 1, use a simple parsing of segment_id format: cohort_age_region
            if '_' in segment_id:
                parts = segment_id.split('_')
                if len(parts) >= 3:
                    cohort = parts[0]
                    age = parts[1]
                    region = parts[2]
                    
                    self.flow_metrics[flow_id][period][f'cohort:{cohort}'] += count
                    self.flow_metrics[flow_id][period][f'age:{age}'] += count
                    self.flow_metrics[flow_id][period][f'region:{region}'] += count
        
        return self.flow_metrics[flow_id][period]['total']
    
    def update_financial_metric(self, metric_id, period, amount, segment_id=None):
        """
        Update a specific financial metric.
        
        Args:
            metric_id (str): Metric identifier.
            period (str): Time period identifier.
            amount (float): Amount to add.
            segment_id (str, optional): Segment identifier for segmented metrics.
            
        Returns:
            float: Updated financial amount.
        """
        # Update overall total
        self.financial_metrics[metric_id][period]['total'] += amount
        
        # Update by segment if provided
        if segment_id:
            self.financial_metrics[metric_id][period][f'segment:{segment_id}'] += amount
            
            # Extract cohort and age from segment_id if available
            if '_' in segment_id:
                parts = segment_id.split('_')
                if len(parts) >= 3:
                    cohort = parts[0]
                    age = parts[1]
                    region = parts[2]
                    
                    self.financial_metrics[metric_id][period][f'cohort:{cohort}'] += amount
                    self.financial_metrics[metric_id][period][f'age:{age}'] += amount
                    self.financial_metrics[metric_id][period][f'region:{region}'] += amount
        
        return self.financial_metrics[metric_id][period]['total']
    
    def calculate_derived_state_metrics(self, period):
        """
        Calculate metrics derived from state metrics.
        
        Args:
            period (str): Time period identifier.
            
        Returns:
            dict: Updated derived metrics.
        """
        # Calculate total_eligible_population
        eligible = self.state_metrics['eligible'][period]['total']
        re_enrollment_eligible = self.state_metrics['re_enrollment_eligible'][period]['total']
        total_eligible = eligible + re_enrollment_eligible
        
        self.derived_metrics['total_eligible_population'][period]['total'] = total_eligible
        
        # Calculate total_enrolled_population
        enrolled_inactive = self.state_metrics['enrolled_inactive'][period]['total']
        active_claimant = self.state_metrics['active_claimant'][period]['total']
        total_enrolled = enrolled_inactive + active_claimant
        
        self.derived_metrics['total_enrolled_population'][period]['total'] = total_enrolled
        
        # Calculate enrollment_rate
        if total_eligible > 0:
            enrollment_rate = total_enrolled / total_eligible
            self.derived_metrics['enrollment_rate'][period]['total'] = enrollment_rate
        
        # Repeat calculations for each segment level
        segment_keys = [k for k in self.state_metrics['eligible'][period].keys() 
                       if k.startswith('segment:')]
        
        for key in segment_keys:
            eligible_seg = self.state_metrics['eligible'][period][key]
            re_enroll_seg = self.state_metrics['re_enrollment_eligible'][period][key]
            total_eligible_seg = eligible_seg + re_enroll_seg
            
            enrolled_inactive_seg = self.state_metrics['enrolled_inactive'][period][key]
            active_claimant_seg = self.state_metrics['active_claimant'][period][key]
            total_enrolled_seg = enrolled_inactive_seg + active_claimant_seg
            
            self.derived_metrics['total_eligible_population'][period][key] = total_eligible_seg
            self.derived_metrics['total_enrolled_population'][period][key] = total_enrolled_seg
            
            if total_eligible_seg > 0:
                enrollment_rate_seg = total_enrolled_seg / total_eligible_seg
                self.derived_metrics['enrollment_rate'][period][key] = enrollment_rate_seg
        
        return self.derived_metrics
    
    def calculate_derived_financial_metrics(self, period):
        """
        Calculate metrics derived from financial metrics.
        
        Args:
            period (str): Time period identifier.
            
        Returns:
            dict: Updated derived metrics.
        """
        # Calculate expenditure_per_enrollee
        claim_expenditure = self.financial_metrics['claim_expenditure'][period]['total']
        
        # Get total of new enrollments and re-enrollments
        new_enrollments = self.flow_metrics['new_enrollments'][period]['total']
        new_re_enrollment = self.flow_metrics['new_re_enrollment'][period]['total']
        total_new_enrollees = new_enrollments + new_re_enrollment
        
        if total_new_enrollees > 0:
            expenditure_per_enrollee = claim_expenditure / total_new_enrollees
            self.derived_metrics['expenditure_per_enrollee'][period]['total'] = expenditure_per_enrollee
        
        # Calculate expenditure_per_claim
        total_new_claims = (self.flow_metrics.get('new_first_claims', {})
                           .get(period, {}).get('total', 0))
        total_new_claims += (self.flow_metrics.get('new_subsequent_claims', {})
                            .get(period, {}).get('total', 0))
        
        if total_new_claims > 0:
            expenditure_per_claim = claim_expenditure / total_new_claims
            self.derived_metrics['expenditure_per_claim'][period]['total'] = expenditure_per_claim
        
        return self.derived_metrics
    
    def update_cumulative_expenditure(self, time_manager):
        """
        Update cumulative expenditure for the current fiscal year.
        
        Args:
            time_manager (TimeManager): Time manager for current period.
            
        Returns:
            float: Updated cumulative expenditure.
        """
        period = time_manager.get_current_period()
        fiscal_year = time_manager.get_current_fiscal_year()
        
        # Reset cumulative expenditure at fiscal year start
        if time_manager.is_fiscal_year_start():
            self.financial_metrics['cumulative_expenditure'][fiscal_year]['total'] = 0.0
        
        # Add current period expenditure to cumulative
        current_expenditure = self.financial_metrics['claim_expenditure'][period]['total']
        
        self.financial_metrics['cumulative_expenditure'][fiscal_year]['total'] += current_expenditure
        
        return self.financial_metrics['cumulative_expenditure'][fiscal_year]['total']
    
    def reset_period_metrics(self):
        """
        Reset metrics that are period-specific.
        
        This is not needed in Phase 1, as we're always adding to metrics
        rather than updating in place.
        """
        pass
    
    def calculate_derived_metrics(self, time_manager):
        """
        Calculate metrics derived from other metrics.
        
        Args:
            time_manager (TimeManager): Time manager for current period.
            
        Returns:
            dict: Updated derived metrics.
        """
        period = time_manager.get_current_period()
        
        # Calculate state-derived metrics
        self.calculate_derived_state_metrics(period)
        
        # Calculate financial-derived metrics
        self.calculate_derived_financial_metrics(period)
        
        # Update cumulative expenditure
        self.update_cumulative_expenditure(time_manager)
        
        return self.derived_metrics
    
    def get_metrics_by_cohort(self, cohort_id, time_period=None):
        """
        Get metrics filtered by cohort.
        
        Args:
            cohort_id (str): Cohort identifier.
            time_period (str, optional): Specific time period to filter by.
            
        Returns:
            dict: Dictionary of metrics for the cohort.
        """
        key_filter = f'cohort:{cohort_id}'
        return self._get_filtered_metrics(key_filter, time_period)
    
    def get_metrics_by_age_bracket(self, age_bracket, time_period=None):
        """
        Get metrics filtered by age bracket.
        
        Args:
            age_bracket (str): Age bracket identifier.
            time_period (str, optional): Specific time period to filter by.
            
        Returns:
            dict: Dictionary of metrics for the age bracket.
        """
        key_filter = f'age:{age_bracket}'
        return self._get_filtered_metrics(key_filter, time_period)
    
    def get_metrics_by_region(self, region_id, time_period=None):
        """
        Get metrics filtered by region.
        
        Args:
            region_id (str): Region identifier.
            time_period (str, optional): Specific time period to filter by.
            
        Returns:
            dict: Dictionary of metrics for the region.
        """
        key_filter = f'region:{region_id}'
        return self._get_filtered_metrics(key_filter, time_period)
    
    def get_metrics_by_segment(self, segment_id, time_period=None):
        """
        Get metrics filtered by segment.
        
        Args:
            segment_id (str): Segment identifier.
            time_period (str, optional): Specific time period to filter by.
            
        Returns:
            dict: Dictionary of metrics for the segment.
        """
        key_filter = f'segment:{segment_id}'
        return self._get_filtered_metrics(key_filter, time_period)
    
    def _get_filtered_metrics(self, key_filter, time_period=None):
        """
        Get metrics filtered by a specific key and optional time period.
        
        Args:
            key_filter (str): Key to filter by.
            time_period (str, optional): Specific time period to filter by.
            
        Returns:
            dict: Dictionary of filtered metrics.
        """
        filtered_metrics = {
            'state_metrics': {},
            'flow_metrics': {},
            'financial_metrics': {},
            'derived_metrics': {}
        }
        
        # Filter state metrics
        for state_id, periods in self.state_metrics.items():
            filtered_metrics['state_metrics'][state_id] = {}
            
            for period, keys in periods.items():
                if time_period and period != time_period:
                    continue
                    
                if key_filter in keys:
                    filtered_metrics['state_metrics'][state_id][period] = keys[key_filter]
        
        # Filter flow metrics
        for flow_id, periods in self.flow_metrics.items():
            filtered_metrics['flow_metrics'][flow_id] = {}
            
            for period, keys in periods.items():
                if time_period and period != time_period:
                    continue
                    
                if key_filter in keys:
                    filtered_metrics['flow_metrics'][flow_id][period] = keys[key_filter]
        
        # Filter financial metrics
        for metric_id, periods in self.financial_metrics.items():
            filtered_metrics['financial_metrics'][metric_id] = {}
            
            for period, keys in periods.items():
                if time_period and period != time_period:
                    continue
                    
                if key_filter in keys:
                    filtered_metrics['financial_metrics'][metric_id][period] = keys[key_filter]
        
        # Filter derived metrics
        for metric_id, periods in self.derived_metrics.items():
            filtered_metrics['derived_metrics'][metric_id] = {}
            
            for period, keys in periods.items():
                if time_period and period != time_period:
                    continue
                    
                if key_filter in keys:
                    filtered_metrics['derived_metrics'][metric_id][period] = keys[key_filter]
        
        return filtered_metrics
    
    def get_metric_history(self, metric_type, metric_id, key_filter='total'):
        """
        Get historical values for a specific metric.
        
        Args:
            metric_type (str): Type of metric ('state', 'flow', 'financial', 'derived').
            metric_id (str): Metric identifier.
            key_filter (str, optional): Key to filter by, defaults to 'total'.
            
        Returns:
            dict: Dictionary mapping periods to metric values.
        """
        history = {}
        
        if metric_type == 'state':
            metric_data = self.state_metrics.get(metric_id, {})
        elif metric_type == 'flow':
            metric_data = self.flow_metrics.get(metric_id, {})
        elif metric_type == 'financial':
            metric_data = self.financial_metrics.get(metric_id, {})
        elif metric_type == 'derived':
            metric_data = self.derived_metrics.get(metric_id, {})
        else:
            return history
        
        for period, keys in metric_data.items():
            if key_filter in keys:
                history[period] = keys[key_filter]
        
        return history
