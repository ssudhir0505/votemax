# 🇮🇳 ECI SecureVote: Next-Gen Blockchain Voting System

### A Quantum-Leap in Electoral Integrity & Privacy

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Security](https://img.shields.io/badge/Security-ECDSA%20%2B%20AES-red)
![Blockchain](https://img.shields.io/badge/Ledger-Immutable-orange)

---

## 📖 Abstract

**ECI SecureVote** is a demonstration of a cryptographic, blockchain-backed electronic voting infrastructure designed to solve the "Trilemma of E-Voting": **Anonymity, Integrity, and Transparency**. 

Unlike traditional centralized databases where a single admin can manipulate counts, SecureVote utilizes a decentralized ledger where every vote is cryptographically signed, timestamped, and chained. It introduces a novel **"Nuclear Session Isolation"** protocol, ensuring that voter identity is strictly ephemeral—existing only for the precise moments of casting a ballot before being irretrievably wiped from the server.

> *"The essence of democracy is not just that every vote counts, but that every vote is provably counted and impossible to trace back to the voter."*

---

## 📑 Documentation Suite

This project is documented in three specialized files to keep information organized:

- **[🛠️ SETUP.md](SETUP.md)**: **Start Here.** A crisp, step-by-step guide to installing and running the app.
- **[🔄 WORKFLOW.md](WORKFLOW.md)**: Detailed architectural diagrams, logic flows, and deep-dives into the blockchain algorithm.
- **[📂 Source Code](/backend)**: The complete Python implementation of the blockchain node and web server.

---

## ⚡ Key Innovations & Features

### 1. The "Nuclear" Session Protocol ☢️
We implemented an aggressive security policy to prevent "Session Hijacking" or "Ghost Sessions" (where a user leaves a terminal and the next person can access their account).
- **Voter Safe Zone**: The server maintains a strict whitelist of "safe" URLs.
- **Instant Kill Switch**: The moment a voter navigates away from the voting terminal (even to the "About" page), their session is **instantly destroyed** server-side.
- **Anti-Cache Armor**: Hardened headers force the browser to never cache sensitive pages, ensuring the "Back" button cannot resurrect a dead session.

### 2. Immutable Blockchain Ledger ⛓️
Votes are not just rows in a database; they are blocks in a chain.
- **Strict 3-Tx Bundling**: Blocks are only mined when exactly 3 transactions are pending, ensuring a dense, organized ledger.
- **Tamper-Proof**: Modifying a past vote changes its cryptographic hash, breaking the link to all subsequent blocks.
- **Persistent Mempool**: Pending votes are stored in a SQL database to survive server restarts.

### 3. Cryptographic Identity & Security 🔐
- **Block-First Locking**: To prevent double-voting race conditions, the system marks a voter as "Voted" in the database **before** starting the heavy mining process.
- **ECDSA Signatures**: Every vote is signed with a private key generated on-the-fly for the valid session.
- **Anonymity**: The link between Voter ID and the content of the vote is cryptographically decoupled.

---

## 💻 Tech Stack & Dependencies

The system is built on a robust, lightweight stack optimized for educational clarity and performance.

### Core Backend
- **Language**: Python 3.x
- **Framework**: Flask (Microframework for Web)
- **Database**: SQLite (SQLAlchemy ORM) - *Used for the ephemeral state (User Registry), while votes live in the JSON Blockchain.*

### Cryptography Engine
- **Library**: `cryptography` (Python)
- **Algorithms**:
    - **SHA-256**: Hashing blocks and transactions.
    - **SECP256R1 (NIST P-256)**: Elliptic Curve Digital Signature Algorithm for vote authentication.

### Frontend Interface
- **HTML5/CSS3**: Custom "Glassmorphism" UI variables for a modern, government-tech aesthetic.
- **JavaScript (Vanilla)**: For client-side session heartbeats and dynamic DOM manipulation (no heavy framework overhead).

---

## 🔬 Research & References

This project draws inspiration from several pivotal concepts in digital democracy:

1.  **Nakamoto, S. (2008)**: *Bitcoin: A Peer-to-Peer Electronic Cash System.* (Foundational concept for the immutable ledger structure).
2.  **Estonian Internet Voting System**: Concepts of digital ID binding and separation of identification from the voting act.
3.  **Zero-Knowledge Proofs**: The principle of proving valid citizenship without revealing the exact identity during the tallying phase (simulated via our Token system).

---

## 🚀 How It Works (Simplified)

### Reference Flow
For the detailed technical diagrams, please see **[WORKFLOW.md](WORKFLOW.md)**.

1.  **Registration**: A citizen submits **Form 6** (Name, DOB, Mobile).
2.  **Verification**: An Admin approves the request, generating a unique **Voter ID** and **Private Key**.
3.  **The Vote**:
    - Voter logs in with their ID.
    - The server validates eligibility (has not voted yet).
    - Voter selects a candidate.
    - The vote is **Signed** with the session keys and **Broadcast** to the Mempool.
4.  **The Mining**:
    - The system (consensus node) validates the digital signature.
    - Valid votes are packed into a Block.
    - The block is "Mined" (Proof-of-Work) and added to the Chain.
5.  **The Result**: The vote is now eternal. Any attempt to change it is mathematically impossible.

---

*Project developed for [Your Course/Institution Name] - 2026*
