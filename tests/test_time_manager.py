"""
Tests for TimeManager class.
"""

import unittest
import datetime
from dateutil.relativedelta import relativedelta
from core.time_manager import TimeManager, TimeInterval


class TestTimeManager(unittest.TestCase):
    """Test cases for the TimeManager class."""
    
    def test_initialization(self):
        """Test initialization of TimeManager."""
        start_date = datetime.date(2025, 4, 1)
        tm = TimeManager(start_date)
        
        self.assertEqual(tm.start_date, start_date)
        self.assertEqual(tm.current_date, start_date)
        self.assertEqual(tm.time_interval, TimeInterval.MONTHLY)
        self.assertEqual(tm.fiscal_year_start_month, 4)
        self.assertEqual(tm.fiscal_year_start_day, 1)
        
        # Test string date conversion
        tm2 = TimeManager("2025-04-01")
        self.assertEqual(tm2.start_date, start_date)
    
    def test_advance_time_monthly(self):
        """Test advancing time with monthly interval."""
        start_date = datetime.date(2025, 4, 1)
        tm = TimeManager(start_date, TimeInterval.MONTHLY)
        
        # Advance one month
        fiscal_transition = tm.advance_time()
        expected_date = start_date + relativedelta(months=1)
        
        self.assertEqual(tm.current_date, expected_date)
        self.assertFalse(fiscal_transition)
        
        # Advance to fiscal year boundary
        # Set date to just before fiscal year end
        tm.current_date = datetime.date(2026, 3, 1)
        fiscal_transition = tm.advance_time()
        
        self.assertEqual(tm.current_date, datetime.date(2026, 4, 1))
        self.assertTrue(fiscal_transition)
    
    def test_advance_time_quarterly(self):
        """Test advancing time with quarterly interval."""
        start_date = datetime.date(2025, 4, 1)
        tm = TimeManager(start_date, TimeInterval.QUARTERLY)
        
        # Advance one quarter
        tm.advance_time()
        expected_date = start_date + relativedelta(months=3)
        
        self.assertEqual(tm.current_date, expected_date)
    
    def test_advance_time_annual(self):
        """Test advancing time with annual interval."""
        start_date = datetime.date(2025, 4, 1)
        tm = TimeManager(start_date, TimeInterval.ANNUAL)
        
        # Advance one year
        fiscal_transition = tm.advance_time()
        expected_date = start_date + relativedelta(years=1)
        
        self.assertEqual(tm.current_date, expected_date)
        self.assertTrue(fiscal_transition)
    
    def test_is_fiscal_year_start(self):
        """Test checking for fiscal year start date."""
        # Initialize on fiscal year start
        tm = TimeManager(datetime.date(2025, 4, 1))
        self.assertTrue(tm.is_fiscal_year_start())
        
        # Advance to non-fiscal year start
        tm.advance_time()
        self.assertFalse(tm.is_fiscal_year_start())
        
        # Set to next fiscal year start
        tm.current_date = datetime.date(2026, 4, 1)
        self.assertTrue(tm.is_fiscal_year_start())
    
    def test_get_current_period(self):
        """Test getting string representation of current period."""
        # Monthly
        tm = TimeManager(datetime.date(2025, 4, 1), TimeInterval.MONTHLY)
        self.assertEqual(tm.get_current_period(), "2025-04")
        
        # Quarterly
        tm = TimeManager(datetime.date(2025, 4, 1), TimeInterval.QUARTERLY)
        self.assertEqual(tm.get_current_period(), "2025-Q2")
        
        # Annual
        tm = TimeManager(datetime.date(2025, 4, 1), TimeInterval.ANNUAL)
        self.assertEqual(tm.get_current_period(), "2025")
    
    def test_get_months_since(self):
        """Test calculating months between dates."""
        tm = TimeManager(datetime.date(2025, 7, 15))
        
        # Test with reference date 3 months earlier
        reference_date = datetime.date(2025, 4, 15)
        self.assertEqual(tm.get_months_since(reference_date), 3)
        
        # Test with reference date 1 year earlier
        reference_date = datetime.date(2024, 7, 15)
        self.assertEqual(tm.get_months_since(reference_date), 12)
        
        # Test with string date
        self.assertEqual(tm.get_months_since("2025-04-15"), 3)
    
    def test_get_current_fiscal_year(self):
        """Get the current fiscal year identifier using start year convention."""
        # Start of fiscal year
        tm = TimeManager(datetime.date(2025, 4, 1))
        self.assertEqual(tm.get_current_fiscal_year(), "FY2025")
        
        # Middle of fiscal year
        tm.current_date = datetime.date(2025, 9, 1)
        self.assertEqual(tm.get_current_fiscal_year(), "FY2025")
        
        # Just before next fiscal year
        tm.current_date = datetime.date(2026, 3, 31)
        self.assertEqual(tm.get_current_fiscal_year(), "FY2025")
        
        # Start of next fiscal year
        tm.current_date = datetime.date(2026, 4, 1)
        self.assertEqual(tm.get_current_fiscal_year(), "FY2026")


if __name__ == '__main__':
    unittest.main()
