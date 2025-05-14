"""
Time Manager module for OHB Simulation Model.

This module provides the TimeManager class, which manages time progression during
the simulation and provides utilities for date-related calculations.
"""

import datetime
from dateutil.relativedelta import relativedelta
from enum import Enum, auto


class TimeInterval(Enum):
    """Enumeration of possible time intervals for simulation progression."""
    MONTHLY = auto()
    QUARTERLY = auto()
    ANNUAL = auto()


class TimeManager:
    """
    Manages time progression during simulation.
    
    The TimeManager is responsible for tracking the current date in the simulation,
    advancing time by specified intervals, and determining fiscal year transitions.
    """
    
    def __init__(self, start_date, time_interval=TimeInterval.MONTHLY, 
                 fiscal_year_start_month=4, fiscal_year_start_day=1):
        """
        Initialize with start date and time interval.
        
        Args:
            start_date (datetime.date): The starting date for the simulation.
            time_interval (TimeInterval): The interval for time progression.
            fiscal_year_start_month (int): Month when fiscal year starts (1-12).
            fiscal_year_start_day (int): Day when fiscal year starts (1-31).
        """
        if isinstance(start_date, str):
            # Convert string date to datetime.date
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            
        self.start_date = start_date
        self.current_date = start_date
        
        if isinstance(time_interval, str):
            time_interval = TimeInterval[time_interval.upper()]
        self.time_interval = time_interval
        
        self.fiscal_year_start_month = fiscal_year_start_month
        self.fiscal_year_start_day = fiscal_year_start_day
        
        # Calculate the first fiscal year start date on or before the start date
        self._calculate_fiscal_year_start()
    
    def _calculate_fiscal_year_start(self):
        """Calculate the fiscal year start date for the current date."""
        year = self.current_date.year
        fiscal_start = datetime.date(year, self.fiscal_year_start_month, 
                                    self.fiscal_year_start_day)
        
        # If current date is before this year's fiscal start,
        # we're in the previous fiscal year
        if self.current_date < fiscal_start:
            fiscal_start = datetime.date(year - 1, self.fiscal_year_start_month, 
                                         self.fiscal_year_start_day)
        
        self.fiscal_year_start_date = fiscal_start
    
    def advance_time(self):
        """
        Advance time by one interval.
        
        Returns:
            datetime.date: The new current date after advancing.
        """
        if self.time_interval == TimeInterval.MONTHLY:
            self.current_date = self.current_date + relativedelta(months=1)
        elif self.time_interval == TimeInterval.QUARTERLY:
            self.current_date = self.current_date + relativedelta(months=3)
        elif self.time_interval == TimeInterval.ANNUAL:
            self.current_date = self.current_date + relativedelta(years=1)
        
        # Check if we've crossed into a new fiscal year
        next_fiscal_start = datetime.date(
            self.fiscal_year_start_date.year + 1,
            self.fiscal_year_start_month,
            self.fiscal_year_start_day
        )
        
        if self.current_date >= next_fiscal_start:
            self.fiscal_year_start_date = next_fiscal_start
            return True  # Indicate fiscal year transition
        
        return False  # No fiscal year transition
    
    def is_fiscal_year_start(self):
        """
        Check if current date is the start of a fiscal year.
        
        Returns:
            bool: True if the current date is a fiscal year start date.
        """
        return (self.current_date.month == self.fiscal_year_start_month and
                self.current_date.day == self.fiscal_year_start_day)
    
    def get_current_period(self):
        """
        Get string representation of current period.
        
        Returns:
            str: A string representing the current period (e.g., "2025-04").
        """
        if self.time_interval == TimeInterval.MONTHLY:
            return self.current_date.strftime("%Y-%m")
        elif self.time_interval == TimeInterval.QUARTERLY:
            quarter = (self.current_date.month - 1) // 3 + 1
            return f"{self.current_date.year}-Q{quarter}"
        elif self.time_interval == TimeInterval.ANNUAL:
            return str(self.current_date.year)
    
    def get_months_since(self, reference_date):
        """
        Calculate months between reference date and current date.
        
        Args:
            reference_date (datetime.date): The reference date.
            
        Returns:
            int: Number of months between the reference and current date.
        """
        if isinstance(reference_date, str):
            reference_date = datetime.datetime.strptime(reference_date, "%Y-%m-%d").date()
            
        delta = relativedelta(self.current_date, reference_date)
        return delta.years * 12 + delta.months
    
    def get_current_fiscal_year(self):
        """
        Get the current fiscal year identifier.
        
        Returns:
            str: String representing the fiscal year (e.g., "FY2025").
        """
        if self.current_date < self.fiscal_year_start_date:
            year = self.fiscal_year_start_date.year - 1
        else:
            year = self.fiscal_year_start_date.year
            
        return f"FY{year}"
    
    def __str__(self):
        """Return string representation of the TimeManager."""
        return (f"TimeManager(current_date={self.current_date}, "
                f"interval={self.time_interval.name}, "
                f"fiscal_year={self.get_current_fiscal_year()})")
