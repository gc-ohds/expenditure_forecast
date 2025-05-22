"""
Application module for OHB Simulation Model.

This module provides the ApplicationGenerator and ApplicationProcessor classes,
which handle generating applications from eligible populations and processing
applications into enrollments.
"""

import logging
import random
import math
from .process_step import ProcessStep
from .process_result import ProcessResult

logger = logging.getLogger(__name__)


class ApplicationGenerator(ProcessStep):
    """
    Generates applications for eligible population.
    
    The ApplicationGenerator is responsible for generating applications
    from the eligible population based on configurable rates.
    """
    
    def __init__(self, source_state, target_state):
        """
        Initialize application generator.
        
        Args:
            source_state (str): Source state identifier.
            target_state (str): Target state identifier.
        """
        super().__init__("application_generator", "Application Generation", 
                         source_state, target_state)
        self.application_rates_by_segment = {}
        self.re_enrollment_rates_by_segment = {}
        self.application_rate_distributions = {}
    
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
        results = []
        
        # Process each population segment
        for segment in population_segments:
            # Check if segment has a valid rollout phase
            # if not self._is_segment_eligible(segment, time_manager, config_manager):
            #     continue
            
            # Generate new applications
            new_apps = self.generate_new_applications(segment, time_manager, config_manager)
            
            if new_apps > 0:
                # Create result for new applications
                result = self.create_process_result(
                    source_state=self.source_state,
                    target_state=self.target_state,
                    population_count=segment.get_state_population(self.source_state),
                    success_count=new_apps,
                    segment_id=segment.segment_id
                )
                results.append(result)
            
            # Generate re-enrollment applications
            re_enroll_apps = self.generate_re_enrollment_applications(
                segment, time_manager, config_manager
            )
            
            if re_enroll_apps > 0:
                # Create result for re-enrollment applications
                result = self.create_process_result(
                    source_state="re_enrollment_eligible",
                    target_state=self.target_state,
                    population_count=segment.get_state_population("re_enrollment_eligible"),
                    success_count=re_enroll_apps,
                    segment_id=segment.segment_id
                )
                result.flow_id = "new_re_enrollment_applications"
                results.append(result)
        
        return results
    
    def generate_new_applications(self, population_segment, time_manager, config_manager):
        """
        Generate new applications for segment.
        
        Args:
            population_segment (PopulationSegment): Target population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            int: Number of applications generated.
        """
        # Get eligible population count
        eligible_population = population_segment.get_state_population(self.source_state)
        
        print(f"DEBUG: Eligible population for {population_segment.segment_id}: {eligible_population}")
        
        if eligible_population <= 0:
            print(f"DEBUG: No eligible population, returning 0 applications")
            return 0
        
        # Get application rate for this segment
        base_rate = self._get_application_rate(
            population_segment, time_manager, config_manager
        )
        
        print(f"DEBUG: Base rate for {population_segment.segment_id}: {base_rate}")
        
        # Apply seasonal factors
        adjusted_rate = self.apply_seasonal_factors(base_rate, time_manager, population_segment, config_manager)
        
        print(f"DEBUG: Adjusted rate after seasonal factors: {adjusted_rate}")
        
        # Apply distribution variation if available
        final_rate = self._apply_rate_distribution(
            adjusted_rate, population_segment, time_manager, config_manager
        )
        
        print(f"DEBUG: Final rate after distribution: {final_rate}")
        
        # Calculate the number of applications
        applications = int(round(eligible_population * final_rate))
        
        print(f"DEBUG: Calculated applications: {applications}")
        
        # Ensure applications don't exceed eligible population
        applications = min(applications, eligible_population)
        
        print(f"DEBUG: Applications after min check: {applications}")
        
        # Perform state transition
        success_count, _, _ = population_segment.transition_population(
            self.source_state, self.target_state, applications
        )
        
        print(f"DEBUG: Successful transitions: {success_count}")
        
        return success_count
    
    def generate_re_enrollment_applications(self, population_segment, time_manager, config_manager):
        """
        Generate re-enrollment applications for segment.
        
        Args:
            population_segment (PopulationSegment): Target population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            int: Number of re-enrollment applications generated.
        """
        # Get re-enrollment eligible population count
        eligible_population = population_segment.get_state_population("re_enrollment_eligible")
        
        if eligible_population <= 0:
            return 0
        
        # Get re-enrollment application rate for this segment
        base_rate = self._get_re_enrollment_rate(
            population_segment, time_manager, config_manager
        )
        
        # Apply seasonal factors
        adjusted_rate = self.apply_seasonal_factors(base_rate, time_manager, population_segment, config_manager)
        
        # Apply distribution variation if available
        final_rate = self._apply_rate_distribution(
            adjusted_rate, population_segment, time_manager, config_manager, 
            rate_type="re_enrollment"
        )
        
        # Calculate the number of applications
        applications = int(round(eligible_population * final_rate))
        
        # Ensure applications don't exceed eligible population
        applications = min(applications, eligible_population)
        
        # Perform state transition
        success_count, _, _ = population_segment.transition_population(
            "re_enrollment_eligible", self.target_state, applications
        )
        
        return success_count
    
    def _get_application_rate(self, segment, time_manager, config_manager):
        """
        Get application rate for segment.
        
        Args:
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            float: Application rate for the segment.
        """
        # Try to get segment-specific rate from cache
        if segment.segment_id in self.application_rates_by_segment:
            return self.application_rates_by_segment[segment.segment_id]
        
        # Get from configuration
        rate = config_manager.get_flow_rate(
            "new_applications", segment.cohort_type, segment.age_bracket.bracket_name
        )
        
        # Cache the rate
        self.application_rates_by_segment[segment.segment_id] = rate
        
        return rate
    
    def _get_re_enrollment_rate(self, segment, time_manager, config_manager):
        """
        Get re-enrollment rate for segment.
        
        Args:
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            float: Re-enrollment rate for the segment.
        """
        # Try to get segment-specific rate from cache
        if segment.segment_id in self.re_enrollment_rates_by_segment:
            return self.re_enrollment_rates_by_segment[segment.segment_id]
        
        # Get from configuration
        rate = config_manager.get_flow_rate(
            "new_re_enrollment_applications", segment.cohort_type, 
            segment.age_bracket.bracket_name
        )
        
        # Cache the rate
        self.re_enrollment_rates_by_segment[segment.segment_id] = rate
        
        return rate
    
    def apply_seasonal_factors(self, base_rate, time_manager, population_segment, config_manager):
        """
        Apply seasonal adjustment factors to base rate.
        
        Args:
            base_rate (float): Base rate value.
            time_manager (TimeManager): Time manager.
            population_segment (PopulationSegment): Population segment.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            float: Adjusted rate.
        """
        # Simple seasonal adjustment for Phase 2
        month = time_manager.current_date.month
        cohort_type = population_segment.cohort_type
        
        # Debug logging
        merged_config = config_manager.get_merged_config()
        print(f"Month: {month}, Cohort: {cohort_type}")
        print(f"Merged config has application_rates: {'application_rates' in merged_config}")
        
        if 'application_rates' in merged_config:
            print(f"Available cohorts: {list(merged_config['application_rates'].keys())}")
            if cohort_type in merged_config['application_rates']:
                cohort_config = merged_config['application_rates'][cohort_type]
                print(f"Cohort config: {cohort_config}")
                if 'seasonal_factors' in cohort_config:
                    print(f"Seasonal factors: {cohort_config['seasonal_factors']}")
                    if month in cohort_config['seasonal_factors']:
                        factor = cohort_config['seasonal_factors'][month]
                        print(f"Applying factor {factor} for month {month}")
                        return base_rate * factor
        
        # Fallback
        print(f"Using fallback logic for month {month}")
        if month == 1:
            return base_rate * 2.0
        elif month == 7:
            return base_rate * 0.5
        else:
            return base_rate
    
    def _apply_rate_distribution(self, base_rate, segment, time_manager, config_manager, 
                               rate_type="standard"):
        """
        Apply distribution variation to the rate.
        
        Args:
            base_rate (float): Base rate value.
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            rate_type (str): Type of rate ("standard" or "re_enrollment").
            
        Returns:
            float: Rate with applied variation.
        """
        # Get distribution parameters
        dist_id = "new_applications_distribution"
        if rate_type == "re_enrollment":
            dist_id = "new_re_enrollment_applications_distribution"
        
        dist_params = config_manager.get_distribution_parameters(
            dist_id, segment.cohort_type
        )
        
        # For Phase 2, implement simple normal distribution variation
        if dist_params.get('type') == 'normal':
            mean = dist_params.get('params', {}).get('mean', 1.0)
            stddev = dist_params.get('params', {}).get('stddev', 0.1)
            
            # Generate a variation factor
            variation = random.normalvariate(mean, stddev)
            
            # Apply variation to base rate
            adjusted_rate = base_rate * variation
            
            # Ensure rate is within valid range
            return max(0.0, min(1.0, adjusted_rate))
        
        # Default: return base rate
        return base_rate
    
    # def _is_segment_eligible(self, segment, time_manager, config_manager):
    #     """
    #     Check if segment is eligible based on rollout schedule.
        
    #     Args:
    #         segment (PopulationSegment): Population segment.
    #         time_manager (TimeManager): Time manager.
    #         config_manager (ConfigurationManager): Configuration manager.
            
    #     Returns:
    #         bool: True if segment is eligible, False otherwise.
    #     """
    #     # For Phase 2, implement basic rollout schedule check
    #     rollout_schedule = config_manager.get_rollout_schedule_object()
        
    #     if rollout_schedule:
    #         # Get age from segment's age bracket (midpoint for simplicity)
    #         age = (segment.age_bracket.age_min + segment.age_bracket.age_max) // 2
            
    #         # Check if cohort and age are eligible at current date
    #         return rollout_schedule.is_cohort_age_eligible(
    #             segment.cohort_type, age, time_manager.current_date
    #         )
        
    #     # If no rollout schedule, assume eligible
    #     return True


class ApplicationProcessor(ProcessStep):
    """
    Processes applications with approval/rejection.
    
    The ApplicationProcessor is responsible for approving or rejecting
    applications based on configurable rates and criteria.
    """
    
    def __init__(self, source_state, target_state):
        """
        Initialize application processor.
        
        Args:
            source_state (str): Source state identifier.
            target_state (str): Target state identifier.
        """
        super().__init__("application_processor", "Application Processing", 
                         source_state, target_state)
        self.approval_rates_by_segment = {}
        self.approval_rate_distributions = {}
    
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
        results = []
        
        # Process each population segment
        for segment in population_segments:
            # Get applied population
            applied_population = segment.get_state_population(self.source_state)
            
            if applied_population <= 0:
                continue
            
            # Calculate how many are from original eligible vs re-enrollment
            # This is a simplification - in a real system we would track these separately
            # Here we use proportional estimate
            eligible_pre = segment.get_state_population("eligible")
            re_enroll_pre = segment.get_state_population("re_enrollment_eligible")
            total_pre = eligible_pre + re_enroll_pre
            
            if total_pre <= 0:
                # If no pre-application population, assume all are original
                proportion_original = 1.0
            else:
                proportion_original = eligible_pre / total_pre
            
            original_applications = int(round(applied_population * proportion_original))
            re_enrollment_applications = applied_population - original_applications
            
            # Process original applications
            if original_applications > 0:
                approvals, rejections = self.process_applications(
                    segment, original_applications, time_manager, config_manager
                )
                
                if approvals > 0:
                    # Create result for approved applications
                    result = self.create_process_result(
                        source_state=self.source_state,
                        target_state=self.target_state,
                        population_count=original_applications,
                        success_count=approvals,
                        segment_id=segment.segment_id
                    )
                    result.flow_id = "new_enrollments"
                    results.append(result)
            
            # Process re-enrollment applications
            if re_enrollment_applications > 0:
                approvals, rejections = self.process_re_enrollments(
                    segment, re_enrollment_applications, time_manager, config_manager
                )
                
                if approvals > 0:
                    # Create result for approved re-enrollments
                    result = self.create_process_result(
                        source_state=self.source_state,
                        target_state=self.target_state,
                        population_count=re_enrollment_applications,
                        success_count=approvals,
                        segment_id=segment.segment_id
                    )
                    result.flow_id = "new_re_enrollment"
                    results.append(result)
        
        return results
    
    def process_applications(self, population_segment, application_count, 
                            time_manager, config_manager):
        """
        Process applications with approvals and rejections.
        
        Args:
            population_segment (PopulationSegment): Target population segment.
            application_count (int): Number of applications to process.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            tuple: (approvals_count, rejections_count)
        """
        if application_count <= 0:
            return 0, 0
        
        # Get approval rate for this segment
        approval_rate = self.calculate_approval_rate(
            population_segment, time_manager, config_manager, "new_enrollments"
        )
        
        # Calculate approvals and rejections
        approvals = int(round(application_count * approval_rate))
        rejections = application_count - approvals
        
        # Ensure we have valid counts
        approvals = max(0, min(approvals, application_count))
        rejections = application_count - approvals
        
        # Process approvals (source -> target)
        if approvals > 0:
            success_count, _, _ = population_segment.transition_population(
                self.source_state, self.target_state, approvals
            )
            approvals = success_count
            rejections = application_count - approvals
        
        # Process rejections (source -> eligible)
        if rejections > 0:
            rej_success, _, _ = population_segment.transition_population(
                self.source_state, "eligible", rejections
            )
            rejections = rej_success
        
        return approvals, rejections
    
    def process_re_enrollments(self, population_segment, application_count, 
                              time_manager, config_manager):
        """
        Process re-enrollment applications.
        
        Args:
            population_segment (PopulationSegment): Target population segment.
            application_count (int): Number of applications to process.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            
        Returns:
            tuple: (approvals_count, rejections_count)
        """
        if application_count <= 0:
            return 0, 0
        
        # Get approval rate for this segment (higher for re-enrollments)
        approval_rate = self.calculate_approval_rate(
            population_segment, time_manager, config_manager, "new_re_enrollment"
        )
        
        # Calculate approvals and rejections
        approvals = int(round(application_count * approval_rate))
        rejections = application_count - approvals
        
        # Ensure we have valid counts
        approvals = max(0, min(approvals, application_count))
        rejections = application_count - approvals
        
        # Process approvals (source -> target)
        if approvals > 0:
            success_count, _, _ = population_segment.transition_population(
                self.source_state, self.target_state, approvals
            )
            approvals = success_count
            rejections = application_count - approvals
        
        # Process rejections (source -> re_enrollment_eligible)
        if rejections > 0:
            rej_success, _, _ = population_segment.transition_population(
                self.source_state, "re_enrollment_eligible", rejections
            )
            rejections = rej_success
        
        return approvals, rejections
    
    def calculate_approval_rate(self, segment, time_manager, config_manager, flow_id):
        """
        Calculate approval rate for segment.
        
        Args:
            segment (PopulationSegment): Population segment.
            time_manager (TimeManager): Time manager.
            config_manager (ConfigurationManager): Configuration manager.
            flow_id (str): Flow identifier ("new_enrollments" or "new_re_enrollment").
            
        Returns:
            float: Approval rate for the segment.
        """
        # Try to get segment-specific rate from cache
        cache_key = f"{segment.segment_id}_{flow_id}"
        if cache_key in self.approval_rates_by_segment:
            return self.approval_rates_by_segment[cache_key]
        
        # Get from configuration
        rate = config_manager.get_flow_rate(
            flow_id, segment.cohort_type, segment.age_bracket.bracket_name
        )
        
        # Apply seasonal adjustment
        month = time_manager.current_date.month
        
        # Lower approval rates in high-volume months
        if month in [1, 9]:
            rate = rate * 0.95
        # Higher approval rates in low-volume months
        elif month in [6, 7, 8]:
            rate = rate * 1.05
        
        # Cache the rate
        self.approval_rates_by_segment[cache_key] = rate
        
        return rate