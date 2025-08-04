import os
import json
import time
import uuid
import boto3
import requests
import joblib
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from datetime import date

# ---------------- Load Environment Variables ----------------
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "call-audit-temp-bucket")

# ---------------- Local Imports ----------------
from bedrock_rule_checker import check_violations as check_bedrock
from audio_features import extract_audio_features  # Your working feature extraction function

# ---------------- Global Variables ----------------
AUDIO_FILE = ""
JOB_NAME = ""


def generate_unique_job_name():
    """Generate a unique AWS Transcribe job name."""
    return f"CallAuditJob-{uuid.uuid4().hex[:8]}-{int(time.time())}"


def transcribe_audio():
    """Upload audio to S3 and start AWS Transcribe job."""
    global JOB_NAME

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
    transcribe_client = boto3.client(
        "transcribe",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    # Ensure bucket exists
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except Exception:
        print(f"[INFO] Creating S3 bucket: {BUCKET_NAME}")
        if AWS_REGION == "us-east-1":
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
            )

    # Upload file to S3
    s3_key = os.path.basename(AUDIO_FILE)
    print(f"[INFO] Uploading {AUDIO_FILE} to S3 bucket {BUCKET_NAME}...")
    s3_client.upload_file(AUDIO_FILE, BUCKET_NAME, s3_key)

    audio_uri = f"s3://{BUCKET_NAME}/{s3_key}"

    # Generate unique job name
    JOB_NAME = generate_unique_job_name()

    # Detect file format
    file_ext = Path(AUDIO_FILE).suffix.lower().replace(".", "")
    if file_ext not in ["mp3", "wav", "m4a"]:
        raise ValueError(f"Unsupported audio format: {file_ext}")

    # Start AWS Transcribe
    print(f"[INFO] Starting AWS Transcribe job: {JOB_NAME}...")
    transcribe_client.start_transcription_job(
        TranscriptionJobName=JOB_NAME,
        Media={"MediaFileUri": audio_uri},
        MediaFormat=file_ext,
        LanguageCode="en-US"
    )

    # Wait for job completion
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=JOB_NAME)
        state = status["TranscriptionJob"]["TranscriptionJobStatus"]
        if state in ["COMPLETED", "FAILED"]:
            break
        print("[INFO] Waiting for transcription job to complete...")
        time.sleep(5)

    if state == "COMPLETED":
        transcript_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        print(f"[INFO] Transcription completed. Downloading transcript from {transcript_url}...")
        r = requests.get(transcript_url)
        transcript_data = r.json()
        transcript_text = transcript_data["results"]["transcripts"][0]["transcript"]

        # Standardize transcript for Bedrock checker
        transcript_list = [{"speaker": "agent", "text": transcript_text}]
        return transcript_list
    else:
        raise Exception("AWS Transcribe failed.")


def classify_call(features):
    """Run ML classification using the trained model."""
    print("[INFO] Loading classifier from: call_classifier.pkl")
    clf = joblib.load("call_classifier.pkl")

    # Build feature vector for prediction
    X = [[
        features.get("pitch", 0),
        features.get("pitch_range", 0),
        features.get("tempo", 0),
        features.get("jitter", 0),
        features.get("zero_crossing_rate", 0),
        features.get("rms_energy", 0),
        np.mean(features.get("mfcc", [0])),
        np.mean(features.get("gfcc", [0])),
        np.mean(features.get("chroma", [0]))
    ]]

    prediction = clf.predict(X)[0]
    confidence = max(clf.predict_proba(X)[0])
    return int(prediction), float(confidence)


def generate_full_audit(audio_path=None):
    """Run full AWS Call Audit pipeline."""
    global AUDIO_FILE
    if not audio_path:
        raise ValueError("Audio path must be provided.")
    AUDIO_FILE = audio_path

    # Step 1: Transcribe
    transcript_list = transcribe_audio()

    # Step 2: Bedrock violation detection
    bedrock_result = check_bedrock(transcript_list)

    # Step 3: Extract audio features
    print("[INFO] Extracting audio features...")
    features = extract_audio_features(AUDIO_FILE)

    # Step 4: ML classification
    classification, confidence = classify_call(features)

    # Step 5: Save report (ensure numpy/int64 are JSON serializable)
    report = {
        "audio_features": json.loads(json.dumps(features, default=lambda o: float(o))),
        "bedrock_analysis": bedrock_result,
        "classification": {
            "status": int(classification),
            "confidence": round(float(confidence), 2)
        }
    }

    with open("report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("[INFO] Final AWS Call Audit Report saved to report.json")

    # Step 6: Save to MongoDB so View Reports shows it immediately
    try:
        from mongo_connector import save_report
        agent_name = os.getenv("DEFAULT_AGENT_NAME", "test_agent")
        file_name = os.path.basename(audio_path)  # Track specific uploaded file

        # Updated call to match correct signature
        save_report(
            agent_name=agent_name,
            date=str(date.today()),
            report_data=report,
            file_name=file_name
        )

        print(f"[INFO] Report also saved to MongoDB for agent: {agent_name} (File: {file_name})")
    except Exception as e:
        print(f"[WARN] Could not save to MongoDB: {e}")

    return report


if __name__ == "__main__":
    # For direct testing
    generate_full_audit("web_backend/uploaded_calls/WhatsApp Audio 2025-08-01 at 10.09.32.mp3")