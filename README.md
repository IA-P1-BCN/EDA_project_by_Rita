# Marketing Campaign Performance: Exploratory Data Analysis

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python&logoColor=white&labelColor=333)
![Pandas](https://img.shields.io/badge/Pandas-3.0-150458?style=flat&logo=pandas&logoColor=white&labelColor=333)
![Status](https://img.shields.io/badge/Status-In%20progress-e6b800?style=flat&labelColor=333)
![Priority](https://img.shields.io/badge/Priority-High-e63946?style=flat&labelColor=333)

## 📋 Project Context

Exploratory data analysis (EDA) project for the AI Bootcamp at Factoría F5 (Mini Datathon). The goal is to load a dataset, clean it, explore it, visualize it and tell the story the data contains in an executive report aimed at a CEO.

The analysis is framed around how advertising drives user acquisition and engagement, the same question a Content Partners Data Analyst answers for streaming, CTV, gaming and content-app brands.

## 📊 Dataset

[Marketing Campaign Performance Dataset](https://www.kaggle.com/datasets/manishabhatt22/marketing-campaign-performance-dataset) (Kaggle).

- Campaign-level records with channel, campaign type, target audience, duration, location, language and customer segment.
- Performance metrics: impressions, clicks, conversion rate, acquisition cost, ROI and engagement score.
- The dataset appears to be synthetic, so differences between groups can be small. Findings are supported with statistical tests rather than eyeballed from charts.
- It has no retention data. Engagement score is the closest available proxy, and this is stated as a limitation in the report.

## ❓ Key Questions

1. Which channels acquire users most efficiently (CTR, conversion rate, cost per conversion, ROI)?
2. Do more impressions or higher spend translate into more engagement?
3. Which customer segments, audiences, countries and languages respond best?
4. Does campaign duration affect ROI or engagement?
5. Is there seasonality or a trend over time?
6. Which combinations of channel, campaign type and audience perform best, and which waste budget?

## 🛠️ Tech Stack

- Python 3.11
- Pandas and NumPy for loading, cleaning and analysis
- Matplotlib, Seaborn and Plotly for visualization
- SciPy for statistical tests
- Requests for the second data source (US public holidays from the [Nager.Date API](https://date.nager.at))
- Pytest for testing the cleaning code
- Jupyter Notebook in VS Code

## 🧠 Technical Decisions

- **Conda environment (`eda-marketing`):** keeps the project dependencies isolated from other coursework and makes the Python version explicit and reproducible.
- **Pandas 3.0:** string columns use the dedicated `str` dtype and copy-on-write is the default, which the cleaning steps take into account.
- **Notebook as the main deliverable:** every cleaning decision is explained in a markdown cell next to the code, so the reasoning is auditable.
- **Cleaning code in `src/`, tested first:** type conversions, derived metrics, outlier flags and the holiday merge are reusable functions. Each one has pytest tests written before the function, and the notebook and the pipeline import the same code.
- **Outliers are flagged, not removed:** high cost-per-conversion campaigns are the ones that waste budget, so they stay in the data with a `High_Cost_Outlier` flag.
- **Holidays cached locally:** the API is called once and the result is saved to `data/us_holidays_2021.csv`, so the analysis runs offline and always uses the same data.
- **Branch per phase:** `feature/limpieza`, `feature/eda` and `feature/informe`, merged into `main` through pull requests, with small, descriptive commits.

## 📁 Project Structure

```
EDA_project_from_Rita/
├── data/
│   ├── marketing_campaign_dataset.csv   # Raw dataset (Kaggle)
│   ├── us_holidays_2021.csv             # Cached API response (second source)
│   └── processed/                       # Pipeline output, not committed
├── docs/
│   └── project_log.md   # Project log: decisions and findings per session
├── notebooks/        # EDA notebook
├── reports/          # Executive report and exported figures
├── src/
│   ├── cleaning.py   # Type conversions
│   ├── features.py   # Derived metrics (CTR, CPC, CPM, cost per conversion...)
│   ├── quality.py    # IQR outlier detection
│   ├── holidays.py   # Nager.Date API download, cache and merge
│   └── pipeline.py   # Runs every step and saves the processed CSV
├── tests/            # Pytest tests for every module in src/
├── pytest.ini
├── requirements.txt
└── README.md
```

## ⚙️ Installation

```bash
conda create -n eda-marketing python=3.11
conda activate eda-marketing
pip install -r requirements.txt
```

## 🚀 Run Locally

```bash
git clone https://github.com/IA-P1-BCN/EDA_project_from_Rita.git
cd EDA_project_from_Rita
conda create -n eda-marketing python=3.11 -y && conda activate eda-marketing && pip install -r requirements.txt
jupyter notebook notebooks/
```

The CSV must be at `data/marketing_campaign_dataset.csv`. If it is missing, download it from the Kaggle link above and place it there.

From the repo root, with the environment active:

```bash
pytest -v              # run the tests of the cleaning code
python -m src.pipeline # build data/processed/campaigns_clean.csv in one command
```

## 🗺️ Next Steps

- [x] Data cleaning and preprocessing
- [ ] Exploratory analysis and visualizations per key question
- [ ] Conclusions and recommendations
- [ ] Executive report (PDF)

## 👩‍💻 Authors

Rita Pereira, Data Analyst.
