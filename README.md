# Drop-Out Early-Warning Copilot

A production-ready hackathon Streamlit dashboard for the **Explainable Drop-Out Risk Dashboard** challenge. It turns routine attendance and marks spreadsheets into a closed-loop workflow:

**Input CSV/Excel → Validate + engineer features → Calibrated risk model → Student-level SHAP explanations → Action queue + editable intervention message → Outcome tracking + audit logs**

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
streamlit run app.py
```

## Demo accounts

| Role | Email | Password |
|---|---|---|
| teacher | `teacher@demo.school` | `teacher123` |
| school leader | `leader@demo.school` | `leader123` |
| admin | `admin@demo.school` | `admin123` |

Use **Run built-in demo pipeline** in the sidebar to generate 50+ realistic learners, multiple classes/sections, attendance over weeks, several terms, subject gaps, long absence streaks, missing assessments, and mixed risk cases. The demo flows through the same validation, feature engineering, calibrated scoring, SHAP explainability, SQLite persistence, action-card, and audit-log path as uploaded files.

## Spreadsheet formats

Attendance requires mappable columns for student id, student name, class/grade, date, and status. Marks requires student id, student name, class/grade, date, subject, marks, and max marks. Common aliases are supported, including `roll_no`, `admission_no`, `learner_name`, `grade`, `attendance_date`, `exam_date`, `present`, `score`, `out_of`, and `term`.

## Risk model

`src/model.py` trains a `GradientBoostingClassifier` wrapped in scikit-learn `CalibratedClassifierCV` with sigmoid calibration. If no real historical dropout label is supplied, transparent synthetic labels are generated from attendance decline, low recent attendance, low marks, absence streaks, and failing subjects; the model metadata marks this as synthetic-label mode. The selected threshold prioritizes high-risk recall to reduce false negatives, and metadata stores recall, false-negative rate, precision, ROC-AUC/PR-AUC when valid, Brier score, feature list, model version, and calibration status.

## SHAP explanations

`src/explainability.py` uses SHAP `TreeExplainer` on the calibrated gradient-boosting base estimator. Per-student top positive SHAP impacts are translated into plain teacher language such as attendance decline, current absence streak, recent marks decline, missing assessments, or failing subjects. The UI labels these as **model signals, not final human judgement**.

## Privacy, RBAC, audit, and persistence

SQLite is the default persistence layer and stores upload batches, standardized rows, student master records, risk scores, SHAP drivers, interventions, outcomes, audit logs, and model metadata. Student display IDs are salted SHA-256 pseudonyms. Demo RBAC supports teacher, school leader, and admin roles; identity reveal is restricted and audited. Configuration includes encryption-ready placeholders for production secrets, database encryption, PostgreSQL/cloud object storage adapters, and school tenancy fields.

## Production next steps and limitations

- Move salts and credentials to a managed secret vault.
- Swap SQLite for PostgreSQL with row-level tenancy and optional transparent database encryption.
- Add scheduled batch inference and persisted model artifacts.
- Validate with local school outcome labels and monitor equity/drift over time.
- Integrate SIS/LMS APIs and guardian communication tools after privacy review.
