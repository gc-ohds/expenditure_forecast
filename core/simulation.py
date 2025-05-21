"""
Simulation module for OHB Simulation Model.

This module provides the Simulation class, which orchestrates the entire
simulation process.
"""

import logging
import datetime
from core.time_manager import TimeManager
from core.config_manager import ConfigurationManager
from population.region import Region
from stats.statistics_tracker import StatisticsTracker
from util.rollout import RolloutSchedule
from process.application import ApplicationGenerator, ApplicationProcessor


logger = logging.getLogger(__name__)


class Simulation:
    """
    Main simulation class that orchestrates the entire process.
    
    The Simulation class is responsible for initializing all components,
    running the simulation through time periods, and generating reports.
    """
    
    def __init__(self, start_date, end_date, time_interval='MONTHLY', config_directory='config'):
        """
        Initialize simulation with time boundaries and interval.
        
        Args:
            start_date (datetime.date or str): Starting date for the simulation.
            end_date (datetime.date or str): Ending date for the simulation.
            time_interval (str): Time interval for progression ('MONTHLY', 'QUARTERLY', 'ANNUAL').
            config_directory (str): Path to the configuration directory.
        """
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
        self.start_date = start_date
        self.end_date = end_date
        self.time_interval = time_interval
        
        # Initialize components
        self.config_manager = ConfigurationManager(config_directory)
        self.time_manager = None
        self.regions = []
        self.statistics_tracker = StatisticsTracker()
        
        logger.info(f"Initialized simulation from {start_date} to {end_date} "
                   f"with {time_interval} intervals")
    
    def initialize_simulation(self):
        """
        Set up all simulation components.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        # Initialize time manager
        sim_params = self.config_manager.get_simulation_parameters()
        fiscal_year_start_month = sim_params.get('fiscal_year_start_month', 4)
        fiscal_year_start_day = sim_params.get('fiscal_year_start_day', 1)
        
        self.time_manager = TimeManager(
            start_date=self.start_date,
            time_interval=self.time_interval,
            fiscal_year_start_month=fiscal_year_start_month,
            fiscal_year_start_day=fiscal_year_start_day
        )
        
        # Initialize regions and population segments
        self._initialize_regions()
        
        # Load rollout schedule from configuration
        from util.rollout import RolloutSchedule
        self.rollout_schedule = RolloutSchedule()
        success = self.rollout_schedule.load_from_config(self.config_manager)
        
        if not success:
            logger.warning("Failed to load rollout schedule from configuration")
        else:
            logger.info(f"Successfully loaded rollout schedule with {len(self.rollout_schedule.phases)} phases")
        
        # Store original population sizes for each segment
        self.segment_original_populations = {}
        
        # Apply rollout schedule to determine initial eligible populations
        if self.rollout_schedule:
            current_date = self.time_manager.current_date
            eligible_cohorts = self.rollout_schedule.get_eligible_cohorts(current_date)
            logger.info(f"Eligible cohorts at start date: {eligible_cohorts}")
            
            # Process each region
            for region in self.regions:
                for segment in region.population_segments:
                    # Store original population
                    self.segment_original_populations[segment.segment_id] = segment.states['eligible'].get_population()
                    
                    # Check if segment is eligible based on rollout schedule
                    age = (segment.age_bracket.age_min + segment.age_bracket.age_max) // 2
                    is_eligible = self.rollout_schedule.is_cohort_age_eligible(
                        segment.cohort_type, age, current_date
                    )
                    
                    if not is_eligible:
                        # Reset eligible population to 0
                        segment.states['eligible'].reset_population()
                        logger.info(f"Segment {segment.segment_id} not eligible at start date")
                    else:
                        logger.info(f"Segment {segment.segment_id} eligible at start date")
        
        # Initialize application process components
        self.application_generator = ApplicationGenerator(
            source_state="eligible",
            target_state="applied"
        )
        
        self.application_processor = ApplicationProcessor(
            source_state="applied",
            target_state="enrolled_inactive"
        )
        
        # Update initial state metrics
        self.statistics_tracker.update_state_metrics(self.regions, self.time_manager)
        
        logger.info("Simulation initialization complete")
        return True
    
    def _initialize_regions(self):
        """
        Initialize regions and their population segments.
        
        Returns:
            list: List of initialized regions.
        """
        # Get region and segment definitions from configuration
        region_defs = self.config_manager.get_regions()
        segment_defs = self.config_manager.get_population_segments()
        state_defs = self.config_manager.get_state_definitions()
        
        # Create regions
        for region_def in region_defs:
            region = Region(
                region_id=region_def.get('region_id'),
                region_name=region_def.get('region_name')
            )
            
            # Initialize segments for this region
            region.initialize_segments(segment_defs, state_defs)
            
            self.regions.append(region)
        
        logger.info(f"Initialized {len(self.regions)} regions with "
                   f"{sum(len(r.population_segments) for r in self.regions)} "
                   f"population segments")
        
        return self.regions
    
    def load_configuration(self, scenario_name):
        """
        Load configuration for a specific scenario.
        
        Args:
            scenario_name (str): Name of the scenario to load.
            
        Returns:
            bool: True if loading was successful, False otherwise.
        """
        success = self.config_manager.load_scenario_configuration(scenario_name)
        
        if success:
            logger.info(f"Loaded scenario configuration: {scenario_name}")
        else:
            logger.warning(f"Failed to load scenario configuration: {scenario_name}")
        
        return success
    
    def run_simulation(self):
        """
        Execute the simulation from start to end date.
        
        Returns:
            dict: Dictionary of simulation results.
        """
        logger.info("Starting simulation run")
        
        # Capture initial state metrics
        self.statistics_tracker.update_state_metrics(self.regions, self.time_manager)
        
        # Process time periods
        while self.time_manager.current_date <= self.end_date:
            period = self.time_manager.get_current_period()
            logger.info(f"Processing period: {period}")
            
            # Process the current time period
            self.process_time_period()
            
            # Record state history for all regions
            for region in self.regions:
                region.record_state_history(period)
            
            # Calculate derived metrics
            self.statistics_tracker.calculate_derived_metrics(self.time_manager)
            
            # Advance time and check for fiscal year transition
            fiscal_transition = self.time_manager.advance_time()
            
            # Handle fiscal year transition if occurred
            if fiscal_transition:
                logger.info(f"Fiscal year transition at {self.time_manager.current_date}")
                
                # Reset annual states for all regions
                for region in self.regions:
                    reset_results = region.reset_annual_states()
                    if reset_results:
                        logger.debug(f"Reset annual states for region {region.region_id}")
            
            # Stop if we've reached the end date
            if self.time_manager.current_date > self.end_date:
                break
        
        logger.info("Simulation run complete")
        
        # Return simulation results
        return self.get_simulation_results()
    
    def process_time_period(self):
        """
        Process a single time period for all regions.
        
        Returns:
            dict: Dictionary of process results.
        """
        all_results = []
        period = self.time_manager.get_current_period()
        logger.info(f"Processing period: {period}")
        
        # Update eligibility based on rollout schedule
        if self.rollout_schedule:
            current_date = self.time_manager.current_date
            eligible_cohorts = self.rollout_schedule.get_eligible_cohorts(current_date)
            logger.info(f"Current date: {current_date}, Eligible cohorts: {eligible_cohorts}")
            
            # Process each region
            for region in self.regions:
                for segment in region.population_segments:
                    # Check if segment is already eligible
                    current_eligible = segment.states['eligible'].get_population()
                    
                    # Only check segments that aren't already eligible
                    if current_eligible == 0:
                        # Check if segment is newly eligible based on rollout schedule
                        age = (segment.age_bracket.age_min + segment.age_bracket.age_max) // 2
                        is_eligible = self.rollout_schedule.is_cohort_age_eligible(
                            segment.cohort_type, age, current_date
                        )
                        
                        # If segment just became eligible, restore its population
                        if is_eligible:
                            original_pop = self.segment_original_populations.get(segment.segment_id, segment.population_size)
                            segment.states['eligible'].set_population(original_pop)
                            logger.info(f"Segment {segment.segment_id} became eligible at {current_date}, population {original_pop}")
        
        # Application generation for all regions
        for region in self.regions:
            # Generate applications using ApplicationGenerator
            app_gen_results = self.application_generator.execute(
                region.population_segments, 
                self.time_manager, 
                self.config_manager
            )
            all_results.extend(app_gen_results)
            
            # Process applications using ApplicationProcessor
            app_proc_results = self.application_processor.execute(
                region.population_segments, 
                self.time_manager, 
                self.config_manager
            )
            all_results.extend(app_proc_results)
            
            # Existing population flow processing
            flow_results = region.process_population_flows(
                self.time_manager, self.config_manager
            )
            all_results.extend(flow_results)
        
        # Update state metrics after all flows
        self.statistics_tracker.update_state_metrics(self.regions, self.time_manager)
        
        # Update flow metrics from results
        for result in all_results:
            if hasattr(result, 'flow_id') and result.flow_id:
                self.statistics_tracker.update_flow_metric(
                    flow_id=result.flow_id, 
                    period=period, 
                    count=result.success_count, 
                    segment_id=result.segment_id
                )
            
            # Add financial impact if present
            if hasattr(result, 'financial_impact') and result.financial_impact > 0:
                self.statistics_tracker.update_financial_metric(
                    metric_id='claim_expenditure',
                    period=period, 
                    amount=result.financial_impact, 
                    segment_id=result.segment_id
                )
        
        return {'period': period, 'results': all_results}
    
    def get_simulation_results(self):
        """
        Get the complete simulation results.
        
        Returns:
            dict: Dictionary of simulation results in normalized format.
        """
        # Get normalized metrics from the statistics tracker
        metrics_dict = self.statistics_tracker.export_to_dict()
        
        # Add simulation parameters
        results = {
            'simulation_params': {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'time_interval': self.time_interval,
                'scenario': self.config_manager.scenario_name
            }
        }
        
        # Merge with metrics
        results.update(metrics_dict)
        
        return results
    
    def generate_reports(self):
        """
        Generate simulation reports.
        
        In Phase 1, this is a placeholder for future report generation.
        
        Returns:
            dict: Dictionary of generated reports.
        """
        # For Phase 1, just return the simulation results
        return self.get_simulation_results()

    def export_results(self, output_path, formats=None):
        """
        Export simulation results to specified formats.
        
        Args:
            output_path (str): Base path for output files (without extension).
            formats (list, optional): List of format strings ('json', 'csv'). 
                                      If None, exports to JSON only.
            
        Returns:
            dict: Dictionary mapping formats to file paths.
        """
        if formats is None:
            formats = ['json']
        
        results = self.get_simulation_results()
        file_paths = {}
        
        # Export to JSON
        if 'json' in formats:
            json_path = f"{output_path}.json"
            import json
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            file_paths['json'] = json_path
        
        # Export to CSV
        if 'csv' in formats:
            csv_paths = self.statistics_tracker.export_to_csv(output_path)
            file_paths['csv'] = csv_paths
            
            # Also export simulation parameters
            params_path = f"{output_path}_simulation_params.csv"
            param_rows = []
            for key, value in results['simulation_params'].items():
                param_rows.append(f"{key},{value}")
            
            with open(params_path, 'w') as f:
                f.write("parameter,value\n")
                f.write("\n".join(param_rows))
            
            file_paths['csv']['params'] = params_path
        
        return file_paths