# core/ml_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_and_save_global_model(
    csv_path = r"I:\AuyshVanniVVCE\ayush\core\data\hospital_disease_outbreak_data.csv",
    model_path=r"I:\AuyshVanniVVCE\ayush\core\outbreak_global_model.pkl"
):
    """
    Expects your hackathon CSV with:
      hospital_id       (int)
      disease           (str)
      date_reported     (YYYY-MM-DD)
      daily_cases       (int)
      humidity          (float)
      temperature       (float)
      outbreak          (0 or 1)
    This script:
     • factorizes 'disease' → diseaseId
     • computes avg_7day_cases per hospital+disease
     • trains RandomForest on:
       [hospital_id, diseaseId, avg_7day_cases, humidity, temperature]
     • saves model to disk
    """
    # 1) Load & sort
    df = pd.read_csv(csv_path, parse_dates=['date_reported'])
    df = df.sort_values(['hospital_id','disease','date_reported'])

    # 2) Encode disease → diseaseId
    df['diseaseId'], _ = pd.factorize(df['disease'])

    # 3) Compute 7-day rolling average of daily_cases per hospital+disease
    df['avg_7day_cases'] = (
        df
        .groupby(['hospital_id','diseaseId'])['daily_cases']
        .transform(lambda s: s.rolling(window=7, min_periods=1).mean().shift(1))
        .fillna(1)
    )

    # 4) Select features and target
    feature_cols = [
        'hospital_id',
        'diseaseId',
        'daily_cases',
        'humidity',
        'temperature'
    ]
    X = df[feature_cols]
    y = df['outbreak']

    # 5) Train & save
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    joblib.dump(clf, model_path)
    print(f"Global outbreak model trained and saved to {model_path}")

if __name__ == '__main__':
    train_and_save_global_model()
