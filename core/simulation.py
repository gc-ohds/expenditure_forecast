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
        
        # Process population flows for all regions
        for region in self.regions:
            flow_results = region.process_population_flows(
                self.time_manager, self.config_manager
            )
            
            all_results.extend(flow_results)
        
        # Update state metrics after all flows
        self.statistics_tracker.update_state_metrics(self.regions, self.time_manager)
        
        # Update flow metrics from results
        period = self.time_manager.get_current_period()
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
                
                if hasattr(result, 'program_payment') and result.program_payment > 0:
                    self.statistics_tracker.update_financial_metric(
                        metric_id='program_expenditure',
                        period=period, 
                        amount=result.program_payment, 
                        segment_id=result.segment_id
                    )
                
                if hasattr(result, 'patient_payment') and result.patient_payment > 0:
                    self.statistics_tracker.update_financial_metric(
                        metric_id='patient_expenditure',
                        period=period, 
                        amount=result.patient_payment, 
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
