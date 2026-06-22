# HUKUM Builders AI Assistant

An AI-powered construction workforce and material management assistant developed during my internship. The system combines traditional Machine Learning models, intelligent intent routing, conversational memory, and a Streamlit-based interface to assist contractors, workers, and administrators.

---

## Overview

HUKUM Builders AI Assistant is designed to streamline decision-making in construction operations by providing:

* Worker matchmaking and recommendations
* Material price estimation
* Worker trust and risk assessment
* Conversational query handling
* Session-based chat memory

The project uses traditional Machine Learning models built with Scikit-learn and operates on structured Excel datasets without relying on LLMs, Vector Databases, or RAG pipelines.

---

## Features

### Worker Matchmaking Engine

Recommends the most suitable workers based on:

* Worker rating
* Distance from project location
* Verification status
* Historical recruitment patterns

### Dynamic Pricing Engine

Predicts material pricing using:

* Material category
* Quantity
* Logistics factors
* Urgency requirements
* Brand multipliers

### Trust Shield Risk Assessment

Evaluates worker risk profiles using:

* Worker rating
* Verification status
* Historical dispute records

Provides:

* Risk Score
* Security Clearance Status
* Profile Audit Summary

### Conversational Memory

Maintains context across chat interactions:

* Follow-up questions
* Worker detail lookups
* Session-aware responses

### Intent Detection System

Automatically routes user queries to the correct backend module:

* Matchmaking
* Pricing
* Trust Shield
* Help
* General Queries

---

## Technology Stack

### Frontend

* Streamlit

### Backend

* Python

### Data Processing

* Pandas
* NumPy

### Machine Learning

* Scikit-learn
* Random Forest Classifier
* Random Forest Regressor

### Storage

* Excel-based datasets

---

## Project Structure

```text
Chatbot-Internship_Project/
│
├── README.md
├── app.py
├── ml_pipelines.py
├── requirements.txt
│
├── chatbot/
│   ├── __init__.py
│   ├── chatbot_engine.py
│   ├── config.py
│   ├── data_access.py
│   ├── intent_detector.py
│   ├── memory_manager.py
│   ├── models.py
│   └── response_generator.py
│
└── tests/
    ├── test_intent.py
    ├── test_memory_manager.py
    └── test_voice_pipeline.py
```

---

## Machine Learning Pipelines

### 1. Matchmaking Recruitment Engine

Inputs:

* Payment Amount
* Worker Rating
* Distance Delta
* Verification Status

Model:

* Random Forest Classifier

Output:

* Worker Match Probability

---

### 2. Dynamic Pricing Regressor

Inputs:

* Material Type
* Quantity
* Logistics Distance
* Urgency

Model:

* Random Forest Regressor

Output:

* Predicted Material Cost

---

### 3. Trust Shield Classifier

Inputs:

* Worker Rating
* Historical Disputes
* Verification Status

Model:

* Random Forest Classifier

Output:

* Risk Probability
* Security Clearance Status

---

## Example Queries

### Matchmaking

```text
Find a painter
Recommend a plumber
Show available electricians
```

### Pricing

```text
Price for 100 cement bags
Cost of steel rods
Estimate bricks for construction
```

### Trust Shield

```text
Check risk status for Amol Chandra
Show low risk workers
Show high risk workers
```

### General

```text
Help
What can you do?
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Shyam4849/Chatbot-Internship_Project.git
cd Chatbot-Internship_Project
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

## Future Enhancements

Planned improvements include:

* Multi-language support (English/Hindi)
* Voice-based interaction
* Advanced analytics dashboard
* Real-time database integration
* Payroll and workforce management modules
* Enhanced risk profiling system

---

## Internship Project

This project was developed as part of an internship focused on applying Machine Learning and Data Analytics concepts to solve real-world construction workforce and resource management problems.

---

## Author

**Shyam Soni**

B.Tech Computer Science Engineering
Arka Jain University

GitHub: https://github.com/Shyam4849
