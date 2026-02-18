# Support Ticket Insights & SLA Prediction

A web application that ingests support ticket data, provides technical insights, and predicts SLA breaches using a Machine Learning model.

## Setup & Run

1. **Install Dependencies**:
   ```bash
   pip install flask pandas scikit-learn joblib xgboost
   ```

2. **Generate Synthetic Data**:
   ```bash
   python generate_data.py
   ```

3. **Ingest Data**:
   ```bash
   python ingestion.py
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   *The app runs on `http://127.0.0.1:5001`*

## Features

- **Diagnostics**: Dashboard card and API showing row counts and data quality issues.
- **Analytics Dashboard**: Daily ticket volume, top categories, SLA breach rates, and 95th percentile resolution times.
- **Problem Customers**: Identification of customers with the highest SLA breach rates.
- **ML Prediction**: XGBoost-powered model to predict SLA breaches using creation-time features.

## Dev Log

### What Broke & How It Was Fixed

1. **ML Feature Name Mismatch (`ValueError`)**: 
   - *Problem*: Predictor crashed because it received features in a different order than training.
   - *Diagnosis*: Error message `Feature names must be in the same order as they were in fit`.
   - *Fix*: Standardized a `FEATURES` list in `model_service.py` to enforce strict ordering in both training and prediction.

2. **Data Accumulation Issue**:
   - *Problem*: Re-running ingestion caused ticket counts to spiral (e.g., 10k instead of 5k).
   - *Diagnosis*: Ingestion script used `INSERT OR REPLACE` but never cleared the table, and random IDs prevented ID-based overwriting.
   - *Fix*: Added `DELETE FROM tickets` and `DELETE FROM customers` at the start of the `ingest_data` function to ensure a fresh state.

3. **Dependency Environment Mismatch**:
   - *Problem*: "Training Failed" error after switching to XGBoost.
   - *Diagnosis*: `xgboost` was installed in system Python, but the app was running in an Anaconda environment.
   - *Fix*: Synchronized environments by installing `xgboost` directly via the active Python executable.

4. **Data Inconsistency**:
   - *Problem*: Synthetic data contained invalid priority "med".
   - *Diagnosis*: Checked ingestion logs and noticed "med" was not in the SLA policy.
   - *Fix*: Added a mapping rule in `ingestion.py` to convert "med" to "medium".

## Tradeoffs & Future Improvements

- **Database**: Used SQLite for simplicity. For scale, PostgreSQL would be preferred for heavy concurrent analytical queries.
- **Model**: Upgraded to **XGBoost** for better non-linear relationship handling compared to basic Decision Trees.
- **Frontend**: Used Vanilla JS/CSS for a lightweight "Glassmorphism" UI. React/Vue would be better for scaling the dashboard complexly.
- **Dirty Data**: Successfully implemented a "Diagnostics" layer that flags bad rows instead of crashing the pipeline.
