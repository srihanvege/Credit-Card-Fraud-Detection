from kagglehub import dataset_download

FRAUD_DATASET_ID = "mlg-ulb/creditcardfraud"
FRAUD_MODEL_PATH = "fraud_xgboost_model.json"

def get_fraud_dataset_path():
    return dataset_download(FRAUD_DATASET_ID)
