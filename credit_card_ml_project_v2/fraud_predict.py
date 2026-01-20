import os
import pandas as pd
import numpy as np
import xgboost as xgb
from utils import get_fraud_dataset_path, FRAUD_MODEL_PATH

if not os.path.exists(FRAUD_MODEL_PATH):
    raise FileNotFoundError("Trained model not found. Run fraud_train.py first.")

model = xgb.XGBClassifier()
model.load_model(FRAUD_MODEL_PATH)

path = get_fraud_dataset_path()
csv_path = os.path.join(path, "creditcard.csv")
df = pd.read_csv(csv_path)

sample = df.sample(5, random_state=0)
X_sample = sample.drop(columns=["Class"])
y_true = sample["Class"].values
y_prob = model.predict_proba(X_sample)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)

for i in range(len(sample)):
    print(f"Transaction {i}: true={y_true[i]}, prob_fraud={y_prob[i]:.4f}, pred={y_pred[i]}")
