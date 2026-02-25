---
description: Steps to run the Secure Feedback System
---

# Running the Secure Feedback System

Follow these steps to get the environment ready and run the application.

## 1. Verify Prerequisites
Ensure MongoDB and Ganache are installed and configured.

## 2. Start Ganache (Blockchain)
// turbo
```powershell
npx ganache --seed 1234
```
*Note: Using a seed ensures your `.env` credentials never need to change.*

## 3. Deploy Contract (Optional)
If you are starting a fresh Ganache instance, run:
```bash
python deploy.py
```

## 4. Start the Application
// turbo
```bash
python app.py
```
Once running, visit [http://127.0.0.1:5000](http://127.0.0.1:5000).
