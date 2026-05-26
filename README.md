
# Banking Customer Support AI Agent

AI-powered multi-agent banking support system built with Python, SQLite, and Streamlit.
---
## Live Demo
Streamlit App:
https://banking-support-ai-agent-fxuybvqgjtvjcypmurytiu.streamlit.app/
---
## GitHub Repository
https://github.com/mbasci/banking-support-ai-agent
---

## Overview

This project implements a multi-agent architecture for banking customer support workflows.

The system classifies incoming customer messages into:
- Positive Feedback
- Negative Feedback
- Query Requests

Based on the classification, the system routes the request to specialized AI agents that:
- Generate personalized responses
- Create support tickets
- Track ticket status
- Maintain interaction logs
- Provide customer support analytics

---

## Features

- Multi-Agent AI Workflow
- Classifier Agent
- Feedback Handler Agent
- Query Handler Agent
- SQLite Ticket Database
- Interaction Logging
- Evaluation Metrics
- Streamlit Dashboard
- Modular Notebook-Style Architecture

---

## Tech Stack

- Python
- Streamlit
- SQLite
- Pandas
- LangChain
- LangGraph

---

## Project Structure

banking-support-ai/

├── app.py  
├── requirements.txt  
├── README.md  
├── banking_support_ai.db  
├── agent_logs.jsonl  
├── classification_evaluation.csv  
├── response_quality_evaluation.csv  

---

## Installation

Clone repository:

git clone https://github.com/mbasci/banking-support-ai.git

cd banking-support-ai

Install dependencies:

pip install -r requirements.txt

---

## Run Streamlit App

streamlit run app.py

---

## Example Workflows

Positive Feedback:

Input:
Thanks for resolving my credit card issue.

Output:
Thank you for your kind words! We’re delighted to assist you.

---

Negative Feedback:

Input:
My debit card replacement still hasn't arrived.

Output:
A new ticket #784521 has been generated.

---

Ticket Status Query:

Input:
Could you check the status of ticket 650932?

Output:
Your ticket #650932 is currently marked as: Resolved.

---

## Evaluation

The project includes:
- Classification accuracy testing
- Routing success rate
- Response quality scoring
- Logging and traceability

---

## Future Improvements

- LLM-based classification
- Sentiment analysis
- Vector databases
- Authentication system
- Cloud deployment
- LangGraph orchestration
- Real banking API integration

---

## Author

Mark Anderson, PhD

AI • Regulatory • Multi-Agent Systems • Streamlit
