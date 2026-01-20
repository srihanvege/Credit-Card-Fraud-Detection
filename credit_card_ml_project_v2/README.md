# Credit Card ML Project

A machine learning project for credit card fraud detection and eligibility recommendation. This project consists of two main components: an XGBoost-based fraud detection model and a rule-based credit card eligibility recommender system.

## Features

- **Fraud Detection Model**: An XGBoost classifier trained to detect fraudulent credit card transactions from anonymized transaction data
- **Eligibility Recommender**: A rule-based system that recommends credit cards based on credit score and annual income

## Project Structure

```
credit_card_ml_project_v2/
├── fraud_train.py          # Training script for fraud detection model
├── fraud_predict.py        # Prediction demo using trained model
├── eligibility_recommender.py  # Credit card recommendation system
├── utils.py                # Utility functions for dataset and model paths
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Installation

1. Clone or download this repository

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- pandas
- numpy
- scikit-learn
- xgboost
- kagglehub

### Dataset

The fraud detection model uses the Credit Card Fraud Detection dataset from Kaggle. The dataset is automatically downloaded via `kagglehub` when you first run the training script.

## Usage

### Fraud Detection Model

#### Training

Train the XGBoost fraud detection model:

```bash
python fraud_train.py
```

This script will:
- Download the credit card fraud dataset (if not already present)
- Split the data into training and testing sets
- Train an XGBoost classifier with appropriate class weighting for imbalanced data
- Evaluate the model and display performance metrics (classification report, confusion matrix, ROC AUC score)
- Save the trained model to `fraud_xgboost_model.json`

#### Prediction

Run predictions on sample transactions:

```bash
python fraud_predict.py
```

This script will:
- Load the trained model (requires `fraud_train.py` to be run first)
- Sample 5 random transactions from the dataset
- Display predictions with fraud probabilities for each transaction

### Eligibility Recommender

Get credit card recommendations based on credit score and annual income:

```bash
python eligibility_recommender.py --credit_score 705 --income 72000
```

The recommender considers:
- Credit score ranges: below 580, 580-669, 670-689, 690-739, 740+
- Annual income ranges: below $40k, $40k-$80k, $80k+
- Provides specific card recommendations with reasoning based on eligibility criteria

Example output includes card recommendations such as:
- Chase Sapphire Preferred/Reserve
- American Express Platinum/Gold
- Citi Double Cash
- Secured or credit-builder cards for lower scores
- Income-based warnings about annual fees

## Model Details

### Fraud Detection Model

- **Algorithm**: XGBoost Classifier
- **Objective**: Binary classification (fraud vs. legitimate)
- **Features**: Anonymized transaction features (V1-V28, Amount, Time)
- **Handling Imbalanced Data**: Uses `scale_pos_weight` to account for class imbalance
- **Evaluation Metrics**: Classification report, confusion matrix, ROC AUC score

### Eligibility Recommender

- **Type**: Rule-based system
- **Inputs**: Credit score (integer) and annual income (float)
- **Output**: Text-based recommendations with explanations
- **Logic**: Matches credit score ranges to card types, then adjusts recommendations based on income level

## Notes

- The fraud detection model requires the trained model file (`fraud_xgboost_model.json`) to be present for predictions
- The eligibility recommender provides educational guidance only and should not be considered as financial advice
- Credit card issuers consider many factors beyond credit score and income (payment history, credit utilization, recent inquiries, etc.)

## License

This project is provided as-is for educational purposes.
