# AI-Powered Financial & Investment Advisory System
## Python Flask + MySQL + Tailwind CSS + Google Gemini

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Framework** | Flask 3.0 + FastAPI-style REST API |
| **Database** | MySQL (via SQLAlchemy ORM) |
| **Auth** | JWT (Flask-JWT-Extended) + bcrypt |
| **AI / LLM** | Google Gemini (`gemini-1.5-flash`) |
| **Financial Data** | yfinance (live stock data) |
| **ML Libraries** | Scikit-learn, Pandas, NumPy |
| **Charts** | Chart.js (Doughnut, Bar) |
| **Frontend** | HTML5 + CSS3 + Vanilla JavaScript |
| **Styling** | Custom CSS (dark theme, responsive) |

---

## Features

- 🔐 **Authentication** — Register, Login, Logout, Delete account (JWT cookies)
- 📊 **Dashboard** — Balance, investments, spending chart, recent transactions
- 🤖 **AI Chat Advisor** — Gemini-powered financial Q&A with history
- ⚠️ **Risk Assessment** — 9-factor risk profile → Low/Medium/High strategy
- 🎯 **Goal-Based Planning** — AI investment plan to reach your goals
- ❤️ **Financial Health Score** — 0–100 score with recommendations
- 📷 **Receipt Scanner** — Upload receipt → Gemini extracts amount/category
- 💳 **Transactions** — Paginated table, category badges, detail modal
- 📰 **Stock News** — Live yfinance news + AI stock recommendation
- 🔔 **Notifications** — Activity feed (login, updates, etc.)
- 👤 **Profile** — Edit name, email, password, avatar URL
- 💳 **Billing** — Account details + card management

---

## Setup

### 1. Prerequisites

- Python 3.10+
- MySQL 8.0+ running locally (or cloud)
- Google Gemini API key → https://aistudio.google.com/app/apikey

### 2. Create virtual environment

```bash
cd flask-app
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create MySQL database

```sql
CREATE DATABASE financial_advisory;
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=financial_advisory

SECRET_KEY=your-flask-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
```

### 6. Run the application

```bash
python run.py
```

Open your browser at: **http://localhost:5000**

---

## Project Structure

```
flask-app/
├── run.py                  # Entry point
├── app.py                  # Flask application factory
├── config.py               # Configuration (env vars)
├── extensions.py           # SQLAlchemy, Bcrypt, JWT
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
│
├── models/
│   └── models.py           # SQLAlchemy models (User, Account, Card, Transaction, etc.)
│
├── routes/
│   ├── auth.py             # /api/auth/* (register, login, logout, delete)
│   ├── user.py             # /api/user/* (profile, account, card, notifications)
│   ├── transactions.py     # /api/transactions/* (add, list, totals, statistics)
│   ├── ai.py               # /api/ai/* (Gemini + yfinance)
│   ├── contact.py          # /api/contact/
│   └── pages.py            # HTML page routes
│
├── templates/
│   ├── base.html           # Base HTML layout
│   ├── home.html           # Landing page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # Main dashboard
│   ├── ai_assistant.html   # AI chat
│   ├── risk_assessment.html
│   ├── goal_planning.html
│   ├── financial_health.html
│   ├── spendings.html      # Add spending + receipt scanner
│   ├── transactions.html   # Transaction history
│   ├── news.html           # Stock news + AI insights
│   ├── profile.html
│   ├── billing.html
│   ├── account.html
│   ├── notifications.html
│   ├── contact.html
│   └── partials/
│       └── sidebar.html    # Reusable sidebar + topbar macros
│
└── static/
    ├── css/
    │   └── style.css       # Complete dark-theme stylesheet
    └── js/
        └── app.js          # API helpers, markdown renderer, utilities
```

---

## API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login (sets JWT cookie) |
| POST | `/api/auth/logout` | Logout (clears cookie) |
| GET | `/api/auth/me` | Get current user |
| DELETE | `/api/auth/delete` | Delete account + all data |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/api/user/update/<id>` | Update profile |
| GET | `/api/user/account` | Get account details |
| POST | `/api/user/account-details` | Save account + card |
| GET | `/api/user/card` | Get cards |
| GET | `/api/user/notifications` | Get notifications |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/transactions/add` | Add transaction |
| GET | `/api/transactions/` | Get all transactions |
| GET | `/api/transactions/total` | Total spending amount |
| GET | `/api/transactions/statistics` | Spending by category |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/assistant` | Chat with AI advisor |
| GET | `/api/ai/assistant/history` | Chat history |
| POST | `/api/ai/financial-health-score` | Health score |
| POST | `/api/ai/risk-assessment` | Risk profile |
| POST | `/api/ai/goal-planning` | Goal investment plan |
| POST | `/api/ai/scan-receipt` | Scan receipt image |
| POST | `/api/ai/stock-suggestion` | Stock AI analysis |
| POST | `/api/ai/news-summary` | Summarize news URL |
| GET | `/api/ai/stock-news?ticker=TSLA` | Live stock news |

---

## Database Schema (MySQL)

```
users          — id, fname, lname, email, password, profile_img, signup_method
accounts       — id, user_id, total_balance, amount_invested, monthly_income, monthly_budget, account_type
cards          — id, user_id, card_number, card_holder, card_cvc
transactions   — id, user_id, amount, merchant_name, date, category, description
notifications  — id, user_id, type, title, message
conversations  — id, user_id, prompt, response
contacts       — id, name, email, subject, message
```
