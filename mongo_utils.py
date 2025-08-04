from pymongo import MongoClient
import os

client = MongoClient("mongodb://localhost:27017/")
db = client["call_audit_db"]

def save_report(agent, date, filename, report_dict):
    collection = db["call_reports"]
    collection.insert_one({
        "agent": agent,
        "date": date,
        "filename": filename,
        "report": report_dict
    })

def get_reports_by_agent(agent):
    return list(db["call_reports"].find({"agent": agent}))

def get_reports_by_agent_and_date(agent, date):
    return list(db["call_reports"].find({"agent": agent, "date": date}))