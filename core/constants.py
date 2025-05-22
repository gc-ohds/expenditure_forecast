"""
Constants module for OHB Simulation Model.

This module defines system-wide constants used throughout the simulation.
"""

# State identifiers
STATE_ELIGIBLE = "eligible"
STATE_RE_ENROLLMENT_ELIGIBLE = "re_enrollment_eligible"
STATE_APPLIED = "applied"
STATE_ENROLLED_INACTIVE = "enrolled_inactive"
STATE_ACTIVE_CLAIMANT = "active_claimant"
STATE_NON_ELIGIBLE = "non_eligible"


# Flow identifiers
FLOW_NEW_APPLICATIONS = "new_applications"
FLOW_NEW_RE_ENROLLMENT_APPLICATIONS = "new_re_enrollment_applications"
FLOW_NEW_ENROLLMENTS = "new_enrollments"
FLOW_NEW_RE_ENROLLMENT = "new_re_enrollment"
FLOW_NEW_FIRST_CLAIMANTS = "new_first_claimants"
FLOW_NEW_SUBSEQUENT_CLAIMANTS = "new_subsequent_claimants"

# Cohort types
COHORT_SENIORS = "seniors"
COHORT_PWD = "pwd"
COHORT_CHILDREN = "children"
COHORT_ADULTS = "adults"

# Age brackets
AGE_BRACKET_65PLUS = "65plus"
AGE_BRACKET_18TO64 = "18to64"
AGE_BRACKET_U18 = "u18"

# Metric types
METRIC_TYPE_STATE = "state"
METRIC_TYPE_FLOW = "flow"
METRIC_TYPE_FINANCIAL = "financial"
METRIC_TYPE_DERIVED = "derived"

# Financial metric identifiers
FINANCIAL_CLAIM_EXPENDITURE = "claim_expenditure"
FINANCIAL_PROGRAM_EXPENDITURE = "program_expenditure"
FINANCIAL_PATIENT_EXPENDITURE = "patient_expenditure"
FINANCIAL_CUMULATIVE_EXPENDITURE = "cumulative_expenditure"

# Derived metric identifiers
DERIVED_TOTAL_ELIGIBLE_POPULATION = "total_eligible_population"
DERIVED_TOTAL_ENROLLED_POPULATION = "total_enrolled_population"
DERIVED_ENROLLMENT_RATE = "enrollment_rate"
DERIVED_EXPENDITURE_PER_ENROLLEE = "expenditure_per_enrollee"
DERIVED_EXPENDITURE_PER_CLAIM = "expenditure_per_claim"
