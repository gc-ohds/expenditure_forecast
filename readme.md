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
- **Flexible Output Formats**: Generate results in JSON or CSV format for easy analysis

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/gc-ohds/expenditure_forecast.git
   cd expenditure_forecast
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
- `--output-format`: Format for output files - json, csv, or both (default: "json")
- `--list-scenarios`: List available scenarios and exit
- `--verbose`, `-v`: Enable verbose logging

### Example

```
python main.py --scenario simple_scenario --start-date 2025-04-01 --end-date 2026-03-31 --output-format csv --verbose
```

### Output Formats

The simulation can output results in two formats:

#### JSON Format

The default output format is JSON, which provides a structured representation of all simulation metrics:

```
python main.py --scenario simple_scenario --output-format json
```

#### CSV Format

For easier data analysis, the simulation can output results as CSV files:

```
python main.py --scenario simple_scenario --output-format csv
```

This generates multiple CSV files in the output directory:
- `[base_filename]_state_metrics.csv`: Metrics for population states
- `[base_filename]_flow_metrics.csv`: Metrics for population flows
- `[base_filename]_financial_metrics.csv`: Financial metrics
- `[base_filename]_derived_metrics.csv`: Derived metrics (e.g., enrollment rates)
- `[base_filename]_simulation_params.csv`: Simulation parameters

#### Both Formats

You can also generate both JSON and CSV formats simultaneously:

```
python main.py --scenario simple_scenario --output-format both
```

### Data Analysis

The CSV output files are designed for easy import into data analysis tools:

- Each row represents a single metric value with all its dimensions (type, id, period, region, cohort, age_bracket, segment)
- Files are organized by metric type for convenient analysis
- The normalized structure is compatible with spreadsheet applications and tools like pandas

Example of analyzing with pandas:

```python
import pandas as pd

# Load state metrics
state_df = pd.read_csv('output/simulation_results_simple_scenario_20250514_state_metrics.csv')

# Create a pivot table of state populations over time
pivot_table = pd.pivot_table(
    state_df,
    values='value',
    index='period',
    columns=['id', 'region'],
    aggfunc='sum'
)

# Filter for a specific state
eligible_df = state_df[state_df['id'] == 'eligible']
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

This implementation represents Phase 1 (Core Framework & Minimal Viable Simulation)

### Phase 1: Core Framework & Minimal Viable Simulation (4 weeks)
1. **Core Infrastructure**:
   - `ConfigurationManager` (basic version for loading simple YAML configs)
   - `TimeManager` (complete implementation)
   - Simple test configuration files

2. **Minimal Population Tracking**:
   - `ProcessState` (complete implementation)
   - `PopulationSegment` (basic implementation with key methods)
   - `Region` (minimal implementation)
   
3. **Basic Process Framework**:
   - `ProcessStep` (base class with core functionality)
   - `ProcessResult` (complete implementation)
   - Simple `PopulationFlow` implementation
   
4. **Core Simulation Framework**:
   - `Simulation` (basic skeleton with time progression)
   - Simple CLI interface in `main.py`
   - Basic `StatisticsTracker` for essential metrics
   
5. **Testing Framework**:
   - Unit tests for core components
   - Simple end-to-end test with mock data

### Phase 2: Enrollment Process Slice (3 weeks)
- Enhanced application generation and processing
- Rollout schedule functionality
- Enhanced enrollment metrics

### Phase 3: Claims & Utilization Process Slice (3 weeks)
- Benefit structure implementation
- Claim generation and processing
- Financial calculations

### Phase 4: Complete Integration & Advanced Features (3 weeks)
- Integration of all components
- Advanced statistical distributions
- Duration-based claiming patterns
- Comprehensive reporting

### Phase 5: Refinement & Documentation (2 weeks)
- Performance optimization
- Comprehensive documentation
- Enhanced error handling
- Configuration validation tools