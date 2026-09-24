# 🔄 ECI SecureVote - System Design & Workflow Specification

**Version:** 2.0 (Final Release)  
**Date:** January 2026  
**System Type:** Decentralized Electronic Voting Infrastructure

---

## 1. 🏗️ System Architecture Overview

The ECI SecureVote system uses a hybrid architecture that separates the **Identity Layer** (SQL Database) from the **Transaction Layer** (Blockchain Ledger). This ensures that while voter *eligibility* is centrally verified, the *vote itself* is decentralized and immutable.

### 1.1 Core Modules & Files

| Module | File Path | Functionality |
| :--- | :--- | :--- |
| **Server Runtime** | `run.py` | The application entry point. Initializes the Flask server on Port 8080. |
| **Logic Controller** | `backend/app/views.py` | The "Brain". Handles routing, session "nuclear" lifecycle, blockchain mining triggers, and admin logic. |
| **Blockchain Engine** | `backend/app/blockchain.py` | The "Heart". Manages the chain, Proof-of-Work (PoW) mining, ECDSA signature verification, and mempool. |
| **Data Models** | `backend/app/models.py` | Defines the schema for Voters, Registration Requests, and Admins (SQLAlchemy). |
| **Configuration** | `backend/config.py` | Manages environment variables, database URI, and secret keys. |
| **Frontend** | `frontend/templates/` | Jinja2 HTML templates (`eci_portal.html`, `index.html`) with anti-cache scripts. |

---

## 2. 🗄️ Database & Data Schema

The system uses efficient structures to manage state.

### 2.1 SQL Database (Identity)
Stored in `backend/instance/voting_system.db`.

**Table: `voter`**
- `voter_id` (PK): Unique string (e.g., "CRYV83921")
- `full_name`: String
- `dob`: Date String (YYYY-MM-DD)
- `phone`: String (Indexed for fast lookup)
- `public_key`: Text (PEM format public key for verifying signatures)
- `has_voted`: Boolean (Prevents double voting)

**Table: `registration_request`**
- `id` (PK): Integer
- `full_name`, `dob`, `phone`, `address`: Applicant details
- `status`: Enum ("Pending", "Approved", "Rejected")

### 2.2 Blockchain Structure (Transaction)
Stored in `BlockModel` and `MempoolModel` for total persistence across restarts.

**Block Structure (3-Tx Bundle)**
Each block contains a mandatory batch of 3 transactions to ensure cryptographic density.
```json
{
  "index": 1,
  "timestamp": 1234567890.123,
  "transactions": [
    { "voter_id": "...", "party": "...", "timestamp": "...", "signature": "...", "public_key": "..." },
    { "voter_id": "...", "party": "...", "timestamp": "...", "signature": "...", "public_key": "..." },
    { "voter_id": "...", "party": "...", "timestamp": "...", "signature": "...", "public_key": "..." }
  ],
  "previous_hash": "a1b2c3d4...",
  "nonce": 4291,
  "hash": "0000a1b2..."
}
```

---

## 3. 🚦 Detailed Step-by-Step Workflows

These algorithms describe the exact logic flow for key operations.

### 3.1 Voter Registration Algorithm (Form 6)
**Goal:** Verify identity and issue a unique crypto-ID.

1.  **User Action**: User submits Name, DOB, Phone, Address on `/register`.
2.  **System Check**: Server queries `RegistrationRequest` table for `(name + phone)`.
    *   *If Found*: Return "Already Applied".
    *   *If New*: Create new `RegistrationRequest` with status `Pending`.
3.  **Admin Action**: Admin logs in to `/admin` and views "Pending Applications".
4.  **Approval Logic**:
    *   Admin clicks "Approve".
    *   System generates `voter_id` = "CRYV" + 5 Random Digits.
    *   System generates Keypair: `private_key` (temporary), `public_key` (stored).
    *   System creates new row in `Voter` table.
    *   System updates `RegistrationRequest` status to `Approved`.
5.  **Result**: Voter is live and can be searched.

### 3.2 The "Nuclear" Voting Session Algorithm
**Goal:** Cast a vote without leaving any session trace.

1.  **Login**: User enters `voter_id` at `/eci-portal`.
2.  **Safety Check**:
    *   Is `voter_id` valid?
    *   Has `voter.has_voted` == `False`?
3.  **Session Creation**:
    *   Server generates a **Fresh Ephemeral Private Key** for this session.
    *   Server updates `voter.public_key` in DB to match this new key.
    *   Server stores `voter_id` and `private_key` in strict HTTP Session.
    *   User redirected to `/voter` (Dashboard).
4.  **Vote Casting (Security-First Pattern)**:
    *   User selects Party and clicks "Submit".
    *   **Phase A: Digital Seal**: Server signs `{id, party, time}` using session's `private_key`.
    *   **Phase B: Locking (Block-First)**: System marks `voter.has_voted = True` and **commits to DB immediately**. This prevents "race-condition" double-voting during mining.
    *   **Phase C: Broadcast**: Server sends `{Tx, Signature}` to Blockchain Module.
5.  **Chain Verification & Bundling**:
    *   **Deduplication**: Blockchain checks if `voter_id` is already in Mempool or Chain.
    *   **Persistent Mempool**: Tx is saved to `MempoolModel`.
    *   **Auto-Mine Trigger**: When `len(Global_Mempool) >= 3`, a block is mined.
6.  **Nuclear Cleanup**:
    *   **INSTANT ACTION**: `session.clear()` is called.
    *   User redirected to Dashboard (Locked).
    *   UI detects back-button usage and forces redirect to ECI Portal to prevent ghost session viewing.

---

## 4. 📐 Visual Architecture Diagrams

### 4.1 System Data Flow

4.1 System Data Flow

```
   [ Voter ]
       │
       ▼ (HTTPS)
  [ Web Portal ]
  (Frontend UI)
       │
       ▼ (POST Request)
  [ Flask Controller ] <──────────┐
  (Backend Logic)                 │
       │                          │
       ├─────────────────┐        │
       ▼                 ▼        │
[ Identity Zone ]   [ Transaction Zone ]
(SQLite DB)         (Blockchain Ledger)
       │                 │        │
    Check Auth        Submit      │
       │               Tx         │
       │                 │        │
    Valid ID             ▼        │
       └────────── [ Mempool ]    │
                         │        │
                         ▼        │
                  [ Miner Node ]  │
                  (Proof-of-Work) │
                         │        │
                         ▼        │
                  [ Valid Block ] │
                         │        │
                         ▼        │
                  [ Immutable ]   │
                  [  Ledger   ] ──┘
                      (Read)
```

### 4.2 The "Safe Zone" Security Logic

```
   [ USER LANDS ]
         │
         ▼
  [ ECI PORTAL ] ◄──────────────────────────┐
         │                                  │
    Enters ID                           Back Button
         │                              (Reloads)
         ▼                                  │
  [ AUTH CHECK ] ─── Invalid ──> [ ACCESS DENIED ]
         │
    Valid Credentials
         │
         ▼
 ┌── [ DASHBOARD ] ─────────┐
 │ (Session Active)         │
 │                          │
 │    [ SUBMIT VOTE ]       │
 │          │               │
 │          ▼               │
 │    [ SIGN & SEND ]       │
 │          │               │
 │          ▼               │
 │    [ RESULT PAGE ]       │
 └──────────┬────────xxxxxxx┘
            │
            ▼
 [ NUCLEAR SESSION WIPE ]
            │
            ▼
    [ SESSION DESTROYED ]
```

---

## 5. 🔐 Security Implementation Details

### 5.1 ECDSA Digital Signatures
We use **SECP256R1** (NIST P-256) curves.
*   **Why?**: It provides high security with small key sizes, suitable for rapid web signing.
*   **Process**: The vote is not just "text"; it is a cryptographic proof. Even if a hacker compromised the database, they could not fake a vote without the ephemeral private key which existed only for the 2 minutes the voter was logged in.

### 5.2 The "Ghost Session" Prevention
To prevent "back-button hacking" (where a user logs out, and the next user hits 'Back' to see their screen):
1.  **Server-Side**: `Cache-Control: no-store` header is global.
2.  **Client-Side**: A `pageshow` event listener in `base.html` detects if the page is being loaded from the browser's "BFCache" (Back-Forward Cache).
3.  **Action**: If detected, it forces a `window.location.reload()`, forcing the browser to ask the server for permission again. The server, seeing the session is dead, demands a login.

### 5.3 Proof-of-Work (PoW) Consesus
*   **Algorithm**: `SHA-256`.
*   **Difficulty**: The hash of a new block must start with `0000` (adjustable).
*   **Purpose**: Prevents spam attacks. To rewrite the history of the election, an attacker would need more computing power than the network to redo the PoW for every single block since the beginning.

---

## 6. Setup & Deployment Reference

For concise setup instructions, please refer to **[SETUP.md](SETUP.md)**.
For the master summary, refer to **[README.md](README.md)**.
