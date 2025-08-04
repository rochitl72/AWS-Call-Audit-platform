import boto3
import json
import os
import time
import requests
import joblib
import numpy as np
from audio_features import extract_audio_features
from rule_checker import check_violations
from call_audit_report import analyze_tone

# AWS Credentials
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY = "AKIAWOIGTHBM6OIOCQWK"
AWS_SECRET_KEY = "DHiFA0H7vEzsJ6WlfGGVTv4ADimrdd+os2slelSX"

# File
AUDIO_FILE = "/Users/rochitlen/Downloads/audio_sample.mp3"
JOB_NAME = "CallAuditFullPipelineJob"
BUCKET_NAME = "call-audit-temp-bucket"


def parse_aws_transcript(transcript_data):
    """Convert AWS Transcribe JSON to our expected list of dictionaries."""
    if isinstance(transcript_data, dict) and "results" in transcript_data:
        items = transcript_data.get("results", {}).get("items", [])
        parsed = []
        for item in items:
            if item.get("type") == "pronunciation":
                start = item.get("start_time", "0")
                text = item.get("alternatives", [{}])[0].get("content", "")
                parsed.append({
                    "start_time": start,
                    "speaker": "agent",
                    "text": text
                })
        return parsed
    return transcript_data


def transcribe_audio():
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

    # Upload file to S3
    try:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
    except Exception:
        pass

    s3_key = os.path.basename(AUDIO_FILE)
    print(f"[INFO] Uploading {AUDIO_FILE} to S3 bucket {BUCKET_NAME}...")
    s3_client.upload_file(AUDIO_FILE, BUCKET_NAME, s3_key)

    audio_uri = f"s3://{BUCKET_NAME}/{s3_key}"

    # Start AWS Transcribe
    print(f"[INFO] Starting AWS Transcribe job: {JOB_NAME}...")
    transcribe_client.start_transcription_job(
        TranscriptionJobName=JOB_NAME,
        Media={"MediaFileUri": audio_uri},
        MediaFormat="mp3",
        LanguageCode="en-US",
        Settings={
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": 2
        }
    )

    # Wait for job to finish
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=JOB_NAME)
        state = status["TranscriptionJob"]["TranscriptionJobStatus"]
        if state in ["COMPLETED", "FAILED"]:
            break
        print("[INFO] Waiting for transcription job to complete...")
        time.sleep(10)

    if state == "COMPLETED":
        transcript_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        print(f"[INFO] Transcription completed. Downloading transcript from {transcript_url}...")
        r = requests.get(transcript_url)
        with open("real_transcript.json", "w") as f:
            json.dump(r.json(), f, indent=2)
        return "real_transcript.json"
    else:
        raise Exception("AWS Transcribe failed.")


def generate_full_audit():
    transcript_file = transcribe_audio()

    with open(transcript_file, "r") as f:
        transcript = json.load(f)
    transcript = parse_aws_transcript(transcript)

    print("[INFO] Extracting audio features...")
    features = extract_audio_features(AUDIO_FILE)

    print("[INFO] Checking for rule violations...")
    violations = check_violations(transcript)

    print("[INFO] Analyzing tone...")
    tone, tone_scores = analyze_tone(transcript)

    # Prepare ML feature vector
    feature_vector = [
        features.get("mfcc", [0, 0])[0],
        features.get("mfcc", [0, 0])[1],
        features.get("pitch", 0),
        features.get("tempo", 0),
        features.get("rms_energy", 0),
        len(violations.get("violations", [])),
        tone_scores.get("positive", 0),
        tone_scores.get("negative", 0),
        tone_scores.get("neutral", 0)
    ]
    feature_vector = np.array(feature_vector).reshape(1, -1)

    # Predict compliance using trained model
    clf = joblib.load("call_classifier.pkl")
    prediction = clf.predict(feature_vector)[0]
    prediction_proba = clf.predict_proba(feature_vector)[0][prediction]

    # Generate explanation for classification
    reasons = []
    if len(violations.get("violations", [])) > 0:
        reasons.append(f"{len(violations['violations'])} rule violations")
    if tone_scores.get("negative", 0) > tone_scores.get("positive", 0):
        reasons.append("Negative tone dominates")
    if features.get("pitch", 0) > 250:
        reasons.append("High pitch (indicating stress)")

    classification_reason = " and ".join(reasons) if reasons else "Call is normal and compliant"

    classification = {
        "status": "Compliant" if prediction == 1 else "Non-Compliant",
        "confidence": round(float(prediction_proba), 2),
        "reason": classification_reason
    }

    report = {
        "audio_features": features,
        "rule_violations": violations,
        "agent_tone": tone,
        "tone_scores": tone_scores,
        "classification": classification
    }

    with open("report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("[INFO] Final AWS Call Audit Report saved to report.json")


if __name__ == "__main__":
    generate_full_audit()