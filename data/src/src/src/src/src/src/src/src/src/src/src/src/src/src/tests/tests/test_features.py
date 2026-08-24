from src.sample_data import generate_demo_data
from src.features import build_features

def test_feature_engineering_includes_required_signals():
    attendance, marks = generate_demo_data(n_students=50)
    features = build_features(attendance, marks)
    assert len(features) == 50
    for col in ['attendance_pct','recent_attendance_pct','longest_absence_streak','marks_pct','failing_subject_count','decline_interaction','data_quality_confidence_score']:
        assert col in features.columns
    assert features['attendance_pct'].between(0, 100).all()
