
import streamlit as st
import sqlite3
import pandas as pd
import re
import random
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional

# =========================
# Configuration
# =========================

DB_PATH = "banking_support_ai.db"
LOG_PATH = "agent_logs.jsonl"

POSITIVE_FEEDBACK = "Positive Feedback"
NEGATIVE_FEEDBACK = "Negative Feedback"
QUERY = "Query"
UNKNOWN = "Unknown"

STATUS_UNRESOLVED = "Unresolved"
STATUS_IN_PROGRESS = "In Progress"
STATUS_RESOLVED = "Resolved"

# =========================
# Utility Functions
# =========================

def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_connection():
    return sqlite3.connect(DB_PATH)


def safe_lower(text):
    return text.lower().strip() if isinstance(text, str) else ""


def extract_ticket_number(text):
    match = re.search(r"\b\d{6}\b", text)
    if match:
        return match.group(0)
    return None


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        ticket_number TEXT PRIMARY KEY,
        customer_name TEXT,
        issue_text TEXT,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interaction_logs (
        interaction_id TEXT PRIMARY KEY,
        timestamp TEXT,
        customer_name TEXT,
        user_message TEXT,
        classification TEXT,
        agent_path TEXT,
        response TEXT,
        ticket_number TEXT,
        success INTEGER,
        error_message TEXT
    )
    """)

    conn.commit()
    conn.close()


def generate_ticket_number():
    conn = get_connection()
    cursor = conn.cursor()

    while True:
        ticket_number = str(random.randint(100000, 999999))
        cursor.execute(
            "SELECT ticket_number FROM support_tickets WHERE ticket_number = ?",
            (ticket_number,)
        )
        if cursor.fetchone() is None:
            conn.close()
            return ticket_number


def create_support_ticket(customer_name, issue_text):
    ticket_number = generate_ticket_number()
    now = current_timestamp()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO support_tickets
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ticket_number,
        customer_name,
        issue_text,
        STATUS_UNRESOLVED,
        now,
        now
    ))

    conn.commit()
    conn.close()

    return ticket_number


def get_ticket_status(ticket_number):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT ticket_number, customer_name, issue_text, status, created_at, updated_at
    FROM support_tickets
    WHERE ticket_number = ?
    """, (ticket_number,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "ticket_number": row[0],
        "customer_name": row[1],
        "issue_text": row[2],
        "status": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


def save_interaction(record):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO interaction_logs
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["interaction_id"],
        record["timestamp"],
        record["customer_name"],
        record["user_message"],
        record["classification"],
        record["agent_path"],
        record["response"],
        record["ticket_number"],
        int(record["success"]),
        record["error_message"]
    ))

    conn.commit()
    conn.close()

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# =========================
# Agents
# =========================

class ClassifierAgent:
    def __init__(self):
        self.positive_keywords = [
            "thanks", "thank you", "appreciate", "great", "excellent",
            "resolved", "helpful", "happy", "satisfied", "good service"
        ]

        self.negative_keywords = [
            "not arrived", "hasn't arrived", "problem", "issue", "complaint",
            "bad", "poor", "terrible", "angry", "frustrated",
            "not working", "failed", "delay", "unable", "cannot", "can't"
        ]

        self.query_keywords = [
            "status", "check", "update", "ticket", "where is", "track"
        ]

    def classify(self, message):
        text = safe_lower(message)

        if extract_ticket_number(text) and any(word in text for word in self.query_keywords):
            return QUERY, 0.95, "Detected ticket number and query/status intent."

        if any(word in text for word in self.query_keywords):
            return QUERY, 0.80, "Detected query/status intent."

        if any(word in text for word in self.positive_keywords):
            return POSITIVE_FEEDBACK, 0.85, "Detected positive sentiment."

        if any(word in text for word in self.negative_keywords):
            return NEGATIVE_FEEDBACK, 0.85, "Detected negative sentiment or complaint."

        return QUERY, 0.50, "Fallback route."


class FeedbackHandlerAgent:
    def positive(self, customer_name, message):
        return {
            "response": f"Thank you for your kind words, {customer_name}! We’re delighted to assist you.",
            "ticket_number": None,
            "action": "Positive feedback acknowledged."
        }

    def negative(self, customer_name, message):
        ticket_number = create_support_ticket(customer_name, message)

        return {
            "response": f"We apologize for the inconvenience. A new ticket #{ticket_number} has been generated, and our team will follow up shortly.",
            "ticket_number": ticket_number,
            "action": "New ticket created."
        }


class QueryHandlerAgent:
    def query(self, customer_name, message):
        ticket_number = extract_ticket_number(message)

        if not ticket_number:
            return {
                "response": "Please provide a valid 6-digit ticket number so I can check the status.",
                "ticket_number": None,
                "action": "Ticket number missing."
            }

        ticket_data = get_ticket_status(ticket_number)

        if ticket_data is None:
            return {
                "response": f"We could not find ticket #{ticket_number}. Please verify the ticket number and try again.",
                "ticket_number": ticket_number,
                "action": "Ticket not found."
            }

        return {
            "response": f"Your ticket #{ticket_number} is currently marked as: {ticket_data['status']}.",
            "ticket_number": ticket_number,
            "action": "Ticket status retrieved."
        }


class BankingSupportOrchestrator:
    def __init__(self):
        self.classifier = ClassifierAgent()
        self.feedback = FeedbackHandlerAgent()
        self.query = QueryHandlerAgent()

    def process(self, message, customer_name):
        interaction_id = str(uuid.uuid4())
        timestamp = current_timestamp()

        try:
            classification, confidence, reason = self.classifier.classify(message)

            if classification == POSITIVE_FEEDBACK:
                agent_path = "Classifier -> Positive Feedback Handler"
                result = self.feedback.positive(customer_name, message)

            elif classification == NEGATIVE_FEEDBACK:
                agent_path = "Classifier -> Negative Feedback Handler"
                result = self.feedback.negative(customer_name, message)

            elif classification == QUERY:
                agent_path = "Classifier -> Query Handler"
                result = self.query.query(customer_name, message)

            else:
                agent_path = "Classifier -> Fallback"
                result = {
                    "response": "I’m sorry, I could not determine how to handle your request.",
                    "ticket_number": None,
                    "action": "Fallback."
                }

            record = {
                "interaction_id": interaction_id,
                "timestamp": timestamp,
                "customer_name": customer_name,
                "user_message": message,
                "classification": classification,
                "classification_confidence": confidence,
                "classification_reason": reason,
                "agent_path": agent_path,
                "response": result["response"],
                "ticket_number": result.get("ticket_number"),
                "success": True,
                "error_message": None
            }

        except Exception as e:
            record = {
                "interaction_id": interaction_id,
                "timestamp": timestamp,
                "customer_name": customer_name,
                "user_message": message,
                "classification": UNKNOWN,
                "classification_confidence": 0.0,
                "classification_reason": "Error.",
                "agent_path": "Error Handler",
                "response": "We’re sorry, something went wrong.",
                "ticket_number": None,
                "success": False,
                "error_message": str(e)
            }

        save_interaction(record)
        return record


# =========================
# Streamlit UI
# =========================

st.set_page_config(
    page_title="Banking Customer Support AI Agent",
    layout="wide"
)

initialize_database()

st.title("Banking Customer Support AI Agent")
st.caption("Multi-Agent Architecture: Classifier → Feedback Handler / Query Handler")

orchestrator = BankingSupportOrchestrator()

tab1, tab2, tab3, tab4 = st.tabs([
    "Chat Simulation",
    "Tickets Database",
    "Interaction Logs",
    "Test Scenarios"
])

with tab1:
    st.subheader("Customer Message")

    customer_name = st.text_input("Customer Name", value="Customer")
    message = st.text_area(
        "Enter customer message",
        value="My debit card replacement still hasn't arrived."
    )

    if st.button("Run Agent Workflow"):
        result = orchestrator.process(message, customer_name)

        st.success(result["response"])

        col1, col2, col3 = st.columns(3)

        col1.metric("Classification", result["classification"])
        col2.metric("Confidence", result["classification_confidence"])
        col3.metric("Success", str(result["success"]))

        st.write("Agent Path:", result["agent_path"])
        st.write("Classification Reason:", result["classification_reason"])

        if result["ticket_number"]:
            st.info(f"Ticket Number: {result['ticket_number']}")

with tab2:
    st.subheader("Support Tickets")

    conn = get_connection()
    tickets_df = pd.read_sql_query(
        "SELECT * FROM support_tickets ORDER BY created_at DESC",
        conn
    )
    conn.close()

    st.dataframe(tickets_df, use_container_width=True)

with tab3:
    st.subheader("Interaction Logs")

    conn = get_connection()
    logs_df = pd.read_sql_query(
        "SELECT * FROM interaction_logs ORDER BY timestamp DESC",
        conn
    )
    conn.close()

    st.dataframe(logs_df, use_container_width=True)

with tab4:
    st.subheader("Prebuilt Test Scenarios")

    scenarios = [
        "Thanks for resolving my credit card issue.",
        "My debit card replacement still hasn't arrived.",
        "Could you check the status of ticket 650932?",
        "I am frustrated because my mobile banking app is not working.",
        "Thank you, the support was excellent."
    ]

    selected = st.selectbox("Choose a scenario", scenarios)

    if st.button("Run Selected Scenario"):
        result = orchestrator.process(selected, "Scenario User")

        st.write("Message:", selected)
        st.write("Classification:", result["classification"])
        st.write("Agent Path:", result["agent_path"])
        st.success(result["response"])
