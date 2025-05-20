"""
Statistics Tracker module for OHB Simulation Model.

This module provides the StatisticsTracker class, which tracks all statistics
during simulation using a normalized data structure.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class StatisticsTracker:
    """
    Tracks all statistics during simulation.
    
    The StatisticsTracker aggregates and maintains metrics throughout the
    simulation using a normalized data structure that's suitable for
    tabular analysis.
    """
    
    def __init__(self):
        """Initialize statistics tracker with empty metric records list."""
        # Use a list of metric records instead of nested dictionaries
        self.metrics = []
        
        # Keep a cache of metrics for efficient lookup during simulation
        # This avoids having to search through the metrics list repeatedly
        self._metric_cache = defaultdict(dict)
    
    def update_state_metrics(self, regions, time_manager):
        """
        Update state metrics based on current population states.
        
        Args:
            regions (list): List of regions with population segments.
            time_manager (TimeManager): Time manager for current period.
            
        Returns:
            list: Updated state metrics records.
        """
        period = time_manager.get_current_period()
        new_metrics = []
        
        # Calculate total population across all regions first
        total_by_state = defaultdict(int)
        total_by_state_cohort = defaultdict(lambda: defaultdict(int))
        total_by_state_age = defaultdict(lambda: defaultdict(int))
        
        for region in regions:
            region_id = region.region_id
            
            # Calculate region totals
            region_total_by_state = defaultdict(int)
            
            for segment in region.population_segments:
                segment_id = segment.segment_id
                cohort_type = segment.cohort_type
                age_bracket = segment.age_bracket.bracket_name
                
                for state_id, state in segment.states.items():
                    population = state.get_population()
                    
                    # Skip zero population states
                    if population <= 0:
                        continue
                    
                    # Add segment-level metric
                    segment_metric = {
                        "type": "state",
                        "id": state_id,
                        "period": period,
                        "region": region_id,
                        "cohort": cohort_type,
                        "age_bracket": age_bracket,
                        "segment": segment_id,
                        "value": population
                    }
                    new_metrics.append(segment_metric)
                    
                    # Update cache for this specific metric
                    cache_key = f"state:{state_id}:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                    self._metric_cache[cache_key] = population
                    
                    # Update aggregation counters
                    region_total_by_state[state_id] += population
                    total_by_state[state_id] += population
                    total_by_state_cohort[state_id][cohort_type] += population
                    total_by_state_age[state_id][age_bracket] += population
            
            # Add region-level aggregated metrics
            for state_id, population in region_total_by_state.items():
                region_metric = {
                    "type": "state",
                    "id": state_id,
                    "period": period,
                    "region": region_id,
                    "cohort": "ALL",
                    "age_bracket": "ALL",
                    "segment": "ALL",
                    "value": population
                }
                new_metrics.append(region_metric)
                
                # Update cache
                cache_key = f"state:{state_id}:{period}:{region_id}:ALL:ALL:ALL"
                self._metric_cache[cache_key] = population
        
        # Add cohort-level aggregated metrics
        for state_id, cohorts in total_by_state_cohort.items():
            for cohort_type, population in cohorts.items():
                cohort_metric = {
                    "type": "state",
                    "id": state_id,
                    "period": period,
                    "region": "ALL",
                    "cohort": cohort_type,
                    "age_bracket": "ALL",
                    "segment": "ALL",
                    "value": population
                }
                new_metrics.append(cohort_metric)
                
                # Update cache
                cache_key = f"state:{state_id}:{period}:ALL:{cohort_type}:ALL:ALL"
                self._metric_cache[cache_key] = population
        
        # Add age-level aggregated metrics
        for state_id, ages in total_by_state_age.items():
            for age_bracket, population in ages.items():
                age_metric = {
                    "type": "state",
                    "id": state_id,
                    "period": period,
                    "region": "ALL",
                    "cohort": "ALL",
                    "age_bracket": age_bracket,
                    "segment": "ALL",
                    "value": population
                }
                new_metrics.append(age_metric)
                
                # Update cache
                cache_key = f"state:{state_id}:{period}:ALL:ALL:{age_bracket}:ALL"
                self._metric_cache[cache_key] = population
        
        # Add total-level aggregated metrics
        for state_id, population in total_by_state.items():
            total_metric = {
                "type": "state",
                "id": state_id,
                "period": period,
                "region": "ALL",
                "cohort": "ALL",
                "age_bracket": "ALL",
                "segment": "ALL",
                "value": population
            }
            new_metrics.append(total_metric)
            
            # Update cache
            cache_key = f"state:{state_id}:{period}:ALL:ALL:ALL:ALL"
            self._metric_cache[cache_key] = population
        
        # Add new metrics to the overall list
        self.metrics.extend(new_metrics)
        
        # Calculate derived state metrics
        self.calculate_derived_state_metrics(period)
        
        return new_metrics
    
    def update_flow_metric(self, flow_id, period, count, segment_id=None, region_id=None, 
                          cohort_type=None, age_bracket=None):
        """
        Update a specific flow metric.
        
        Args:
            flow_id (str): Flow identifier.
            period (str): Time period identifier.
            count (int): Flow count to add.
            segment_id (str, optional): Segment identifier for segmented metrics.
            region_id (str, optional): Region identifier.
            cohort_type (str, optional): Cohort type.
            age_bracket (str, optional): Age bracket.
            
        Returns:
            dict: The created or updated metric record.
        """
        # If segment_id is provided but other dimensions aren't, extract them from segment_id
        if segment_id and (not region_id or not cohort_type or not age_bracket):
            # For Phase 1, use a simple parsing of segment_id format: cohort_age_region
            if '_' in segment_id:
                parts = segment_id.split('_')
                if len(parts) >= 3:
                    if not cohort_type:
                        cohort_type = parts[0]
                    if not age_bracket:
                        age_bracket = parts[1]
                    if not region_id:
                        region_id = parts[2]
        
        # Default values for missing dimensions
        region_id = region_id or "ALL"
        cohort_type = cohort_type or "ALL"
        age_bracket = age_bracket or "ALL"
        segment_id = segment_id or "ALL"
        
        # Create flow metric record
        flow_metric = {
            "type": "flow",
            "id": flow_id,
            "period": period,
            "region": region_id,
            "cohort": cohort_type,
            "age_bracket": age_bracket,
            "segment": segment_id,
            "value": count
        }
        
        # Add to metrics list
        self.metrics.append(flow_metric)
        
        # Update cache
        cache_key = f"flow:{flow_id}:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
        
        # Sum with any existing value in cache
        current_value = self._metric_cache.get(cache_key, 0)
        self._metric_cache[cache_key] = current_value + count
        
        # Also update the total flow metric
        total_cache_key = f"flow:{flow_id}:{period}:ALL:ALL:ALL:ALL"
        total_current = self._metric_cache.get(total_cache_key, 0)
        total_value = total_current + count
        self._metric_cache[total_cache_key] = total_value
        
        # Add/update total metric record if needed
        self.metrics.append({
            "type": "flow",
            "id": flow_id,
            "period": period,
            "region": "ALL",
            "cohort": "ALL",
            "age_bracket": "ALL",
            "segment": "ALL",
            "value": total_value
        })
        
        return flow_metric
    
    def update_financial_metric(self, metric_id, period, amount, segment_id=None, 
                               region_id=None, cohort_type=None, age_bracket=None):
        """
        Update a specific financial metric.
        
        Args:
            metric_id (str): Metric identifier.
            period (str): Time period identifier.
            amount (float): Amount to add.
            segment_id (str, optional): Segment identifier for segmented metrics.
            region_id (str, optional): Region identifier.
            cohort_type (str, optional): Cohort type.
            age_bracket (str, optional): Age bracket.
            
        Returns:
            dict: The created or updated metric record.
        """
        # Similar parsing as update_flow_metric
        if segment_id and (not region_id or not cohort_type or not age_bracket):
            if '_' in segment_id:
                parts = segment_id.split('_')
                if len(parts) >= 3:
                    if not cohort_type:
                        cohort_type = parts[0]
                    if not age_bracket:
                        age_bracket = parts[1]
                    if not region_id:
                        region_id = parts[2]
        
        # Default values for missing dimensions
        region_id = region_id or "ALL"
        cohort_type = cohort_type or "ALL"
        age_bracket = age_bracket or "ALL"
        segment_id = segment_id or "ALL"
        
        # Create financial metric record
        financial_metric = {
            "type": "financial",
            "id": metric_id,
            "period": period,
            "region": region_id,
            "cohort": cohort_type,
            "age_bracket": age_bracket,
            "segment": segment_id,
            "value": amount
        }
        
        # Add to metrics list
        self.metrics.append(financial_metric)
        
        # Update cache
        cache_key = f"financial:{metric_id}:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
        
        # Sum with any existing value in cache
        current_value = self._metric_cache.get(cache_key, 0)
        self._metric_cache[cache_key] = current_value + amount
        
        # Also update the total financial metric
        total_cache_key = f"financial:{metric_id}:{period}:ALL:ALL:ALL:ALL"
        total_current = self._metric_cache.get(total_cache_key, 0)
        total_value = total_current + amount
        self._metric_cache[total_cache_key] = total_value
        
        # Add/update total metric record if needed
        self.metrics.append({
            "type": "financial",
            "id": metric_id,
            "period": period,
            "region": "ALL",
            "cohort": "ALL",
            "age_bracket": "ALL",
            "segment": "ALL",
            "value": total_value
        })
        
        return financial_metric
    
    def calculate_derived_state_metrics(self, period):
        """
        Calculate metrics derived from state metrics.
        
        Args:
            period (str): Time period identifier.
            
        Returns:
            list: List of derived metric records.
        """
        derived_metrics = []
        
        # Get required metrics from cache for all dimensions
        dimensions = self._get_all_dimensions()
        
        for dim in dimensions:
            region_id, cohort_type, age_bracket, segment_id = dim
            
            # Calculate total_eligible_population
            eligible_key = f"state:eligible:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            re_enrollment_key = f"state:re_enrollment_eligible:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            
            eligible = self._metric_cache.get(eligible_key, 0)
            re_enrollment_eligible = self._metric_cache.get(re_enrollment_key, 0)
            total_eligible = eligible + re_enrollment_eligible
            
            if total_eligible > 0:
                # Add total_eligible_population metric
                derived_metrics.append({
                    "type": "derived",
                    "id": "total_eligible_population",
                    "period": period,
                    "region": region_id,
                    "cohort": cohort_type,
                    "age_bracket": age_bracket,
                    "segment": segment_id,
                    "value": total_eligible
                })
                
                # Update cache
                self._metric_cache[f"derived:total_eligible_population:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = total_eligible
                
                # Calculate total_enrolled_population
                enrolled_inactive_key = f"state:enrolled_inactive:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                active_claimant_key = f"state:active_claimant:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                
                enrolled_inactive = self._metric_cache.get(enrolled_inactive_key, 0)
                active_claimant = self._metric_cache.get(active_claimant_key, 0)
                total_enrolled = enrolled_inactive + active_claimant
                
                # Add total_enrolled_population metric
                derived_metrics.append({
                    "type": "derived",
                    "id": "total_enrolled_population",
                    "period": period,
                    "region": region_id,
                    "cohort": cohort_type,
                    "age_bracket": age_bracket,
                    "segment": segment_id,
                    "value": total_enrolled
                })
                
                # Update cache
                self._metric_cache[f"derived:total_enrolled_population:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = total_enrolled
                
                # Calculate enrollment_rate
                if total_eligible > 0:
                    enrollment_rate = total_enrolled / total_eligible
                    
                    # Add enrollment_rate metric
                    derived_metrics.append({
                        "type": "derived",
                        "id": "enrollment_rate",
                        "period": period,
                        "region": region_id,
                        "cohort": cohort_type,
                        "age_bracket": age_bracket,
                        "segment": segment_id,
                        "value": enrollment_rate
                    })
                    
                    # Update cache
                    self._metric_cache[f"derived:enrollment_rate:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = enrollment_rate
        
        # Add derived metrics to the overall list
        self.metrics.extend(derived_metrics)
        
        return derived_metrics
    
    def calculate_derived_financial_metrics(self, period):
        """
        Calculate metrics derived from financial metrics.
        
        Args:
            period (str): Time period identifier.
            
        Returns:
            list: List of derived financial metric records.
        """
        derived_metrics = []
        
        # Get required metrics from cache for all dimensions
        dimensions = self._get_all_dimensions()
        
        for dim in dimensions:
            region_id, cohort_type, age_bracket, segment_id = dim
            
            # Get claim expenditure
            claim_expenditure_key = f"financial:claim_expenditure:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            claim_expenditure = self._metric_cache.get(claim_expenditure_key, 0)
            
            if claim_expenditure > 0:
                # Get new enrollments and re-enrollments
                enrollments_key = f"flow:new_enrollments:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                re_enrollments_key = f"flow:new_re_enrollment:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                
                new_enrollments = self._metric_cache.get(enrollments_key, 0)
                new_re_enrollment = self._metric_cache.get(re_enrollments_key, 0)
                total_new_enrollees = new_enrollments + new_re_enrollment
                
                # Calculate expenditure_per_enrollee
                if total_new_enrollees > 0:
                    expenditure_per_enrollee = claim_expenditure / total_new_enrollees
                    
                    # Add expenditure_per_enrollee metric
                    derived_metrics.append({
                        "type": "derived",
                        "id": "expenditure_per_enrollee",
                        "period": period,
                        "region": region_id,
                        "cohort": cohort_type,
                        "age_bracket": age_bracket,
                        "segment": segment_id,
                        "value": expenditure_per_enrollee
                    })
                    
                    # Update cache
                    self._metric_cache[f"derived:expenditure_per_enrollee:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = expenditure_per_enrollee
                
                # Get claims
                first_claims_key = f"flow:new_first_claims:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                subsequent_claims_key = f"flow:new_subsequent_claims:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                
                first_claims = self._metric_cache.get(first_claims_key, 0)
                subsequent_claims = self._metric_cache.get(subsequent_claims_key, 0)
                total_claims = first_claims + subsequent_claims
                
                # Calculate expenditure_per_claim
                if total_claims > 0:
                    expenditure_per_claim = claim_expenditure / total_claims
                    
                    # Add expenditure_per_claim metric
                    derived_metrics.append({
                        "type": "derived",
                        "id": "expenditure_per_claim",
                        "period": period,
                        "region": region_id,
                        "cohort": cohort_type,
                        "age_bracket": age_bracket,
                        "segment": segment_id,
                        "value": expenditure_per_claim
                    })
                    
                    # Update cache
                    self._metric_cache[f"derived:expenditure_per_claim:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = expenditure_per_claim
        
        # Add derived metrics to the overall list
        self.metrics.extend(derived_metrics)
        
        return derived_metrics
    
    def update_cumulative_expenditure(self, time_manager):
        """
        Update cumulative expenditure for the current fiscal year.
        
        Args:
            time_manager (TimeManager): Time manager for current period.
            
        Returns:
            list: List of updated cumulative expenditure metric records.
        """
        period = time_manager.get_current_period()
        fiscal_year = time_manager.get_current_fiscal_year()
        cumulative_metrics = []
        
        # Reset cumulative expenditure at fiscal year start
        if time_manager.is_fiscal_year_start():
            # Clear the cache for cumulative_expenditure
            for key in list(self._metric_cache.keys()):
                if key.startswith("financial:cumulative_expenditure:"):
                    self._metric_cache[key] = 0
        
        # Get required metrics from cache for all dimensions
        dimensions = self._get_all_dimensions()
        
        for dim in dimensions:
            region_id, cohort_type, age_bracket, segment_id = dim
            
            # Get current period expenditure
            current_expenditure_key = f"financial:claim_expenditure:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            current_expenditure = self._metric_cache.get(current_expenditure_key, 0)
            
            if current_expenditure > 0:
                # Get current cumulative expenditure
                cumulative_key = f"financial:cumulative_expenditure:{fiscal_year}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
                current_cumulative = self._metric_cache.get(cumulative_key, 0)
                
                # Add current expenditure to cumulative
                new_cumulative = current_cumulative + current_expenditure
                
                # Update cache
                self._metric_cache[cumulative_key] = new_cumulative
                
                # Add cumulative_expenditure metric
                cumulative_metric = {
                    "type": "financial",
                    "id": "cumulative_expenditure",
                    "period": fiscal_year,
                    "region": region_id,
                    "cohort": cohort_type,
                    "age_bracket": age_bracket,
                    "segment": segment_id,
                    "value": new_cumulative
                }
                
                cumulative_metrics.append(cumulative_metric)
        
        # Add cumulative metrics to the overall list
        self.metrics.extend(cumulative_metrics)
        
        return cumulative_metrics
    
    def calculate_derived_metrics(self, time_manager):
        """
        Calculate metrics derived from other metrics.
        
        Args:
            time_manager (TimeManager): Time manager for current period.
            
        Returns:
            list: List of all derived metric records.
        """
        period = time_manager.get_current_period()
        derived_metrics = []
        
        # Calculate state-derived metrics
        state_metrics = self.calculate_derived_state_metrics(period)
        derived_metrics.extend(state_metrics)
        
        # Calculate enrollment-derived metrics
        enrollment_metrics = self.calculate_enrollment_metrics(period)
        derived_metrics.extend(enrollment_metrics)
        
        # Calculate financial-derived metrics
        financial_metrics = self.calculate_derived_financial_metrics(period)
        derived_metrics.extend(financial_metrics)
        
        # Update cumulative expenditure
        cumulative_metrics = self.update_cumulative_expenditure(time_manager)
        
        return derived_metrics
    
    def _get_all_dimensions(self):
        """
        Get all dimension combinations from the cache.
        
        Returns:
            list: List of dimension tuples (region, cohort, age_bracket, segment).
        """
        dimensions = set()
        
        # Extract dimensions from cache keys
        for key in self._metric_cache.keys():
            if ":" in key:
                parts = key.split(":")
                if len(parts) >= 7:  # type:id:period:region:cohort:age:segment
                    region = parts[3]
                    cohort = parts[4]
                    age = parts[5]
                    segment = parts[6]
                    dimensions.add((region, cohort, age, segment))
        
        # Always ensure the "ALL" dimension is included
        dimensions.add(("ALL", "ALL", "ALL", "ALL"))
        
        return list(dimensions)
    
    def get_all_metrics(self):
        """
        Get all metrics in the normalized format.
        
        Returns:
            list: List of all metric records.
        """
        return self.metrics
    
    def get_metrics_by_type(self, metric_type):
        """
        Get metrics filtered by type.
        
        Args:
            metric_type (str): Type of metrics to retrieve ("state", "flow", "financial", "derived").
            
        Returns:
            list: List of filtered metric records.
        """
        return [m for m in self.metrics if m["type"] == metric_type]
    
    def get_metrics_by_id(self, metric_id):
        """
        Get metrics filtered by ID.
        
        Args:
            metric_id (str): ID of metrics to retrieve.
            
        Returns:
            list: List of filtered metric records.
        """
        return [m for m in self.metrics if m["id"] == metric_id]
    
    def get_metrics_by_period(self, period):
        """
        Get metrics filtered by period.
        
        Args:
            period (str): Period of metrics to retrieve.
            
        Returns:
            list: List of filtered metric records.
        """
        return [m for m in self.metrics if m["period"] == period]
    
    def get_metrics_by_dimensions(self, region=None, cohort=None, age_bracket=None, segment=None):
        """
        Get metrics filtered by dimensions.
        
        Args:
            region (str, optional): Region to filter by.
            cohort (str, optional): Cohort to filter by.
            age_bracket (str, optional): Age bracket to filter by.
            segment (str, optional): Segment to filter by.
            
        Returns:
            list: List of filtered metric records.
        """
        filtered_metrics = self.metrics
        
        if region:
            filtered_metrics = [m for m in filtered_metrics if m["region"] == region]
        
        if cohort:
            filtered_metrics = [m for m in filtered_metrics if m["cohort"] == cohort]
        
        if age_bracket:
            filtered_metrics = [m for m in filtered_metrics if m["age_bracket"] == age_bracket]
        
        if segment:
            filtered_metrics = [m for m in filtered_metrics if m["segment"] == segment]
        
        return filtered_metrics
    
    def export_to_dict(self):
        """
        Export metrics to a dictionary suitable for JSON serialization.
        
        Returns:
            dict: Dictionary with metrics in normalized format.
        """
        return {
            "metrics": self.metrics
        }

    def export_to_dict(self):
        """
        Export metrics to a dictionary suitable for JSON serialization.
        
        Returns:
            dict: Dictionary with metrics in normalized format.
        """
        return {
            "metrics": self.metrics
        }
    
    def calculate_enrollment_metrics(self, period):
        """
        Calculate enrollment-specific metrics.
        
        Args:
            period (str): Time period identifier.
            
        Returns:
            list: List of enrollment metric records.
        """
        enrollment_metrics = []
        
        # Get all dimensions
        dimensions = self._get_all_dimensions()
        
        for dim in dimensions:
            region_id, cohort_type, age_bracket, segment_id = dim
            
            # Calculate application rate (new applications / eligible population)
            eligible_key = f"state:eligible:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            applications_key = f"flow:new_applications:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            
            eligible = self._metric_cache.get(eligible_key, 0)
            applications = self._metric_cache.get(applications_key, 0)
            
            if eligible > 0 and applications > 0:
                application_rate = applications / eligible
                
                # Add application_rate metric
                enrollment_metrics.append({
                    "type": "derived",
                    "id": "application_rate",
                    "period": period,
                    "region": region_id,
                    "cohort": cohort_type,
                    "age_bracket": age_bracket,
                    "segment": segment_id,
                    "value": application_rate
                })
                
                # Update cache
                self._metric_cache[f"derived:application_rate:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = application_rate
            
            # Calculate approval rate (new enrollments / new applications)
            enrollments_key = f"flow:new_enrollments:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"
            enrollments = self._metric_cache.get(enrollments_key, 0)
            
            if applications > 0 and enrollments > 0:
                approval_rate = enrollments / applications
                
                # Add approval_rate metric
                enrollment_metrics.append({
                    "type": "derived",
                    "id": "approval_rate",
                    "period": period,
                    "region": region_id,
                    "cohort": cohort_type,
                    "age_bracket": age_bracket,
                    "segment": segment_id,
                    "value": approval_rate
                })
                
                # Update cache
                self._metric_cache[f"derived:approval_rate:{period}:{region_id}:{cohort_type}:{age_bracket}:{segment_id}"] = approval_rate
        
        # Add metrics to the overall list
        self.metrics.extend(enrollment_metrics)
        
        return enrollment_metrics

    def export_to_csv(self, base_path):
        """
        Export metrics to CSV files, grouped by metric type.
        
        Args:
            base_path (str): Base path for CSV files (without extension).
            
        Returns:
            dict: Dictionary mapping metric types to file paths.
        """
        # Group metrics by type
        metrics_by_type = {}
        for metric in self.metrics:
            metric_type = metric['type']
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric)
        
        # Export each type to a separate CSV file
        file_paths = {}
        for metric_type, metrics in metrics_by_type.items():
            if not metrics:
                continue
                
            file_path = f"{base_path}_{metric_type}_metrics.csv"
            
            # Create CSV content
            header = metrics[0].keys()
            csv_rows = [','.join(str(row[col]) for col in header) for row in metrics]
            csv_content = ','.join(header) + '\n' + '\n'.join(csv_rows)
            
            # Write to file
            with open(file_path, 'w') as f:
                f.write(csv_content)
            
            file_paths[metric_type] = file_path
        
        return file_paths
    
    def export_to_pandas_compatible_dict(self):
        """
        Export metrics in a format directly compatible with pandas DataFrame.
        
        Returns:
            dict: Dictionary with metric data organized by columns.
        """
        # Skip this method if pandas is not available
        try:
            import pandas as pd
        except ImportError:
            return {"error": "pandas not available"}
        
        # Create a dictionary with column names as keys and lists of values
        column_data = {}
        
        if not self.metrics:
            return column_data
            
        # Initialize columns
        for column in self.metrics[0].keys():
            column_data[column] = []
            
        # Fill in data
        for metric in self.metrics:
            for column in column_data:
                column_data[column].append(metric.get(column, None))
                
        return column_data
