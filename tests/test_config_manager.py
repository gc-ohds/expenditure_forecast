"""
Tests for ConfigurationManager class.
"""

import os
import unittest
import tempfile
import yaml
from ohb_simulation.core.config_manager import ConfigurationManager


class TestConfigurationManager(unittest.TestCase):
    """Test cases for the ConfigurationManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test configurations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = self.temp_dir.name
        
        # Create test configurations
        self._create_test_configs()
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def _create_test_configs(self):
        """Create test configuration files."""
        # Create config directories
        os.makedirs(os.path.join(self.config_dir, "scenarios"), exist_ok=True)
        
        # Create base config
        base_config = {
            'simulation': {
                'time_interval': 'MONTHLY',
                'fiscal_year_start_month': 4,
                'fiscal_year_start_day': 1
            },
            'states': {
                'state1': {'id': 'state1', 'name': 'State 1', 'reset_on_fiscal_year': False},
                'state2': {'id': 'state2', 'name': 'State 2', 'reset_on_fiscal_year': True}
            },
            'flows': {
                'flow1': {'id': 'flow1', 'source': 'state1', 'target': 'state2'},
                'flow2': {'id': 'flow2', 'source': 'state2', 'target': 'state1'}
            },
            'flow_rates': {
                'flow1': 0.1,
                'flow2': 0.2
            }
        }
        
        with open(os.path.join(self.config_dir, "base_config.yaml"), 'w') as file:
            yaml.dump(base_config, file)
        
        # Create test scenario
        test_scenario = {
            'flow_rates': {
                'flow1': 0.15  # Override base rate
            },
            'regions': [
                {'region_id': 'region1', 'region_name': 'Region 1'},
                {'region_id': 'region2', 'region_name': 'Region 2'}
            ],
            'population_segments': [
                {
                    'segment_id': 'segment1',
                    'cohort_type': 'cohort1',
                    'region_id': 'region1',
                    'age_min': 0,
                    'age_max': 100,
                    'age_bracket_name': 'all',
                    'population_size': 1000
                }
            ]
        }
        
        with open(os.path.join(self.config_dir, "scenarios", "test_scenario.yaml"), 'w') as file:
            yaml.dump(test_scenario, file)
    
    def test_initialization(self):
        """Test initialization of ConfigurationManager."""
        config_manager = ConfigurationManager(self.config_dir)
        
        self.assertEqual(config_manager.config_directory, self.config_dir)
        self.assertIsNone(config_manager.scenario_name)
        self.assertIsNotNone(config_manager.base_config)
        self.assertEqual(config_manager.base_config['simulation']['time_interval'], 'MONTHLY')
    
    def test_load_scenario_configuration(self):
        """Test loading scenario configuration."""
        config_manager = ConfigurationManager(self.config_dir)
        
        # Load existing scenario
        success = config_manager.load_scenario_configuration("test_scenario")
        
        self.assertTrue(success)
        self.assertEqual(config_manager.scenario_name, "test_scenario")
        self.assertEqual(len(config_manager.scenario_config['regions']), 2)
        
        # Try to load non-existent scenario
        success = config_manager.load_scenario_configuration("nonexistent_scenario")
        
        self.assertFalse(success)
        self.assertEqual(config_manager.scenario_name, "nonexistent_scenario")
        self.assertEqual(config_manager.scenario_config, {})
    
    def test_get_merged_config(self):
        """Test merging base and scenario configurations."""
        config_manager = ConfigurationManager(self.config_dir)
        config_manager.load_scenario_configuration("test_scenario")
        
        merged_config = config_manager.get_merged_config()
        
        # Check that scenario values override base values
        self.assertEqual(merged_config['flow_rates']['flow1'], 0.15)
        
        # Check that base values are preserved
        self.assertEqual(merged_config['flow_rates']['flow2'], 0.2)
        
        # Check that new scenario sections are added
        self.assertIn('regions', merged_config)
        self.assertEqual(len(merged_config['regions']), 2)
    
    def test_get_flow_rate(self):
        """Test getting flow rates for different parameters."""
        config_manager = ConfigurationManager(self.config_dir)
        config_manager.load_scenario_configuration("test_scenario")
        
        # Test getting overridden flow rate
        flow_rate = config_manager.get_flow_rate('flow1', 'cohort1', 'all')
        self.assertEqual(flow_rate, 0.15)
        
        # Test getting base flow rate
        flow_rate = config_manager.get_flow_rate('flow2', 'cohort1', 'all')
        self.assertEqual(flow_rate, 0.2)
        
        # Test getting non-existent flow rate
        flow_rate = config_manager.get_flow_rate('flow3', 'cohort1', 'all')
        self.assertEqual(flow_rate, 0.0)
    
    def test_get_state_definitions(self):
        """Test getting state definitions."""
        config_manager = ConfigurationManager(self.config_dir)
        
        state_defs = config_manager.get_state_definitions()
        
        self.assertEqual(len(state_defs), 2)
        self.assertIn('state1', state_defs)
        self.assertEqual(state_defs['state1']['name'], 'State 1')
        self.assertFalse(state_defs['state1']['reset_on_fiscal_year'])
        self.assertTrue(state_defs['state2']['reset_on_fiscal_year'])
    
    def test_get_flow_definitions(self):
        """Test getting flow definitions."""
        config_manager = ConfigurationManager(self.config_dir)
        
        flow_defs = config_manager.get_flow_definitions()
        
        self.assertEqual(len(flow_defs), 2)
        self.assertIn('flow1', flow_defs)
        self.assertEqual(flow_defs['flow1']['source'], 'state1')
        self.assertEqual(flow_defs['flow1']['target'], 'state2')
    
    def test_get_regions(self):
        """Test getting region definitions."""
        config_manager = ConfigurationManager(self.config_dir)
        config_manager.load_scenario_configuration("test_scenario")
        
        regions = config_manager.get_regions()
        
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0]['region_id'], 'region1')
        self.assertEqual(regions[1]['region_name'], 'Region 2')
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        config_manager = ConfigurationManager(self.config_dir)
        config_manager.load_scenario_configuration("test_scenario")
        
        # Valid configuration
        self.assertTrue(config_manager.validate_configuration())
        
        # Corrupt the configuration
        config_manager.base_config['flows']['invalid_flow'] = {
            'id': 'invalid_flow',
            'source': 'state1',
            'target': 'nonexistent_state'  # Invalid target state
        }
        
        # Invalid configuration
        self.assertFalse(config_manager.validate_configuration())
    
    def test_list_available_scenarios(self):
        """Test listing available scenarios."""
        config_manager = ConfigurationManager(self.config_dir)
        
        scenarios = config_manager.list_available_scenarios()
        
        self.assertIn("test_scenario", scenarios)
        self.assertEqual(len(scenarios), 1)


if __name__ == '__main__':
    unittest.main()
