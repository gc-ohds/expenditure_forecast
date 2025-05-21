"""
Configuration Manager module for OHB Simulation Model.

This module provides the ConfigurationManager class, which handles loading and
managing configuration data for the simulation.
"""

import os
import yaml
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Handles loading and managing configuration data.
    
    The ConfigurationManager is responsible for loading base and scenario-specific
    configurations, and providing access to configuration parameters throughout
    the simulation.
    """
    
    def __init__(self, config_directory):
        """
        Initialize with configuration directory path.
        
        Args:
            config_directory (str): Path to the directory containing configuration files.
        """
        self.config_directory = config_directory
        self.scenario_name = None
        self.base_config = {}
        self.scenario_config = {}
        self.rate_configs = {}
        self.distribution_configs = {}
        self.service_configs = {}
        self.rollout_configs = {}
        self.benefit_configs = {}
        
        # Initialize with base configuration
        self.load_base_configuration()
    
    def load_base_configuration(self):
        """
        Load base configuration settings.
        
        Returns:
            bool: True if loading was successful, False otherwise.
        """
        base_config_path = os.path.join(self.config_directory, "base_config.yaml")
        try:
            with open(base_config_path, 'r') as file:
                self.base_config = yaml.safe_load(file)
            logger.info(f"Loaded base configuration from {base_config_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Base configuration file not found at {base_config_path}")
            # Initialize with empty configuration
            self.base_config = {
                "simulation": {
                    "time_interval": "MONTHLY",
                    "fiscal_year_start_month": 4,
                    "fiscal_year_start_day": 1
                },
                "states": {
                    "eligible_population": {"id": "eligible", "name": "Eligible Population", "reset_on_fiscal_year": False},
                    "re_enrollment_eligible_population": {"id": "re_enrollment_eligible", "name": "Re-enrollment Eligible Population", "reset_on_fiscal_year": False},
                    "applied_population": {"id": "applied", "name": "Applied Population", "reset_on_fiscal_year": False},
                    "enrolled_inactive_population": {"id": "enrolled_inactive", "name": "Enrolled Inactive Population", "reset_on_fiscal_year": True},
                    "active_claimant_population": {"id": "active_claimant", "name": "Active Claimant Population", "reset_on_fiscal_year": True}
                },
                "flows": {
                    "new_applications": {"id": "new_applications", "source": "eligible", "target": "applied"},
                    "new_re_enrollment_applications": {"id": "new_re_enrollment_applications", "source": "re_enrollment_eligible", "target": "applied"},
                    "new_enrollments": {"id": "new_enrollments", "source": "applied", "target": "enrolled_inactive"},
                    "new_re_enrollment": {"id": "new_re_enrollment", "source": "applied", "target": "enrolled_inactive"},
                    "new_first_claimants": {"id": "new_first_claimants", "source": "enrolled_inactive", "target": "active_claimant"}
                }
            }
            logger.info("Initialized with default base configuration")
            return False
    
    def load_scenario_configuration(self, scenario_name):
        """
        Load scenario-specific configuration.
        
        Args:
            scenario_name (str): Name of the scenario to load.
            
        Returns:
            bool: True if loading was successful, False otherwise.
        """
        self.scenario_name = scenario_name
        scenario_path = os.path.join(self.config_directory, "scenarios", f"{scenario_name}.yaml")
        
        try:
            with open(scenario_path, 'r') as file:
                self.scenario_config = yaml.safe_load(file)
            logger.info(f"Loaded scenario configuration from {scenario_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Scenario configuration file not found at {scenario_path}")
            self.scenario_config = {}
            return False
    
    def get_merged_config(self):
        """
        Get configuration with scenario overrides applied to base configuration.
        
        Returns:
            dict: Merged configuration dictionary.
        """
        # Create a deep copy of the base configuration
        merged_config = deepcopy(self.base_config)
        
        # Apply scenario overrides, if any
        if self.scenario_config:
            self._deep_update(merged_config, self.scenario_config)
        
        return merged_config
    
    def _deep_update(self, target, source):
        """
        Recursively update a nested dictionary.
        
        Args:
            target (dict): Target dictionary to update.
            source (dict): Source dictionary with updated values.
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively update nested dictionaries
                self._deep_update(target[key], value)
            else:
                # Directly update value
                target[key] = value
    
    def get_flow_rate(self, flow_id, segment_type, age_bracket):
        """
        Get flow rate for specified parameters.
        
        Args:
            flow_id (str): Identifier for the flow.
            segment_type (str): Type of population segment.
            age_bracket (str): Age bracket identifier.
            
        Returns:
            float: Flow rate for the specified parameters.
        """
        # For Phase 1, implement a simple lookup from configuration
        merged_config = self.get_merged_config()
        
        if 'flow_rates' in merged_config:
            flow_rates = merged_config['flow_rates']
            
            # Try to find exact match for all parameters
            key = f"{flow_id}_{segment_type}_{age_bracket}"
            if key in flow_rates:
                return flow_rates[key]
            
            # Try segment_type
            key = f"{flow_id}_{segment_type}"
            if key in flow_rates:
                return flow_rates[key]
            
            # Try just flow_id
            if flow_id in flow_rates:
                return flow_rates[flow_id]
        
        # Default value if not found
        return 0.0
    
    def get_distribution_parameters(self, dist_id, segment_type):
        """
        Get statistical distribution parameters.
        
        Args:
            dist_id (str): Distribution identifier.
            segment_type (str): Type of population segment.
            
        Returns:
            dict: Distribution parameters.
        """
        # Basic implementation for Phase 1
        merged_config = self.get_merged_config()
        
        if 'distributions' in merged_config:
            distributions = merged_config['distributions']
            
            # Try to find exact match
            key = f"{dist_id}_{segment_type}"
            if key in distributions:
                return distributions[key]
            
            # Try just dist_id
            if dist_id in distributions:
                return distributions[dist_id]
        
        # Default to uniform distribution
        return {"type": "uniform", "params": {"min": 0.0, "max": 1.0}}
    
    def get_state_definitions(self):
        """
        Get process state definitions from configuration.
        
        Returns:
            dict: Dictionary of state definitions.
        """
        merged_config = self.get_merged_config()
        return merged_config.get('states', {})
    
    def get_flow_definitions(self):
        """
        Get population flow definitions from configuration.
        
        Returns:
            dict: Dictionary of flow definitions.
        """
        merged_config = self.get_merged_config()
        return merged_config.get('flows', {})
    
    def get_simulation_parameters(self):
        """
        Get parameters for simulation setup.
        
        Returns:
            dict: Dictionary of simulation parameters.
        """
        merged_config = self.get_merged_config()
        return merged_config.get('simulation', {})
    
    def get_population_segments(self):
        """
        Get population segment definitions.
        
        Returns:
            list: List of population segment definitions.
        """
        merged_config = self.get_merged_config()
        return merged_config.get('population_segments', [])
    
    def get_regions(self):
        """
        Get region definitions.
        
        Returns:
            list: List of region definitions.
        """
        merged_config = self.get_merged_config()
        return merged_config.get('regions', [])
    
    def validate_configuration(self):
        """
        Validate loaded configuration for consistency.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        # Basic validation for Phase 1
        merged_config = self.get_merged_config()
        
        # Check for required sections
        required_sections = ['simulation', 'states', 'flows']
        for section in required_sections:
            if section not in merged_config:
                logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Check for time_interval in simulation section
        if 'time_interval' not in merged_config['simulation']:
            logger.error("Missing required parameter: simulation.time_interval")
            return False
        
        # Validate that all flow sources and targets reference valid states
        states = merged_config['states']
        flows = merged_config['flows']
        
        state_ids = [state['id'] for state in states.values()]
        
        for flow_id, flow in flows.items():
            if 'source' not in flow or 'target' not in flow:
                logger.error(f"Flow {flow_id} missing source or target")
                return False
            
            if flow['source'] not in state_ids:
                logger.error(f"Flow {flow_id} references invalid source state: {flow['source']}")
                return False
            
            if flow['target'] not in state_ids:
                logger.error(f"Flow {flow_id} references invalid target state: {flow['target']}")
                return False
        
        return True
    
    def list_available_scenarios(self):
        """
        List all available scenarios.
        
        Returns:
            List[str]: List of available scenario names.
        """
        scenario_dir = os.path.join(self.config_directory, "scenarios")
        if not os.path.exists(scenario_dir):
            return []
        
        scenarios = []
        for filename in os.listdir(scenario_dir):
            if filename.endswith(".yaml"):
                scenarios.append(filename[:-5])  # Remove .yaml extension
        
        return scenarios
    
    def get_rollout_schedule(self):
        """
        Get rollout schedule configuration.
        
        Returns:
            list: List of rollout phase configurations.
        """
        merged_config = self.get_merged_config()
        return merged_config.get('rollout_schedule', [])

    def get_rollout_schedule_object(self):
        """
        Get or create a RolloutSchedule object from configuration.
        
        Returns:
            RolloutSchedule: Configured rollout schedule object, or None if unavailable.
        """
        # Avoid circular imports
        from util.rollout import RolloutSchedule
        
        if not hasattr(self, '_rollout_schedule') or self._rollout_schedule is None:
            self._rollout_schedule = RolloutSchedule()
            success = self._rollout_schedule.load_from_config(self)
            
            # If loading fails, set to None to avoid repeated failures
            if not success:
                logger.warning("Failed to load rollout schedule, defaulting to None")
                return None
        
        return self._rollout_schedule