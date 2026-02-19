# Support Ticket Insights & SLA Prediction

A web application that ingests support ticket data, provides technical insights, and predicts SLA breaches using a Machine Learning model.

## Setup & Run

1. **Install Dependencies**:
   ```bash
   pip install flask pandas scikit-learn joblib xgboost
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```
   *The app runs on `http://127.0.0.1:5001`*

3. **CLick on "Re-run Ingestion" button to get basic insights**
  

4. **Click on "Train Model" button to train model for prediction and get model metrics**


5. **Use the dropdown to select values for Category, Priority and Channel and click on "Predict Probability" to get prediction.**
   

## Running with Docker

1. **Build the image**:
   ```bash
   docker build -t support-insights .
   ```

2. **Run the container**:
   ```bash
   docker run -p 5001:5001 support-insights
   ```
   *Access the dashboard at `http://localhost:5001`*

## Features

- **Diagnostics**: Dashboard card and API showing row counts and data quality issues.
- **Analytics Dashboard**: Daily ticket volume, top categories, SLA breach rates, and 95th percentile resolution times.
- **Problem Customers**: Identification of customers with the highest SLA breach rates.
- **ML Prediction**: XGBoost-powered model to predict SLA breaches using creation-time features.

## Dev Log

### What Broke & How It Was Fixed


1. **Data Accumulation Issue**:
   - *Problem*: Re-running ingestion caused ticket counts to spiral (e.g., 10k instead of 5k).
   - *Diagnosis*: Ingestion script used `INSERT OR REPLACE` but never cleared the table, and random IDs prevented ID-based overwriting.
   - *Fix*: Added `DELETE FROM tickets` and `DELETE FROM customers` at the start of the `ingest_data` function to ensure a fresh state.

2. **Data Inconsistency**:
   - *Problem*: Synthetic data contained invalid priority "med".
   - *Diagnosis*: Checked ingestion logs and noticed "med" was not in the SLA policy.
   - *Fix*: Added a mapping rule in `ingestion.py` to convert "med" to "medium".

3. **Decision Tree Model**:
   - *Problem*: Due to synthetic data being imbalanced having fewer rows of breached tickets, the model was not able to learn the pattern and was giving low confidence predictions.
   - *Fix*: Replaced the Decision Tree model with XGBoost model which is better at handling imbalanced data.
   
## Tradeoffs & Future Improvements

- **Database**: Used SQLite for simplicity. For scale, PostgreSQL would be preferred for heavy concurrent analytical queries.
- **Frontend**: Used Vanilla JS/CSS for a lightweight "Glassmorphism" UI. React/Vue would be better for scaling the dashboard complexly.

