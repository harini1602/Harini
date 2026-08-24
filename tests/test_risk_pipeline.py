from src.sample_data import generate_demo_data
from src.features import build_features
from src.model import train_calibrated_model, score_students
from src.explainability import explain_students

def test_calibrated_risk_pipeline_scores_and_explains():
    a, m = generate_demo_data(n_students=60)
    features = build_features(a, m)
    model, meta = train_calibrated_model(features)
    scored = score_students(model, features)
    explanations = explain_students(model, scored)
    assert scored['risk_score'].between(0, 100).all()
    assert meta['metrics']['recall_high_risk'] >= 0
    assert meta['calibration_status'].startswith('CalibratedClassifierCV')
    assert len(explanations) == len(scored)
    assert len(explanations[0]['top_drivers']) == 3
