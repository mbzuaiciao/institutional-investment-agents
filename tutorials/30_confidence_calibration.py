"""Tutorial 30: confidence is evaluated against empirical correctness."""

from institutional_investment_agents.phase3_metrics import calibration_metrics
from institutional_investment_agents.phase3_schemas import ClaimCalibrationRecord

claims = (
    ClaimCalibrationRecord(confidence=.9, correct_or_supported=True),
    ClaimCalibrationRecord(confidence=.8, correct_or_supported=False),
    ClaimCalibrationRecord(confidence=.3, correct_or_supported=False),
)
print(calibration_metrics(claims))
