"""
Tests for RolloutSchedule class.
"""

import unittest
import datetime
from util.rollout import RolloutSchedule, RolloutPhase


class TestRolloutSchedule(unittest.TestCase):
    """Test cases for the RolloutSchedule class."""
    
    def setUp(self):
        """Set up test environment."""
        self.rollout = RolloutSchedule()
        
        # Add test phases
        phase1 = RolloutPhase(
            phase_id="phase1",
            cohort_id="seniors",
            age_min=65,
            age_max=120,
            start_date="2025-04-01",
            description="Seniors 65+ initial rollout"
        )
        
        phase2 = RolloutPhase(
            phase_id="phase2",
            cohort_id="pwd",
            age_min=18,
            age_max=64,
            start_date="2025-05-01",
            description="Persons with disabilities aged 18-64"
        )
        
        phase3 = RolloutPhase(
            phase_id="phase3",
            cohort_id="children",
            age_min=0,
            age_max=17,
            start_date="2025-06-01",
            description="Children under 18"
        )
        
        self.rollout.add_phase(phase1)
        self.rollout.add_phase(phase2)
        self.rollout.add_phase(phase3)
    
    def test_is_active(self):
        """Test checking if a phase is active."""
        phase = self.rollout.phases[0]  # Seniors phase
        
        # Before start date
        before_date = datetime.date(2025, 3, 31)
        self.assertFalse(phase.is_active(before_date))
        
        # On start date
        start_date = datetime.date(2025, 4, 1)
        self.assertTrue(phase.is_active(start_date))
        
        # After start date
        after_date = datetime.date(2025, 4, 15)
        self.assertTrue(phase.is_active(after_date))
    
    def test_get_eligible_cohorts(self):
        """Test getting eligible cohorts at a date."""
        # Before any phase
        before_date = datetime.date(2025, 3, 31)
        cohorts = self.rollout.get_eligible_cohorts(before_date)
        self.assertEqual(cohorts, [])
        
        # After first phase
        date1 = datetime.date(2025, 4, 15)
        cohorts = self.rollout.get_eligible_cohorts(date1)
        self.assertEqual(cohorts, ["seniors"])
        
        # After second phase
        date2 = datetime.date(2025, 5, 15)
        cohorts = self.rollout.get_eligible_cohorts(date2)
        self.assertEqual(sorted(cohorts), ["pwd", "seniors"])
        
        # After all phases
        date3 = datetime.date(2025, 6, 15)
        cohorts = self.rollout.get_eligible_cohorts(date3)
        self.assertEqual(sorted(cohorts), ["children", "pwd", "seniors"])
    
    def test_get_eligible_age_brackets(self):
        """Test getting eligible age brackets for a cohort."""
        date = datetime.date(2025, 5, 15)
        
        # Seniors cohort
        brackets = self.rollout.get_eligible_age_brackets("seniors", date)
        self.assertEqual(brackets, [(65, 120)])
        
        # PWD cohort
        brackets = self.rollout.get_eligible_age_brackets("pwd", date)
        self.assertEqual(brackets, [(18, 64)])
        
        # Children cohort (not eligible yet)
        brackets = self.rollout.get_eligible_age_brackets("children", date)
        self.assertEqual(brackets, [])
    
    def test_is_cohort_age_eligible(self):
        """Test checking if specific cohort and age is eligible."""
        date = datetime.date(2025, 5, 15)
        
        # Eligible: seniors aged 70
        self.assertTrue(self.rollout.is_cohort_age_eligible("seniors", 70, date))
        
        # Eligible: PWD aged 30
        self.assertTrue(self.rollout.is_cohort_age_eligible("pwd", 30, date))
        
        # Not eligible: children aged 10 (phase not active yet)
        self.assertFalse(self.rollout.is_cohort_age_eligible("children", 10, date))
        
        # Not eligible: seniors aged 60 (below age range)
        self.assertFalse(self.rollout.is_cohort_age_eligible("seniors", 60, date))
        
        # Not eligible: unknown cohort
        self.assertFalse(self.rollout.is_cohort_age_eligible("unknown", 30, date))


if __name__ == '__main__':
    unittest.main()