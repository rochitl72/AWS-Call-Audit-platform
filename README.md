# AWS-Call-Audit-platform
Got it ✅
Here’s your ready-to-copy-paste README.md for GitHub:

⸻


# 📞 Call Audit AWS — AI-Powered Investment Call Compliance & Audit System

## 📖 Overview
This project audits investment advisory calls for **Sharekhan-style compliance**.  
It detects **violations** (e.g., false promises like *"100% guaranteed return"*),  
extracts **audio features**, runs **ML classification**, and generates **detailed call reports**.  

It is powered by **AWS services**:
- **Amazon S3** → Store uploaded audio files
- **Amazon Transcribe** → Convert speech to text
- **Amazon Bedrock** → Detect compliance violations with Titan LLM
- **MongoDB** → Store audit reports
- **Streamlit** → Interactive dashboard

---

## 🛠 Tech Stack
- **Python 3.11+**
- **Streamlit** (UI)
- **scikit-learn** (ML model)
- **AWS S3 + Transcribe + Bedrock**
- **MongoDB** (local or Atlas cloud)

---

## 📦 Installation & Setup

### 1️⃣ Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/call_audit_aws.git
cd call_audit_aws

2️⃣ Create Virtual Environment

python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# On Windows: venv\Scripts\activate

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Configure AWS

pip install awscli
aws configure

Enter:
	•	AWS Access Key ID
	•	AWS Secret Access Key
	•	Default region name (e.g., us-east-1)

Ensure your IAM role has:
	•	AmazonS3FullAccess
	•	AmazonTranscribeFullAccess
	•	AmazonBedrockFullAccess

⸻

5️⃣ MongoDB Setup

Option 1: Local MongoDB

brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

Option 2: MongoDB Atlas (Cloud)
	1.	Create a free shared cluster at MongoDB Atlas
	2.	Whitelist your IP address
	3.	Get connection string:

mongodb+srv://USERNAME:PASSWORD@cluster0.mongodb.net



⸻

6️⃣ Environment Variables

Create a .env file in the root directory:

AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

MONGO_URI=mongodb+srv://USERNAME:PASSWORD@cluster0.mongodb.net
MONGO_DB_NAME=call_audit_db
MONGO_COLLECTION=call_reports


⸻

7️⃣ Run Locally

cd web_backend
streamlit run main_dashboard.py

Access at:

http://localhost:8501


⸻

📂 Project Structure

call_audit_aws/
├── requirements.txt               # Dependencies
├── audio_features.py              # Extracts ML audio features
├── aws_call_audit.py               # Main AWS call audit pipeline
├── aws_full_pipeline.py            # End-to-end AWS analysis
├── aws_transcribe_client.py        # AWS Transcribe API wrapper
├── bedrock_policy.json             # IAM policy for Bedrock
├── bedrock_rule_checker.py         # Titan LLM violation detection
├── call_audit_report.py            # Generates call audit report
├── debug_feature_comparison.py     # Debugging feature extraction
├── debug_feature_extraction.py     # Debugging audio features
├── rule_checker.py                 # Applies compliance rules
├── rules.json                      # Compliance rules list
├── sample_transcript.json          # Example transcript
│
├── streamlit_dashboard/
│   └── app.py                      # Test dashboard
│
└── web_backend/
    ├── app.py                      # Core backend
    ├── audio_features.py           # Audio feature extraction
    ├── auth_utils.py               # User authentication
    ├── auth.py                     # Auth route handling
    ├── aws_call_audit.py           # AWS call audit logic
    ├── main_dashboard.py           # Main Streamlit dashboard
    ├── mongo_connector.py          # MongoDB connector
    ├── mongo_utils.py              # MongoDB helpers
    ├── static/css/styles.css       # Dashboard CSS
    ├── static/logosk.png           # Logo
    ├── static/tiger.JPG            # Background image
    ├── templates/dashboard.html    # Dashboard template
    ├── templates/index.html        # Home template


⸻

💡 How It Works
	1.	User uploads an audio file via dashboard.
	2.	File is stored in AWS S3.
	3.	AWS Transcribe converts speech → text.
	4.	Transcript is sent to:
	•	AWS Bedrock Titan LLM → Detect violations.
	•	ML classifier (call_classifier.pkl) → Compliance check.
	5.	Report generated with violations + risk analysis.
	6.	Report saved to MongoDB & JSON file.
	7.	Dashboard displays results.

⸻

🧪 Example Workflow
	1.	Upload audio_sample.mp3 in dashboard.
	2.	Wait for AWS Transcribe + Bedrock processing.
	3.	View:
	•	Transcript
	•	Compliance violations
	•	Final decision
	4.	Download or view report from MongoDB.

⸻

📌 Notes
	•	Use MongoDB Atlas for cloud deployment.
	•	Use IAM with limited permissions for security.
	•	Tested on Python 3.11.6.

⸻

📜 License

This project is for educational / internship purposes.
Do NOT use for production without compliance & legal review.

--
