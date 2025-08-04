import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "call_audit_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "call_reports")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def save_report(agent_name, date, file_name, report_data):
    """
    Save a report for a specific agent, date, and file name.
    This will allow multiple files per date without overwriting.
    """
    # Ensure report_data is a pure dict (avoid BSON encoding issues)
    if not isinstance(report_data, dict):
        raise ValueError("report_data must be a dictionary")

    # Insert as a new record — do not overwrite
    record = {
        "agent_name": agent_name,
        "date": date,
        "file_name": file_name,
        "report": report_data
    }
    collection.insert_one(record)
    print(f"[MONGO] Report saved for agent={agent_name}, date={date}, file={file_name}")


def get_reports_for_agent(agent_name):
    """
    Retrieve all reports for a given agent.
    Returns a list of dicts with date, file_name, and report.
    """
    records = collection.find({"agent_name": agent_name}).sort("date", -1)
    results = []
    for r in records:
        results.append({
            "date": r.get("date"),
            "file_name": r.get("file_name"),
            "report": r.get("report")
        })
    return results


def delete_reports_for_agent(agent_name):
    """
    Deletes all reports for a given agent.
    Useful for testing or resetting.
    """
    result = collection.delete_many({"agent_name": agent_name})
    print(f"[MONGO] Deleted {result.deleted_count} reports for agent={agent_name}")