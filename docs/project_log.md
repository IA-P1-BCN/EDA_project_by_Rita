# Project Log

Short record of decisions and findings, one entry per session. It is the basis for the executive report.

## 2026-11-04

**What I did**
- Reviewed the project brief: choose a dataset, explained notebook, clean branches and commits, executive report, one-week deadline.
- Chose the dataset and set up the working environment.
- Downloaded the CSV and cloned the school's repo.
- Wrote the README and a minimal `requirements.txt`.

**Decisions**
- Dropped my own Spotify data. The API only returns the last 50 plays, and the full streaming history takes 5 days to arrive, too tight for the deadline.
- Chose the Marketing Campaign Performance dataset (Kaggle). It fits the role I am aiming for (Content Partners Data Analyst: how advertising drives acquisition and engagement) because it includes channel, impressions, clicks, conversion rate, acquisition cost, ROI and engagement score.
- Environment: conda `eda-marketing`, Python 3.11, pandas 3.0.6. VS Code kernel verified.

**Known limitations**
- The dataset looks synthetic, so differences between channels may be small. If there are no clear differences, I will report that and back it up with a statistical test.
- It has no retention data. The closest proxy is `Engagement_Score`. I will state this in the report.

**Structure**
- The repo was cloned into a subfolder with the same name. I moved `data/`, `CLAUDE.md` and `.vscode/` inside the repo and now work from there.

**Next steps**
- Create the notebook, load the CSV and check types, nulls and duplicates (`info`, `head`, `describe`).

## 2026-11-05

**What I did**
- Finished the first inspection: `describe`, nulls, duplicates, `Campaign_ID` uniqueness, categorical value counts and the clicks vs impressions check, each with a written reading.
- Read the official delivery levels and set the goal: Advanced level complete, Expert if time allows.
- Cleaned the data with reusable functions in `src/`, writing the pytest tests before each function (31 tests, all passing).
- Created derived metrics: CTR, conversions, CPC, cost per conversion, CPM, month and weekday.
- Flagged outliers with the IQR rule.
- Added a second data source: 2021 US federal holidays from the Nager.Date API, downloaded with `requests`, cached as CSV and joined with a merge.
- Built a one-command pipeline: `python -m src.pipeline`.
- Merged the cleaning phase into `main` with PR #2 and started `feature/eda`.
- Answered questions 1 (channels) and 2 (spend and reach vs engagement).

**Decisions**
- `Acquisition_Cost` from text to float, `Duration` to an integer column renamed `Duration_days`, `Date` to datetime.
- The dataset does not define two columns, so I assumed `Conversion_Rate` = conversions / clicks and `Acquisition_Cost` = total campaign spend in USD.
- Outliers are flagged, not removed: high-cost campaigns are exactly the budget waste that question 6 needs to find.
- Only federal holidays (11 in 2021), because the 5 cities are in 5 different states. Duplicate dates are dropped before the merge so no campaign is duplicated.
- Groups are compared with medians and checked with Kruskal-Wallis plus effect size. Correlations use Spearman.
- `Cost_per_Conversion` is the main efficiency metric, because `ROI` does not reflect costs.

**Findings**
- No channel is more efficient: median cost per conversion goes from 330.5 USD (Website) to 337.3 USD (Instagram), and no metric differs significantly between channels (p from 0.17 to 0.93).
- More spend or more impressions do not raise engagement: mean engagement is 5.48 to 5.52 in every spend and impression quintile (p = 0.337 and 0.438).
- 9.2% of campaigns are high-cost outliers. They pay about 7 times more per conversion (2,229 vs 298 USD) because they convert poorly (6 vs 40 conversions).
- Cost per conversion depends much more on the number of conversions (Spearman −0.91) than on spend (+0.39).

**Known limitations (data quality)**
- The original columns are independent of each other (correlations between −0.01 and 0.01), evenly spread and have no outliers.
- Absolute values are unrealistic: median CTR 10%, median CPM 2,270 USD. Only comparisons between groups are meaningful.
- `ROI` is not consistent with costs: high-cost outliers have the same median ROI as normal campaigns (5.00 vs 5.01).
- Dates rotate by campaign ID (100% of rows), so real seasonality cannot exist. Question 5 is expected to be flat.
- `Engagement_Score` is uniform: about 20,000 campaigns on each value from 1 to 10.

**Next steps**
- Questions 3 to 6, including a Plotly interactive chart.
- Conclusions, then the executive report.

## 2026-11-06

**What I did**
- Answered questions 3 (segments, audiences, cities, languages), 4 (duration), 5 (seasonality) and 6 (combinations and budget waste).
- Wrote the conclusions in the notebook: answers to the six questions, three key messages, recommendations and a data quality report.
- Merged the EDA phase into `main` with PR #3 and started `feature/informe`.
- Profiled the high-cost campaigns: which setup attributes and which results set them apart.
- Wrote the executive report in Spanish and English (12 pages each, PDF) and a two-page summary in Spanish, all in `reports/`. Every chart in the report is also in the notebook.

**Decisions**
- Kept the dataset even though it is flat in every dimension. Changing it would be risky this late, and the process is what is assessed.
- Told the report as an investigation: four suspects (channel, audience, combination, budget/duration/calendar) are ruled out with tests, and the twist is that the waste sits inside every channel.
- Applied the Bonferroni correction whenever I ran many tests at once (20 in question 3, 9 in question 5, 11 in the high-cost profile).
- Checked the 150 channel × type × audience combinations with a split-half test (seed 42) before trusting any ranking.
- Removed every claim about "detecting campaigns early". The dataset only has final results per campaign, so when the signal appears is a hypothesis, and the report proposes a pilot to test it.
- Kept the full report and added a two-page summary to meet the 1 to 2 page requirement.

**Findings**
- No segment, audience, city or language is more efficient: cost per conversion from 331.5 to 337.4 USD, 0 of 20 tests significant after Bonferroni.
- Duration and calendar are flat: median ROI 5.00 to 5.02 for every duration, monthly cost per conversion 330.5 to 341.0 USD, holidays vs normal days p = 0.688.
- No winning combination: the best and worst of the 150 combinations (310.6 vs 366.4 USD) change completely between two random halves (Spearman −0.047, 0 of 10 in common in the top 10).
- Budget waste: 9.2% of campaigns take 10.9% of the budget (272.1 of 2,500.9 million USD) and bring only 1.3% of conversions.
- A final conversion rate of 2% or less flags 10.7% of campaigns and catches 58.4% of the high-cost ones, with 50.3% precision.
- No setup attribute predicts high-cost campaigns (share between 8.9% and 9.6% in every group). Budget is the only weak link: conversions do not grow with spend (Spearman 0.001), so the high-cost share rises from 2.9% in the lowest spend quintile to 16.0% in the highest.

**Known limitations (data quality)**
- Channel and campaign type are independent (chi-square p = 0.629), including combinations that make no sense, such as Facebook with Email campaigns.
- Duration does not change spend: median 12,500 USD at 15 days and 12,494.5 USD at 60 days.
- No daily results per campaign, so the report cannot say how soon a costly campaign shows up.

**Next steps**
- Final README, pinned `requirements.txt` and PR #4 into `main`.
- Expert level if time allows: Streamlit dashboard and a 5-minute presentation.
