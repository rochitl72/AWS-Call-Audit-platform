import boto3
import time
import os

AWS_REGION = "us-east-1"
AUDIO_FILE = "/Users/rochitlen/Downloads/audio_sample.mp3"
JOB_NAME = "CallAuditTranscriptionJob"

def transcribe_audio():
    transcribe_client = boto3.client(
        "transcribe",
        aws_access_key_id="AKIAWOIGTHBM6OIOCQWK",
        aws_secret_access_key="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",
        region_name=AWS_REGION
    )

    # Upload file to S3 (needed for AWS Transcribe)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id="AKIAWOIGTHBM6OIOCQWK",
        aws_secret_access_key="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",
        region_name=AWS_REGION
    )

    bucket_name = "call-audit-temp-bucket"
    try:
        s3_client.create_bucket(Bucket=bucket_name)
    except Exception:
        pass  # Bucket may already exist

    s3_key = os.path.basename(AUDIO_FILE)
    s3_client.upload_file(AUDIO_FILE, bucket_name, s3_key)
    audio_uri = f"s3://{bucket_name}/{s3_key}"

    # Start transcription job
    print(f"[INFO] Starting AWS Transcribe job: {JOB_NAME}")
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

    # Wait until job completes
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=JOB_NAME)
        state = status["TranscriptionJob"]["TranscriptionJobStatus"]
        if state in ["COMPLETED", "FAILED"]:
            break
        print("[INFO] Waiting for transcription job to complete...")
        time.sleep(10)

    if state == "COMPLETED":
        transcript_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        print(f"[INFO] Transcription job completed. Download: {transcript_url}")
        return transcript_url
    else:
        raise Exception("Transcription failed.")

if __name__ == "__main__":
    transcribe_audio()