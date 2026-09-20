# Generalized Data + AI Project Sprint Template
## Build 2 Portfolio Projects in 1 Week

**Use this template for any analytics project.**  
The goal is speed, consistency, and portfolio quality — not maximum complexity.

---

# Weekly Goal

Complete **2 projects in 7 days**.

Each project should demonstrate:

- A real problem or business question
- Data collection / ingestion
- Data cleaning
- SQL
- Python analysis
- Visualizations
- Basic statistics where relevant
- A dashboard or app
- One useful AI feature
- Clear README and documentation
- Reproducible GitHub repository

---

# Project Standard

Every project should follow this pipeline:

```text
Problem
   ↓
Data Sources
   ↓
Python Ingestion
   ↓
Cleaning / Validation
   ↓
Processed Dataset
   ↓
SQL Database
   ↓
Analysis
   ↓
Statistics
   ↓
Visualizations
   ↓
AI Tools / Agent
   ↓
Dashboard / App
   ↓
README + Portfolio Story
```

---

# Recommended Core Tech Stack

Use the same stack across projects unless the project genuinely requires something different.

## Data

- Python
- pandas
- NumPy
- requests
- Jupyter Notebook / VS Code

## Database

- PostgreSQL, DuckDB, or SQLite

Choose:

- **SQLite** → simplest local project
- **DuckDB** → strong for analytics and CSV/Parquet
- **PostgreSQL** → strongest general portfolio database skill

## SQL

Practice:

- SELECT
- WHERE
- GROUP BY
- ORDER BY
- CASE
- JOIN
- CTE
- Window functions where useful

## Visualization

Use one or two:

- Power BI
- Tableau
- Streamlit
- matplotlib

## Version Control

- Git
- GitHub

## AI

Use:

- LLM API
- Structured outputs
- Tool/function calling
- Simple agent
- Guardrails

Do **not** add AI just to say the project has AI.

The AI feature must solve a real project problem.

---

# Repository Template

```text
project-name/

├── config/
│   └── sources.csv
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_analysis.ipynb
│
├── src/
│   ├── ingest.py
│   ├── clean.py
│   ├── transform.py
│   ├── analyze.py
│   └── utils.py
│
├── sql/
│   ├── schema.sql
│   └── analysis.sql
│
├── ai/
│   ├── agent.py
│   ├── tools.py
│   └── prompts.py
│
├── app/
│   └── streamlit_app.py
│
├── dashboard/
│
├── reports/
│   └── findings.md
│
├── tests/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# Before Starting Any Project

Answer these first:

## 1. Problem

What real question are we solving?

```text
Example:
Which customers are at the highest risk of churn and how much revenue is at risk?
```

---

## 2. Users

Who would care about the answer?

Examples:

- Operations manager
- Marketing team
- Sales manager
- Government planner
- Healthcare administrator
- Financial analyst
- Supply-chain manager

---

## 3. Main Questions

Limit the project to **3–5 important questions**.

Example:

```text
1. What is happening?
2. Where is it happening?
3. Who / what is most affected?
4. Why might it be happening?
5. What action could be taken?
```

---

## 4. Final Deliverables

Each project should aim for:

- Clean processed dataset
- SQL database
- 3–5 strong SQL queries
- 4–6 useful charts
- Dashboard or Streamlit app
- Key findings
- Limitations
- AI feature
- README
- GitHub repository

---

# 3-Day Project Sprint

Each project gets roughly **3 days**.

The seventh day is shared polishing / buffer time.

---

# Day A — Data + Cleaning + SQL

## Step 1 — Setup

- Create repo
- Create folder structure
- Add README skeleton
- Add `.gitignore`
- Create requirements file
- Add data-source documentation

---

## Step 2 — Ingest Data

Get the data using:

- CSV
- Excel
- API
- JSON
- SQL database
- Public open-data portal

Keep original files in:

```text
data/raw/
```

Never manually edit raw data.

---

## Step 3 — Inspect

Check:

```python
df.head()
df.info()
df.describe()
df.isna().sum()
df.duplicated().sum()
```

Check:

- Missing values
- Duplicates
- Wrong data types
- Invalid ranges
- Strange categories
- Date formatting
- Outliers
- Unit consistency

---

## Step 4 — Clean

Create reusable cleaning functions.

Example:

```python
def clean_data(df):
    ...
    return df
```

Save:

```text
data/processed/
```

---

## Step 5 — Database

Load processed data into:

- PostgreSQL
- DuckDB
- SQLite

Create SQL analysis queries.

Minimum:

```text
3 useful business queries
```

Better:

```text
5–8 queries
```

---

# Day B — Analysis + Statistics + Visuals

## Step 1 — EDA

Answer:

- What are the distributions?
- What changed over time?
- Which groups differ?
- Are there unusual values?
- Are variables related?

---

## Step 2 — Business Questions

Create one analysis section for each main question.

Example:

```text
Question 1
↓
SQL / Python calculation
↓
Chart
↓
Finding
↓
Business meaning
```

---

## Step 3 — Statistics

Only use statistics that genuinely help.

Possible methods:

- Mean / median
- Percentage change
- Correlation
- Confidence intervals
- A/B comparison
- Regression
- Time-series trend
- Segmentation

Do not add machine learning unless it improves the project.

---

## Step 4 — Visuals

Create approximately:

```text
4–6 strong charts
```

Each chart must answer a question.

Avoid charts that only exist because they look nice.

Every chart needs:

- Clear title
- Units
- Labels
- Source
- Short interpretation

---

## Step 5 — Findings

Create:

```text
reports/findings.md
```

Write:

```text
Finding
Evidence
Business meaning
Limitation
```

---

# Day C — AI + App + Portfolio

## Step 1 — Choose ONE AI Feature

Good AI features:

### Natural-language analytics

```text
User question
↓
AI agent
↓
SQL / Python tool
↓
Database
↓
Verified result
↓
AI explanation
```

### Automated insight explanation

AI explains dashboard metrics using calculated results.

### Report assistant

AI converts verified analytical output into plain business language.

### Data-quality assistant

AI explains detected quality problems and recommended fixes.

### Query assistant

AI converts natural language into approved SQL queries.

---

# AI Tool Pattern

Create project-specific Python tools.

Example:

```python
get_summary()
compare_groups()
get_metric()
get_trend()
get_top_categories()
```

The model should call these instead of calculating numbers itself.

---

# AI Guardrails

The AI should:

- Never invent statistics
- Use project tools for numeric answers
- Cite / identify the metric being used
- Mention uncertainty
- Say when data is insufficient
- Avoid claiming causation unless the study supports causation
- Distinguish facts from interpretation
- Stay inside the project's dataset

---

# Streamlit / Dashboard

Build a simple interface.

Example:

```text
PROJECT TITLE

KPI 1 | KPI 2 | KPI 3

Filters

Chart 1
Chart 2
Chart 3

Key Findings

------------------------------

Ask the Data Analyst

[ User question ]

AI Answer
```

Keep it simple.

Do not spend half the project changing button colors.

---

# 7-Day Team Schedule

## Day 1

### Project 1

- Problem definition
- Data collection
- Repository setup
- Data inspection
- Begin cleaning

---

## Day 2

### Project 1

- Finish cleaning
- Database
- SQL
- Analysis
- Charts
- Findings

---

## Day 3

### Project 1

- AI feature
- Streamlit / dashboard
- README
- Final cleanup

**Project 1 should now be portfolio-ready.**

---

## Day 4

### Project 2

- Problem definition
- Data collection
- Repository setup
- Data inspection
- Begin cleaning

---

## Day 5

### Project 2

- Finish cleaning
- Database
- SQL
- Analysis
- Charts
- Findings

---

## Day 6

### Project 2

- AI feature
- Streamlit / dashboard
- README
- Final cleanup

**Project 2 should now be portfolio-ready.**

---

## Day 7 — Buffer + Portfolio Day

For both projects:

- Fix bugs
- Improve README
- Add screenshots
- Clean GitHub
- Verify reproduction steps
- Review findings
- Improve project descriptions
- Prepare interview explanations
- Push final commits

Do not start a third project.

---

# Definition of Done

A project is complete when:

- [ ] Clear problem exists
- [ ] Data source documented
- [ ] Raw data preserved
- [ ] Cleaning pipeline works
- [ ] Processed dataset exists
- [ ] SQL database works
- [ ] At least 3 meaningful SQL queries exist
- [ ] Main business questions are answered
- [ ] 4+ useful charts exist
- [ ] Findings are written
- [ ] Limitations are documented
- [ ] AI feature works with real project data
- [ ] Dashboard / app works
- [ ] README explains the entire project
- [ ] Repository can be understood by another person
- [ ] Final commit is pushed

---

# README Template

```text
# Project Name

## Overview

## Problem

## Business Questions

## Data Sources

## Tech Stack

## Architecture

## Data Pipeline

## Data Cleaning

## SQL Analysis

## Exploratory Analysis

## Statistical Analysis

## Dashboard

## AI Feature

## Key Findings

## Recommendations

## Limitations

## Repository Structure

## How to Run

## Future Improvements
```

---

# Interview Story Template

Be able to explain every project using:

## Problem

What problem were we trying to solve?

## Data

Where did the data come from?

## Process

How did we clean and transform it?

## Analysis

What questions did we answer?

## Technical Work

Which Python, SQL, visualization, and AI tools did we use?

## Finding

What was the most important insight?

## Recommendation

What action could someone take?

## Limitation

What could the analysis not prove?

## AI

Why did AI improve the project rather than simply being added for show?

---

# Portfolio Project Description Template

> Built an end-to-end analytics solution using **[DATA SOURCE]** to investigate **[PROBLEM]**. Developed an automated Python data pipeline, cleaned and transformed the data using pandas, stored analytical datasets in **[DATABASE]**, and used SQL and statistical analysis to answer key business questions. Created interactive visualizations using **[POWER BI / TABLEAU / STREAMLIT]** and added an AI analytics feature using tool calling so users could ask natural-language questions against verified project data.

---

# Technology Rule

Across multiple projects, prioritize repetition.

Do not use a completely different stack for every project.

A strong portfolio could repeatedly use:

```text
Python
pandas
SQL
PostgreSQL / DuckDB
Power BI
Streamlit
GitHub
LLM API
Tool calling
```

Repetition builds competence faster than collecting technologies.

---

# Time-Cut Rule

If the project is behind schedule, cut in this order:

1. Fancy styling
2. Extra charts
3. Extra dataset
4. Extra dashboard pages
5. Advanced machine learning
6. Complex AI features
7. Extra SQL queries

Do NOT cut:

- Data cleaning
- Core SQL
- Main analysis
- Key visualizations
- Findings
- Limitations
- README
- Reproducibility

---

# Rule for Choosing Projects

The two weekly projects should ideally show different business domains.

Example:

```text
Project 1 → Climate / Government Analytics
Project 2 → Retail / Customer / Revenue Analytics
```

That gives variety while keeping the technical stack mostly the same.

---

# Final Principle

**Depth first, novelty second.**

Two finished, explainable projects are worth more than five half-built repositories.

The target is not:

> “We used every technology.”

The target is:

> “We found a real problem, analyzed it correctly, built something useful, and can explain every decision.”
