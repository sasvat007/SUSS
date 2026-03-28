# CapitalSense 💰

> **An AI-based cash flow decision intelligence system for Indian small businesses.**  

---

## The Problem

82% of small businesses fail not because they're unprofitable — but because they run out of cash at the wrong moment. Most existing tools (TallyPrime, Zoho Books, QuickBooks) tell you your balance. **None of them tell you what to do with it.**

When a small business owner has ₹80,000 in the bank and ₹1,20,000 in obligations due this week, no existing tool answers the most important question: **"Who do I pay first, and why?"**

CapitalSense does.

---

## What CapitalSense Does

CapitalSense ingests your financial documents (bank statements, invoices, handwritten receipts), builds a unified real-time picture of your cash position, and uses a deterministic decision engine to:

- Tell you exactly how many **days until you run out of cash**
- **Rank your obligations** by urgency, penalty risk, and vendor flexibility
- **Explain every decision** with full chain-of-thought reasoning
- **Draft negotiation emails** to vendors you need to defer — in the right tone
- **Simulate future scenarios** so you can plan before a crisis hits

---

## Features

| Feature | Description |
|---|---|
| 📄 **Multi-Source Document Ingestion** | Bank statements, digital invoices, physical/handwritten receipts via two-tier OCR (Tesseract + Google Cloud Vision) |
| 🏦 **Live Bank Sync** | Real-time balance via Setu Account Aggregator |
| ⏳ **Days-to-Zero Countdown** | Live liquidity runway indicator with color-coded urgency |
| ⚡ **Obligation Prioritization Engine** | Deterministic rule-based ranking by penalty risk, due date, vendor flexibility, and confidence score |
| 🧠 **Chain-of-Thought Explainability** | Every prioritization decision comes with full human-readable reasoning |
| ✉️ **Agentic Email Drafting** | Auto-drafted deferral and reminder emails with tone adapted to vendor relationship |
| 🔮 **Scenario Simulation** | What-if modeling without touching real data |
| 🤝 **Vendor Confidence Scoring** | Dynamic vendor trust scores built from payment history |
| 🔔 **Push Notifications** | Real-time alerts for liquidity drops, overdue obligations, and health score declines |
| 💬 **Financial Chatbot** | Context-aware assistant with access to your live financial state |
| 🔒 **Privacy-First Architecture** | Sensitive fields hashed, documents auto-deleted after OCR, minimal data storage |

---

## Tech Stack

### Mobile (Frontend)
- **Flutter** — Cross-platform mobile app (iOS & Android)

### Backend
- **FastAPI** — REST API framework
- **PostgreSQL** — Primary database
- **SQLAlchemy (async)** — ORM
- **Alembic** — Database migrations

### AI & Intelligence
- **Python (Deterministic Algorithm)** — Rule-based obligation prioritization engine (separate ML service)
- **Tesseract OCR** — Tier 1 OCR for printed/typed documents
- **Google Cloud Vision API** — Tier 2 OCR for handwritten receipts and low-quality images
- **GPT-4o (OpenAI)** — Agentic email drafting and chatbot

### Integrations
- **Setu Account Aggregator** — Live bank balance sync (India's AA framework)

### Security
- **JWT** — Access + refresh token authentication with rotation
- **bcrypt** — Password hashing
- **SHA-256** — Sensitive field hashing (phone, GST, invoice IDs, contact info)

---

## Architecture Overview

```
Flutter Mobile App
        │
        ▼
   FastAPI Backend
        │
   ┌────┴────────────────────────────────────┐
   │                                         │
PostgreSQL DB              External Services
   │                           │
   ├── users                   ├── Setu AA (bank balance)
   ├── obligations              ├── Google Cloud Vision (OCR)
   ├── receivables              ├── OpenAI GPT-4o (email drafts)
   ├── vendors                  └── ML Prioritization Service
   ├── funds
   ├── notifications
   ├── questionnaire_responses
   └── scenarios
```

**System Workflow:**
1. User onboards → Questionnaire captures preferences (safety buffer, delay tolerance, non-negotiables)
2. Documents uploaded → Two-tier OCR extracts structured data → Original file deleted
3. Central Financial Model built → Days-to-Zero calculated → Health Score computed
4. Liquidity conflict detected → ML engine ranks obligations with CoT reasoning
5. Deferral needed → Agentic AI drafts email with vendor-appropriate tone
6. User marks payment → Vendor confidence score updates → Engine recalculates
7. Scenario simulation → Sandbox projection without touching real data
8. Push notifications fire on threshold breaches

---

## Project Structure

```
capitalsense-backend/
├── main.py
├── .env
├── requirements.txt
├── alembic/
│   └── versions/
├── app/
│   ├── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── obligation.py
│   │   ├── receivable.py
│   │   ├── vendor.py
│   │   ├── fund.py
│   │   ├── notification.py
│   │   ├── questionnaire.py
│   │   └── scenario.py
│   ├── schemas/
│   │   └── (Pydantic v2 schemas matching models)
│   ├── routers/
│   │   ├── auth.py
│   │   ├── obligations.py
│   │   ├── receivables.py
│   │   ├── vendors.py
│   │   ├── funds.py
│   │   ├── notifications.py
│   │   ├── questionnaire.py
│   │   ├── dashboard.py
│   │   ├── scenario.py
│   │   ├── ocr.py
│   │   ├── email_draft.py
│   │   └── chatbot.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── ocr_service.py
│   │   ├── ml_service.py
│   │   ├── email_draft_service.py
│   │   ├── setu_service.py
│   │   ├── notification_service.py
│   │   └── deduplication_service.py
│   └── utils/
│       ├── hashing.py
│       ├── jwt.py
│       └── field_encryption.py
```

---

## API Reference

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login, returns JWT pair |
| POST | `/auth/refresh` | Rotate refresh token |
| POST | `/auth/logout` | Invalidate refresh token |

### Questionnaire
| Method | Endpoint | Description |
|---|---|---|
| POST | `/questionnaire/submit` | Submit onboarding or weekly questionnaire |
| GET | `/questionnaire/latest` | Get most recent responses |
| GET | `/questionnaire/due` | Check if questionnaire is due |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/summary` | Full financial snapshot (balance, days-to-zero, health score, inflows) |
| GET | `/dashboard/balance` | Fetch live balance from Setu |

### Obligations (Payables)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/obligations/` | Add new obligation |
| GET | `/obligations/` | Get all obligations ranked by priority |
| GET | `/obligations/{id}` | Get single obligation with full CoT reasoning |
| PATCH | `/obligations/{id}/mark-paid` | Mark as fully or partially paid |
| DELETE | `/obligations/{id}` | Soft delete obligation |

### Receivables
| Method | Endpoint | Description |
|---|---|---|
| POST | `/receivables/` | Add new receivable |
| GET | `/receivables/` | Get all receivables |
| GET | `/receivables/{id}` | Get single receivable |
| PATCH | `/receivables/{id}/mark-received` | Mark as fully or partially received |
| POST | `/receivables/{id}/draft-reminder` | Generate AI reminder email |

### Vendors
| Method | Endpoint | Description |
|---|---|---|
| POST | `/vendors/` | Add new vendor |
| GET | `/vendors/` | Get all vendors with confidence scores |
| GET | `/vendors/{id}` | Get vendor detail and payment history |
| PATCH | `/vendors/{id}` | Update vendor profile |

### Funds
| Method | Endpoint | Description |
|---|---|---|
| POST | `/funds/` | Add external fund source (loan etc.) |
| GET | `/funds/` | Get all fund records |
| DELETE | `/funds/{id}` | Delete fund record |

### Scenario Simulation
| Method | Endpoint | Description |
|---|---|---|
| POST | `/scenario/simulate` | Run sandbox what-if simulation |
| GET | `/scenario/history` | Get past simulation history |

### Notifications
| Method | Endpoint | Description |
|---|---|---|
| GET | `/notifications/` | Get all notifications |
| PATCH | `/notifications/{id}/read` | Mark single as read |
| PATCH | `/notifications/read-all` | Mark all as read |

### OCR
| Method | Endpoint | Description |
|---|---|---|
| POST | `/ocr/upload` | Upload document for extraction (file deleted after OCR) |

### Email Drafting
| Method | Endpoint | Description |
|---|---|---|
| POST | `/email-draft/deferral` | Draft payment deferral email |
| POST | `/email-draft/reminder` | Draft payment reminder email |

### Chatbot
| Method | Endpoint | Description |
|---|---|---|
| POST | `/chatbot/message` | Send message, get context-aware financial response |

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Tesseract OCR installed on system (`brew install tesseract` / `apt install tesseract-ocr`)
- Google Cloud Vision API key
- OpenAI API key
- Setu Account Aggregator credentials

### 1. Clone the repository
```bash
git clone https://github.com/your-org/capitalsense-backend.git
cd capitalsense-backend
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/capitalsense
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLOUD_VISION_API_KEY=your_key
OPENAI_API_KEY=your_key
SETU_CLIENT_ID=your_setu_client_id
SETU_CLIENT_SECRET=your_setu_client_secret
SETU_BASE_URL=https://aa.setu.co
ML_SERVICE_URL=http://localhost:8001
```

### 5. Set up the database
```bash
# Create PostgreSQL database
createdb capitalsense

# Run migrations
alembic upgrade head
```

### 6. Run the server
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Security Model

| Concern | Implementation |
|---|---|
| Authentication | JWT access tokens (30 min expiry) + refresh tokens (7 days) with rotation |
| Password storage | bcrypt with cost factor 12 |
| Sensitive fields | SHA-256 hashed before storage — phone, GST number, invoice IDs, contact info |
| Document files | Auto-deleted from server immediately after OCR extraction completes |
| Data minimization | Only fields required for decision engine are retained |
| Multi-tenancy | Every DB query filters by authenticated user_id — zero cross-user data leakage |
| CORS | Configured for Flutter mobile app origins only |

---

## Key Design Decisions

**Why a deterministic engine instead of pure LLM?**  
The PS3 requirement explicitly asks for deterministic scenario projections. LLMs hallucinate numerical calculations. The prioritization logic is a rule-based weighted scoring system in Python — auditable, reproducible, and fast. GPT-4o is used only for natural language output (email drafts, chatbot responses) where creativity is an asset, not a liability.

**Why two-tier OCR?**  
Tesseract is fast and free for clean printed documents. It fails badly on handwritten text, which is extremely common in Indian small business contexts (hand-written receipts, informal chits). Google Cloud Vision handles these cases reliably. The system auto-selects based on Tesseract confidence score — the user never sees this choice.

**Why Setu?**  
Setu is India's RBI-regulated Account Aggregator framework. It is the only legally compliant, consent-based way to read a user's bank balance in India without storing their banking credentials. It also means balance data is always live, not manually entered.

**Why minimal data storage?**  
Small business owners are highly sensitive about financial data privacy. The system stores the minimum fields needed for the decision engine to function. Original documents are never persisted. Sensitive identifiers are hashed one-way and are not recoverable from the backend.

---

## Comparison With Existing Tools

| Capability | TallyPrime | Zoho Books | CredFlow | **CapitalSense** |
|---|---|---|---|---|
| Multi-source data ingestion | Partial | Partial | Partial | **Full** |
| Liquidity conflict detection | None | Partial | Partial | **Full** |
| Obligation prioritization engine | None | None | None | **Full** |
| Automated action drafting | Limited | Limited | Limited | **Full** |
| Chain-of-thought explainability | None | None | None | **Full** |
| Handwritten receipt ingestion | None | Limited | Limited | **Full** |
| Mobile-native | Partial | Partial | No | **Full** |

---

## Team

**Team Name:** RUSS  
**Team Leader:** Siddharth S  

---

## License

All rights reserved by Team RUSS.
