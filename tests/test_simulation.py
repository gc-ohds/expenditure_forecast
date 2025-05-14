"""
Tests for Simulation class.
"""

import os
import unittest
import tempfile
import yaml
import datetime
from ohb_simulation.core.simulation import Simulation


class TestSimulation(unittest.TestCase):
    """Test cases for the Simulation class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test configurations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = self.temp_dir.name
        
        # Create test configurations
        self._create_test_configs()
        
        # Set up simulation
        self.start_date = datetime.date(2025, 4, 1)
        self.end_date = datetime.date(2025, 6, 30)
        self.simulation = Simulation(
            start_date=self.start_date,
            end_date=self.end_date,
            time_interval='MONTHLY',
            config_directory=self.config_dir
        )
    
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
                'eligible': {'id': 'eligible', 'name': 'Eligible Population', 'reset_on_fiscal_year': False},
                're_enrollment_eligible': {'id': 're_enrollment_eligible', 'name': 'Re-enrollment Eligible', 'reset_on_fiscal_year': False},
                'applied': {'id': 'applied', 'name': 'Applied Population', 'reset_on_fiscal_year': False},
                'enrolled_inactive': {'id': 'enrolled_inactive', 'name': 'Enrolled Inactive', 'reset_on_fiscal_year': True},
                'active_claimant': {'id': 'active_claimant', 'name': 'Active Claimant', 'reset_on_fiscal_year': True}
            },
            'flows': {
                'new_applications': {'id': 'new_applications', 'source': 'eligible', 'target': 'applied'},
                'new_enrollments': {'id': 'new_enrollments', 'source': 'applied', 'target': 'enrolled_inactive'},
                'new_first_claimants': {'id': 'new_first_claimants', 'source': 'enrolled_inactive', 'target': 'active_claimant'}
            },
            'flow_rates': {
                'new_applications': 0.1,
                'new_enrollments': 0.8,
                'new_first_claimants': 0.2
            }
        }
        
        with open(os.path.join(self.config_dir, "base_config.yaml"), 'w') as file:
            yaml.dump(base_config, file)
        
        # Create test scenario
        test_scenario = {
            'regions': [
                {'region_id': 'test_region', 'region_name': 'Test Region'}
            ],
            'population_segments': [
                {
                    'segment_id': 'test_segment',
                    'cohort_type': 'test_cohort',
                    'region_id': 'test_region',
                    'age_min': 0,
                    'age_max': 100,
                    'age_bracket_name': 'all',
                    'population_size': 1000
                }
            ]
        }
        
        with open(os.path.join(self.config_dir, "scenarios", "test_simulation.yaml"), 'w') as file:
            yaml.dump(test_scenario, file)
    
    def test_initialization(self):
        """Test initialization of Simulation."""
        self.assertEqual(self.simulation.start_date, self.start_date)
        self.assertEqual(self.simulation.end_date, self.end_date)
        self.assertEqual(self.simulation.time_interval, 'MONTHLY')
        self.assertIsNotNone(self.simulation.config_manager)
        self.assertIsNone(self.simulation.time_manager)
        self.assertEqual(len(self.simulation.regions), 0)
        self.assertIsNotNone(self.simulation.statistics_tracker)
    
    def test_load_configuration(self):
        """Test loading configuration."""
        success = self.simulation.load_configuration("test_simulation")
        
        self.assertTrue(success)
        self.assertEqual(self.simulation.config_manager.scenario_name, "test_simulation")
    
    def test_initialize_simulation(self):
        """Test simulation initialization."""
        self.simulation.load_configuration("test_simulation")
        success = self.simulation.initialize_simulation()
        
        self.assertTrue(success)
        self.assertIsNotNone(self.simulation.time_manager)
        self.assertEqual(len(self.simulation.regions), 1)
        self.assertEqual(self.simulation.regions[0].region_id, 'test_region')
        
        # Check population segments
        self.assertEqual(len(self.simulation.regions[0].population_segments), 1)
        segment = self.simulation.regions[0].population_segments[0]
        self.assertEqual(segment.segment_id, 'test_segment')
        self.assertEqual(segment.population_size, 1000)
        
        # Check states are initialized
        self.assertEqual(len(segment.states), 5)
        self.assertEqual(segment.get_state_population('eligible'), 1000)
    
    def test_run_simulation(self):
        """Test running a basic simulation."""
        self.simulation.load_configuration("test_simulation")
        self.simulation.initialize_simulation()
        
        # Run the simulation
        results = self.simulation.run_simulation()
        
        # Basic checks on results
        self.assertIsNotNone(results)
        self.assertIn('simulation_params', results)
        self.assertIn('state_metrics', results)
        self.assertIn('flow_metrics', results)
        
        # Check some metrics were recorded
        self.assertIn('eligible', results['state_metrics'])
        self.assertIn('new_applications', results['flow_metrics'])
        
        # Check that time has advanced to end date
        self.assertTrue(self.simulation.time_manager.current_date > self.end_date)
        
        # Check that at least some population has flowed through states
        final_period = "2025-06"  # June 2025
        initial_eligible = 1000
        final_eligible = results['state_metrics']['eligible'][final_period]['total']
        
        # Should be less than initial as some have applied and enrolled
        self.assertLess(final_eligible, initial_eligible)
        
        # Check that some have enrolled
        enrolled_inactive = results['state_metrics']['enrolled_inactive'][final_period]['total']
        active_claimant = results['state_metrics']['active_claimant'][final_period]['total']
        total_enrolled = enrolled_inactive + active_claimant
        
        self.assertGreater(total_enrolled, 0)
    
    def test_get_simulation_results(self):
        """Test getting simulation results."""
        self.simulation.load_configuration("test_simulation")
        self.simulation.initialize_simulation()
        self.simulation.run_simulation()
        
        results = self.simulation.get_simulation_results()
        
        self.assertIsNotNone(results)
        self.assertIn('simulation_params', results)
        self.assertEqual(results['simulation_params']['scenario'], 'test_simulation')
        self.assertEqual(results['simulation_params']['start_date'], self.start_date.isoformat())
        self.assertEqual(results['simulation_params']['end_date'], self.end_date.isoformat())


if __name__ == '__main__':
    unittest.main()
