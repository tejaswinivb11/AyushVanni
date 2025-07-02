import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def train_and_save_global_model(
    csv_path=r"I:\mini project\ayush\core\data\hospital_disease_outbreak_data.csv",
    model_path=r"I:\mini project\ayush\core\outbreak_global_model.pkl"
):
    """
    Trains a RandomForest model to predict outbreaks using hospital and disease data.
    Also prints accuracy on the test set.
    """
    # 1) Load & sort
    df = pd.read_csv(csv_path, parse_dates=['date_reported'])
    df = df.sort_values(['hospital_id', 'disease', 'date_reported'])

    # 2) Encode disease → diseaseId
    df['diseaseId'], _ = pd.factorize(df['disease'])

    # 3) Compute 7-day rolling average of daily_cases per hospital+disease
    df['avg_7day_cases'] = (
        df
        .groupby(['hospital_id', 'diseaseId'])['daily_cases']
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

    # 5) Train-test split (80-20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 6) Train model
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # 7) Predict and calculate accuracy
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Model Accuracy: {acc * 100:.2f}%")
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred))

    # 8) Save model
    joblib.dump(clf, model_path)
    print(f"\n💾 Global outbreak model saved to: {model_path}")


if __name__ == '__main__':
    train_and_save_global_model()