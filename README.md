# Credit Card Fraud Detection

A small machine learning project with two parts: an XGBoost model for credit card fraud detection on the public ULB Kaggle dataset, and a rule-based eligibility helper that maps a user profile to mainstream U.S. card ideas (educational only, not financial advice).

## Features

- **Fraud detection**: Train and evaluate an XGBoost binary classifier on anonymized transaction features, with class weighting for severe imbalance.
- **Eligibility recommender**: Match a richer profile (score, income, location, housing, optional DTI, history, inquiries, spend, student flag) against a static catalog of cards, grouped into stronger match, compare carefully, and skip for now, each with pros, cons, and short profile notes.
- **Web UI**: Minimal dark Flask app for the recommender with a form and a results view (`app.py`, `templates/`, `static/`).

## Project structure

```
├── app.py                      # Flask server: UI + POST /api/recommend
├── templates/
│   └── index.html              # Recommender UI shell
├── static/
│   ├── recommender.css
│   └── recommender.js
├── card_catalog.py             # Card definitions (pros, cons, typical bands)
├── eligibility_recommender.py  # Profile logic, CLI, structured JSON for API
├── fraud_train.py              # Train XGBoost, save fraud_xgboost_model.json
├── fraud_predict.py            # Demo scoring and optional threshold sweep
├── utils.py                    # Kaggle dataset download helper, model path
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

- Python 3.10 or higher recommended (typing uses modern union syntax in places)
- pip

### Installation

```bash
pip install -r requirements.txt
```

Dependencies include pandas, numpy, scikit-learn, xgboost, kagglehub, and flask (for the UI).

### Fraud dataset

The fraud pipeline uses the [Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) dataset. The first run of `fraud_train.py` downloads it via `kagglehub` (network access required).

## Usage

### Fraud detection

**Train** (writes `fraud_xgboost_model.json` in the project root):

```bash
python fraud_train.py
```

**Predict / demo** (requires the trained model file):

```bash
python fraud_predict.py
```

Useful options:

- `--n_samples N` — number of random rows to print (default 5)
- `--threshold T` — probability cutoff for labeling fraud (default 0.5)
- `--seed S` — RNG seed for sampling
- `--sweep` — print precision, recall, and F1 across several thresholds on a larger random slice (`--sweep_size` controls slice size)
- `--interactive` — prompts for the above (needs a TTY)

The script prints short context on the features (PCA components, amount, time), per-transaction scores, confusion matrix and classification report on the sample, and a short note on why accuracy alone can mislead under imbalance.

### Eligibility recommender (CLI)

Non-interactive mode requires **credit score**, **annual income**, **location** (e.g. state code or region), and **housing** (`rent`, `own`, or `other`). Optional flags: `--credit_history_years`, `--debt_to_income_ratio` (decimal or percent), `--employment_years`, `--recent_inquiries`, `--monthly_card_spend`, `--student`.

```bash
python eligibility_recommender.py --credit_score 705 --income 72000 --location CA --housing rent \
  --credit_history_years 4 --debt_to_income_ratio 0.22 --recent_inquiries 1 --monthly_card_spend 2500
```

Interactive prompts (TTY required if required CLI args are missing):

```bash
python eligibility_recommender.py --interactive
```

Structured JSON (same logic as the CLI text output) is available from Python via `recommend_cards_structured(UserProfile(...))`, used by the web API.

### Eligibility recommender (web UI)

From the project root:

```bash
python app.py
```

Open `http://127.0.0.1:5050` in a browser. Submit the form to call `POST /api/recommend` and render grouped cards on the results screen.

## Model and recommender details

### Fraud model

- **Algorithm**: XGBoost classifier, binary logistic objective.
- **Features**: `Time`, `Amount`, and anonymized `V1`–`V28` (PCA); no raw merchant or cardholder identifiers in this dataset.
- **Imbalance**: `scale_pos_weight` derived from class counts in the training split.
- **Artifacts**: Model saved as `fraud_xgboost_model.json` for `fraud_predict.py` and any custom code you add.

### Eligibility recommender

- **Catalog**: `card_catalog.py` holds a fixed list of common products with typical score bands, annual fee, pros, cons, and when people often skip a product.
- **Scoring**: `eligibility_recommender.py` combines soft score-band fit, income versus fee comfort, optional DTI and history penalties, inquiry load, and simple product mismatch rules (for example, secured cards when the score is already very high).
- **Outputs**: Plain text (`recommend_cards`) or JSON (`recommend_cards_structured`) with tiers `good`, `maybe`, and `avoid`.

## Notes

- Fraud training and prediction need network access at least once for dataset download.
- The recommender is **not** financial or legal advice; issuers use proprietary underwriting and many factors not modeled here.
- Card names and typical approval bands are rough public-style guidance only; always verify current terms, fees, and eligibility with the issuer.

## License

This project is provided as-is for educational purposes.
