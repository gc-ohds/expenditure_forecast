# OHB Simulation Model

A simulation model for Ontario Health Benefits enrollment and expenditure forecasting.

## Overview

The OHB Simulation Model is a flexible and comprehensive simulation tool designed to model the enrollment and utilization processes of health benefit programs. It allows for forecasting population flows through different states of the program, from eligibility to enrollment to claim submission, and calculates expenditures based on utilization patterns.

This implementation represents Phase 1 of the development, focusing on creating a minimal viable simulation that can process basic population flows.

## Features

- **Time-based Simulation**: Progress through monthly, quarterly, or annual time intervals
- **Population Segmentation**: Model different demographic groups with varying characteristics
- **Geographic Regions**: Support for region-specific population segments and adjustment factors
- **Configurable Flow Rates**: Define rates for transitions between population states
- **Fiscal Year Tracking**: Handle fiscal year transitions and state resets
- **Statistical Tracking**: Capture detailed metrics throughout the simulation
- **Scenario-based Configuration**: Run different scenarios with configuration variations

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/ohb-simulation.git
   cd ohb-simulation
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the package in development mode:
   ```
   pip install -e .
   ```

## Project Structure

```
ohb_simulation/
│
├── __init__.py                    # Package initialization
├── main.py                        # Entry point for running simulations
│
├── core/                          # Core simulation components
│   ├── __init__.py
│   ├── simulation.py              # Main Simulation class
│   ├── config_manager.py          # Configuration management
│   ├── time_manager.py            # Time progression handling
│   └── constants.py               # System constants
│
├── population/                    # Population tracking components
│   ├── __init__.py
│   ├── region.py                  # Regional population handling
│   ├── segment.py                 # Population segments
│   ├── state.py                   # Population states
│   └── flow.py                    # Population transitions
│
├── process/                       # Process implementation
│   ├── __init__.py
│   ├── process_step.py            # Base process step class
│   └── process_result.py          # Results from process steps
│
├── stats/                         # Statistics and reporting
│   ├── __init__.py
│   └── statistics_tracker.py      # Metrics tracking
│
├── config/                        # Configuration files
│   ├── base_config.yaml           # Base configuration
│   └── scenarios/                 # Scenario-specific configs
│       └── simple_scenario.yaml   # Simple test scenario
│
└── tests/                         # Unit tests
    ├── __init__.py
    ├── test_time_manager.py
    ├── test_config_manager.py
    └── test_simulation.py
```

## Usage

### Running a Simulation

The simulation can be run from the command line using the `main.py` script:

```
python main.py --scenario simple_scenario --start-date 2025-04-01 --end-date 2026-03-31
```

### Command Line Arguments

- `--scenario`: Name of the scenario to run (default: "simple_scenario")
- `--start-date`: Start date for simulation in YYYY-MM-DD format (default: "2025-04-01")
- `--end-date`: End date for simulation in YYYY-MM-DD format (default: "2026-03-31")
- `--time-interval`: Time interval for simulation progression - MONTHLY, QUARTERLY, or ANNUAL (default: "MONTHLY")
- `--config-dir`: Directory containing configuration files (default: "config")
- `--output-dir`: Directory for output files (default: "output")
- `--list-scenarios`: List available scenarios and exit
- `--verbose`, `-v`: Enable verbose logging

### Example

```
python main.py --scenario simple_scenario --start-date 2025-04-01 --end-date 2026-03-31 --verbose
```

### Configuration

The simulation uses YAML configuration files to define scenarios, population segments, flow rates, and other parameters. See the `config/` directory for examples.

#### Base Configuration

The `base_config.yaml` file defines the core structure of the simulation, including:

- Time progression parameters
- State definitions
- Flow definitions
- Default flow rates

#### Scenario Configuration

Scenario-specific files in the `config/scenarios/` directory extend the base configuration with:

- Region definitions
- Population segment definitions
- Scenario-specific flow rates
- Adjustment factors

### Creating Custom Scenarios

To create a custom scenario:

1. Create a new YAML file in the `config/scenarios/` directory (e.g., `my_scenario.yaml`)
2. Define scenario-specific parameters (regions, population segments, flow rates, etc.)
3. Run the simulation with your custom scenario:
   ```
   python main.py --scenario my_scenario
   ```

## Testing

Run the test suite to verify the functionality of the simulation components:

```
python -m unittest discover -s ohb_simulation/tests
```

## Development Roadmap

This implementation represents Phase 1 (Core Framework & Minimal Viable Simulation) of the "Hybrid Implementation with Vertical Slices" approach. Future phases will include:

### Phase 2: Enrollment Process Slice (3-4 weeks)
- Enhanced application generation and processing
- Rollout schedule functionality
- Enhanced enrollment metrics

### Phase 3: Claims & Utilization Process Slice (4-5 weeks)
- Benefit structure implementation
- Claim generation and processing
- Financial calculations

### Phase 4: Complete Integration & Advanced Features (4-6 weeks)
- Integration of all components
- Advanced statistical distributions
- Duration-based claiming patterns
- Comprehensive reporting

### Phase 5: Refinement & Documentation (2-3 weeks)
- Performance optimization
- Comprehensive documentation
- Enhanced error handling
- Configuration validation tools

## License

[License information]

## Contact

[Contact information]
