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
