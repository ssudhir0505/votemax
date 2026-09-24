# 🛠️ ECI SecureVote - Setup & Installation Guide

This guide provides crisp, step-by-step instructions to get the ECI SecureVote system running on your local machine.

## 📋 Prerequisites
- **Python 3.8+** (Ensure `python` is in your system PATH)
- **Git** (Optional, for cloning)
- **Web Browser** (Chrome/Edge/Firefox)

---

## 🚀 Quick Start (Windows)

### 1. Clone/Download the Repository
Extract the project files to a folder (e.g., `Desktop\vote`).

### 2. Open a Terminal
Open PowerShell or Command Prompt in the project folder.

### 3. Install Dependencies
Run the following command to install Flask and cryptography libraries:
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database (Optional)
The system comes with a pre-configured implementation, but if you want to wipe everything and start fresh:
```powershell
python -m flask reset-db
```

### 5. Create Admin Account
You need an admin account to manage the election.
```powershell
python -m flask create-admin admin admin123
```
*(Replace `admin` and `admin123` with your desired credentials)*

### 6. Run the Application
Start the secure server:
```powershell
python run.py
```
**Access the App:** Open **[http://127.0.0.1:8080](http://127.0.0.1:8080)** in your browser.

---

## 🛡️ Admin CLI Commands
The system includes built-in CLI tools for management.

| Command | Description |
| :--- | :--- |
| `python -m flask create-admin <user> <pass>` | Creates a new superuser for the Admin Portal. |
| `python -m flask reset-db` | **WARNING:** Wipes all voters, votes, and blockchain data. |
| `python -m flask sync-ledger` | Manually reconciles the Voter Registry with the Blockchain. |

---

## ⚠️ Troubleshooting

**Port 8080 Process ID Error?**
If the port is in use, kill the python process or restart your terminal.

**Ghost Sessions?**
The app uses "Nuclear Session Isolation". If you get logged out unexpectedly, it is a security feature. Ensure you stay within the dashboard while voting.

---
*For detailed architecture and feature explanations, refer to [WORKFLOW.md](WORKFLOW.md).*
