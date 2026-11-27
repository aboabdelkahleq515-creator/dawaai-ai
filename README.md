---
title: Dawaai AI
emoji: 💊
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# DAWAA'I AI (دوائي) — Professional Bilingual Medicine Information Platform

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](#)
[![Python](https://img.shields.io/badge/Python-3.14-blue)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-teal)](#)
[![Tests](https://img.shields.io/badge/Tests-22%20Passed-brightgreen)](#)

> **Arabic Tagline:** "افهم دواءك، بطريقة أوضح."  
> **English Tagline:** "Understand Your Medicine. Make Informed Decisions."

---

## 1. Project Overview & Brand Identity

**Dawaa'i AI (دوائي)** is an AI-powered, bilingual healthcare web application designed to clarify prescription and over-the-counter medicine information, unpack complex patient information leaflets (PILs), and guide patients with clinically grounded, source-referenced explanations.

### Brand Personality
* **Trustworthy & Professional:** Grounded strictly in official regulatory monographs (SFDA, US FDA, EMA, WHO).
* **Modern & Accessible:** Designed with high-contrast medical palettes, clear typography, and responsive touch targets.
* **Privacy-Conscious:** Never tracks or sells private health histories; stores minimal non-sensitive activity logs; anonymizes public review names.

### Medical Grade Design System & Palette
| Token | Hex Code | Role |
| :--- | :--- | :--- |
| **Primary Dark Teal** | `#123B43` | Hero text, headers, footer background |
| **Primary Teal** | `#167D83` | Primary action buttons, badges, brand focus |
| **Secondary Turquoise** | `#38B8AC` | Accents, highlights, progress indicators |
| **Light Medical Background** | `#F4F8F8` | Page backdrop, card hover surfaces |
| **White** | `#FFFFFF` | Elevated cards, dialog surfaces, inputs |
| **Main Text** | `#172B35` | High-contrast readable body text |
| **Secondary Text** | `#647680` | Descriptive captions and timestamps |
| **Borders** | `#E0E9E9` | Clean structural dividers |
| **Success** | `#248A60` | Verified status badges, approved notices |
| **Warning** | `#C58A26` | Clinical precautions, disclaimer callouts |
| **Error** | `#C64747` | Contraindications, severe warnings |

### Typography
* **Arabic:** Cairo font family with proper RTL directionality, natural line-heights, and mirrored icons.
* **English:** Inter font family with clean LTR typographic hierarchies.

---

## 2. Complete Bilingual Experience (Arabic & English)

* Main navigation toggle (`العربية | EN`) with persistent language storage in `localStorage` and user database profile.
* Switching language updates:
  * `document.documentElement.lang = "ar"` or `"en"`
  * `document.documentElement.dir = "rtl"` or `"ltr"`
* Every interface element, button, notification, search placeholder, review dialog, and empty state is localized via `static/js/i18n.js`.
* Allows searching medicines in both Arabic ("بنادول", "أوجمنتين", "باراسيتامول") and English ("Panadol", "Augmentin", "Paracetamol").

---

## 3. Real Google Sign-In & Authentication

* **Google Identity Services (GSI):** Integrated client SDK (`accounts.google.com/gsi/client`) configured with `GOOGLE_CLIENT_ID`.
* **Backend Token Verification:** `POST /api/auth/google` verifies ID tokens against Google's tokeninfo API (`https://oauth2.googleapis.com/tokeninfo`), validating issuer (`accounts.google.com`), audience (`GOOGLE_CLIENT_ID`), expiration, and verified email status.
* **Session Handling:** Issues signed JWT session tokens (`HS256`) stored securely and verified on protected endpoints (`/api/auth/me`, `/api/reviews`, `/api/reviews/me/status`).
* **Local Testing Convenience:** `POST /api/auth/demo-login` issues real signed JWT tokens and creates real user database records, allowing testing without cloud credentials.
* **First-Time User Onboarding:** Guided dialog presenting platform capabilities, source citations, privacy commitments, and language selection.

---

## 4. Mandatory First-Use Review System

The platform implements a database-backed review system ensuring that first-time authenticated users provide feedback following their first meaningful interaction:

### Meaningful Use Definition
A meaningful use is counted only when an authenticated user successfully:
1. Opens verified medicine details after a successful search (`medicine_view`).
2. Successfully processes a medicine leaflet (`leaflet_processed`).
3. Receives a source-grounded assistant explanation (`assistant_explanation`).
4. Successfully scans a medicine package (`medicine_scanned`).

Merely opening the homepage or clicking a navigation tab does not count as meaningful use.

### Review Workflow & Dialog
* The requested clinical action completes and results are displayed first.
* The review modal appears with:
  * 5 accessible rating buttons with star labels:
    * 1: **سيئة جدًا** / Very poor
    * 2: **سيئة** / Poor
    * 3: **مقبولة** / Fair
    * 4: **جيدة جدًا** / Very good
    * 5: **ممتازة** / Excellent
  * Optional feedback text field ("شاركنا رأيك أو اقتراحاتك...").
  * Optional category selector (Ease of use, Medicine search, Leaflet reader, AI explanations, Website design, Other).
  * Public display consent toggle.
* **Database Persistence & Constraints:** `reviews` table enforces a `UNIQUE(user_id, review_type)` constraint, rejecting duplicate first-use submissions with HTTP 409 Conflict.
* **Admin Moderation:** Endpoint `POST /api/reviews/admin/{id}/moderate` allows approving or hiding inappropriate comments without altering the numeric rating.

---

## 5. Real Database Usage Statistics & Public Reviews

* `GET /api/public/statistics`:
  * **Registered Users:** `SELECT COUNT(*) FROM users;`
  * **Verified Medicine Records:** `SELECT COUNT(*) FROM medicines WHERE is_verified = 1;`
  * **Successfully Processed Documents:** `SELECT COUNT(*) FROM processed_documents WHERE is_successful = 1;`
  * **Published User Reviews:** `SELECT COUNT(*) FROM reviews WHERE is_published = 1 AND moderation_status = 'approved';`
  * **Average User Rating:** `SELECT AVG(rating) FROM reviews WHERE is_published = 1 AND moderation_status = 'approved';`
* **Zero-Data State:** If no users or reviews exist, honest zero-data copy is displayed ("نبدأ رحلتنا معًا: عدد المستخدمين المسجلين: 0"). No invented numbers.
* `GET /api/reviews/public`:
  * Real reviews with rating distribution breakdown (1 to 5 stars).
  * Filterable by star rating.
  * Masks user names (e.g., "Ahmed M." or "مستخدم موثق") to preserve privacy; never exposes email addresses or internal IDs.

---

## 6. Functional Core Tools

1. **Medicine Search (`/search`):** Real-time verified medicine catalog search with therapeutic category filters and detailed clinical modal (Indications, Dosage, Contraindications, Adverse effects, Drug & food interactions, Pregnancy safety, Storage, Source URL).
2. **Medicine Box Scanner (`/scan`):** OCR image and keyword extractor with fuzzy matching algorithm against verified medicine active ingredients. Includes pre-loaded samples (Panadol 500mg, Augmentin 1g, Brufen 400mg) for zero-friction testing.
3. **Leaflet Reader (`/leaflet`):** Patient information leaflet parser with structured sectioning and a **"Simplify Medical Terms" (تبسيط المصطلحات الطبية)** toggle translating clinical jargon into patient-friendly wording.
4. **AI Medicine Assistant (`/assistant`):** Grounded conversational interface citing official regulatory authorities (SFDA, EMA, FDA, WHO) with safety caveats and disclaimers. Compatible with Google Gemini API when configured, with a built-in clinical pharmacology engine fallback when unconfigured.

---

## 7. Project Structure

```
dawaai-ai/
├── app/
│   ├── config.py             # App settings, JWT parameters, environment variables
│   ├── database.py           # SQLite connection with WAL mode, schema tables & indexes
│   ├── models.py             # Pydantic schemas (User, Review, Medicine, Leaflet, etc.)
│   ├── auth.py               # Google OAuth token verification, JWT issuance, dependencies
│   ├── medicines_db.py       # Verified clinical catalog (SFDA, FDA, EMA records)
│   ├── routers/
│   │   ├── auth.py           # Auth endpoints (/api/auth/google, /api/auth/demo-login, /api/auth/me)
│   │   ├── medicines.py      # Catalog search & details (/api/medicines)
│   │   ├── scan.py           # Box packaging scanner (/api/scan)
│   │   ├── leaflets.py       # Leaflet parser & simplifier (/api/leaflets/parse)
│   │   ├── assistant.py      # Grounded AI assistant (/api/assistant/chat)
│   │   ├── reviews.py        # Review status, submission, public reviews & admin
│   │   └── statistics.py     # Database-backed public statistics (/api/public/statistics)
│   └── main.py               # FastAPI application, CORS, static mounting
├── static/
│   ├── index.html            # Complete bilingual SPA
│   ├── css/
│   │   └── styles.css        # Medical design system, tokens, responsive layouts
│   └── js/
│       ├── i18n.js           # Arabic & English translation engine
│       ├── api.js            # Frontend API client with JWT header
│       └── app.js            # UI controller, routing, review modal, interactive tools
├── tests/
│   ├── test_auth.py          # Authentication & token tests
│   ├── test_reviews.py       # Mandatory review & duplicate prevention tests
│   ├── test_statistics.py    # Database aggregation & privacy tests
│   ├── test_medicines.py     # Bilingual search & clinical tools tests
│   └── test_api_public.py    # Public routes & admin authorization tests
├── .env.example              # Documented environment variables template
├── run.py                    # Server launcher
└── README.md                 # Project documentation
```

---

## 8. Local Setup & Execution Guide

### Prerequisites
* Python 3.10+ (tested on Python 3.14)
* Virtual environment (`.venv`)

### Installation & Execution
```powershell
# Navigate to project directory
cd C:\Users\abdom\.gemini\antigravity\scratch\dawaai-ai

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start the application server
python run.py
```
Open your browser at: **`http://localhost:8000`**

### Running the Test Suite
```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```
All **22 tests** run and pass in under 1 second.

---

## 9. Google OAuth Configuration Steps

To configure Google Identity Services for production:
1. Visit the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a new OAuth 2.0 Client ID for **Web application**.
3. Under **Authorized JavaScript origins**, add:
   * `http://localhost:8000`
   * `http://127.0.0.1:8000`
   * Your production domain (e.g. `https://dawaai.ai`)
4. Copy the generated Client ID and paste it into `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   ```
5. Restart the server (`python run.py`). The Google Identity Services button on `/login` will authenticate directly with Google accounts.
