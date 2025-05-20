"""
Main module for OHB Simulation Model.

This module provides the entry point for running simulations.
"""

import os
import sys
import logging
import argparse
import datetime
import json
from core.simulation import Simulation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description='Run OHB Simulation Model')
    
    parser.add_argument('--start-date', type=str, default='2025-04-01',
                       help='Start date for simulation (YYYY-MM-DD)')
    
    parser.add_argument('--end-date', type=str, default='2026-03-31',
                       help='End date for simulation (YYYY-MM-DD)')
    
    parser.add_argument('--time-interval', type=str, default='MONTHLY',
                       choices=['MONTHLY', 'QUARTERLY', 'ANNUAL'],
                       help='Time interval for simulation progression')
    
    parser.add_argument('--config-dir', type=str, default='config',
                       help='Directory containing configuration files')
    
    parser.add_argument('--scenario', type=str, default='simple_scenario',
                       help='Name of the scenario to run')
    
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Directory for output files')
    
    parser.add_argument('--output-format', type=str, default='json',
                       choices=['json', 'csv', 'both'],
                       help='Format for output files (json, csv, or both)')
    
    parser.add_argument('--list-scenarios', action='store_true',
                       help='List available scenarios and exit')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    return parser.parse_args()


def list_available_scenarios(config_dir):
    """
    List available simulation scenarios.
    
    Args:
        config_dir (str): Path to configuration directory.
        
    Returns:
        list: List of available scenario names.
    """
    from core.config_manager import ConfigurationManager
    
    config_manager = ConfigurationManager(config_dir)
    scenarios = config_manager.list_available_scenarios()
    
    if scenarios:
        print("Available scenarios:")
        for scenario in scenarios:
            print(f"  - {scenario}")
    else:
        print("No scenarios found in", config_dir)
    
    return scenarios


def main():
    """
    Main application entry point.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # List scenarios if requested
    if args.list_scenarios:
        list_available_scenarios(args.config_dir)
        return 0
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        logger.info(f"Created output directory: {args.output_dir}")
    
    try:
        # Create and initialize simulation
        simulation = Simulation(
            start_date=args.start_date,
            end_date=args.end_date,
            time_interval=args.time_interval,
            config_directory=args.config_dir
        )
        
        # Load scenario configuration
        simulation.load_configuration(args.scenario)
        
        # Initialize simulation components
        simulation.initialize_simulation()

        
        # Run simulation
        results = simulation.run_simulation()
                
        # Generate reports - This is a placeholder for report generation in the future
        # reports = simulation.generate_reports()

        # Generate output filename base
        output_base = os.path.join(
            args.output_dir, 
            f"simulation_results_{args.scenario}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Determine output formats
        formats = []
        if args.output_format == 'json' or args.output_format == 'both':
            formats.append('json')
        if args.output_format == 'csv' or args.output_format == 'both':
            formats.append('csv')
        
        # Export results in the requested format(s)
        output_files = simulation.export_results(output_base, formats)
        
        # Log output files
        logger.info(f"Simulation results exported in the following formats:")
        for fmt, paths in output_files.items():
            if isinstance(paths, dict):
                logger.info(f"  {fmt.upper()} files:")
                for metric_type, path in paths.items():
                    logger.info(f"    - {metric_type}: {path}")
            else:
                logger.info(f"  {fmt.upper()}: {paths}")
        
        # Print summary results
        print("\nSimulation Summary:")
        print(f"  Scenario: {args.scenario}")
        print(f"  Time period: {args.start_date} to {args.end_date}")
        print(f"  Time interval: {args.time_interval}")
        
        # Find the latest period in the metrics
        all_periods = set(m["period"] for m in results["metrics"] if m["period"].startswith("20"))
        if all_periods:
            final_period = max(all_periods)
            
            # Get total eligible population
            total_eligible_metrics = [m for m in results["metrics"] 
                                      if m["type"] == "derived" and 
                                         m["id"] == "total_eligible_population" and 
                                         m["period"] == final_period and
                                         m["region"] == "ALL" and
                                         m["cohort"] == "ALL" and
                                         m["age_bracket"] == "ALL"]
            
            total_eligible = total_eligible_metrics[0]["value"] if total_eligible_metrics else 0
            
            # Get total enrolled population
            total_enrolled_metrics = [m for m in results["metrics"] 
                                      if m["type"] == "derived" and 
                                         m["id"] == "total_enrolled_population" and 
                                         m["period"] == final_period and
                                         m["region"] == "ALL" and
                                         m["cohort"] == "ALL" and
                                         m["age_bracket"] == "ALL"]
            
            total_enrolled = total_enrolled_metrics[0]["value"] if total_enrolled_metrics else 0
            
            # Get enrollment rate
            enrollment_rate_metrics = [m for m in results["metrics"] 
                                      if m["type"] == "derived" and 
                                         m["id"] == "enrollment_rate" and 
                                         m["period"] == final_period and
                                         m["region"] == "ALL" and
                                         m["cohort"] == "ALL" and
                                         m["age_bracket"] == "ALL"]
            
            enrollment_rate = enrollment_rate_metrics[0]["value"] if enrollment_rate_metrics else 0
            
            print(f"\nFinal Enrollment Metrics (Period {final_period}):")
            print(f"  Total Eligible Population: {total_eligible:,}")
            print(f"  Total Enrolled Population: {total_enrolled:,}")
            print(f"  Enrollment Rate: {enrollment_rate:.2%}")
            
            # Calculate financial metrics
            expenditure_metrics = [m for m in results["metrics"] 
                                  if m["type"] == "financial" and 
                                     m["id"] == "claim_expenditure" and
                                     m["region"] == "ALL" and
                                     m["cohort"] == "ALL" and
                                     m["age_bracket"] == "ALL"]
            
            total_expenditure = sum(m["value"] for m in expenditure_metrics)
            
            if total_expenditure > 0:
                print("\nFinancial Metrics:")
                print(f"  Total Expenditure: ${total_expenditure:,.2f}")
                
                if total_enrolled > 0:
                    print(f"  Average Expenditure per Enrollee: ${total_expenditure / total_enrolled:,.2f}")
        else:
            print("\nNo metrics generated in the simulation.")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error running simulation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
