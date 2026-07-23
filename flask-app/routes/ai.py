from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import User, Account, Conversation
import yfinance as yf
import base64
import requests
import json
import re

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _get_groq_api_key():
    api_key = current_app.config.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Add it to your .env file or Render environment variables.")
    return api_key


def _extract_groq_response(resp):
    try:
        payload = resp.json()
    except ValueError:
        payload = {}

    if not resp.ok:
        detail = payload.get("error", {}).get("message") or resp.text or "Groq API request failed"
        raise RuntimeError(f"Groq API error {resp.status_code}: {detail}")

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Groq API returned an unexpected response.")


def generate_ai_text(prompt, model_name=None, response_format=None, max_completion_tokens=2048):
    model = model_name or current_app.config.get("GROQ_MODEL", "llama-3.1-8b-instant")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_completion_tokens": max_completion_tokens,
    }
    if response_format:
        body["response_format"] = response_format

    resp = requests.post(
        GROQ_CHAT_URL,
        headers={
            "Authorization": f"Bearer {_get_groq_api_key()}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    return _extract_groq_response(resp)


def generate_ai_from_image(prompt, image_data, mime_type):
    model = current_app.config.get("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")
    image_b64 = base64.b64encode(image_data).decode("utf-8")
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_completion_tokens": 1024,
        "response_format": {"type": "json_object"},
    }

    resp = requests.post(
        GROQ_CHAT_URL,
        headers={
            "Authorization": f"Bearer {_get_groq_api_key()}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=90,
    )
    return _extract_groq_response(resp)


def clean_json(text):
    """Strip markdown code fences around JSON if present."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# ── AI Chat Assistant ──────────────────────────────────────────────────────────

@ai_bp.route("/assistant", methods=["POST"])
@jwt_required()
def ai_assistant():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        user = User.query.get(user_id)
        account = Account.query.filter_by(user_id=user_id).first()

        context = f"""You are an expert AI financial advisor specializing in the Indian financial market. The user's name is {user.fname} {user.lname}.
User financial profile:
- Monthly Income: ₹{account.monthly_income if account else 'N/A'}
- Total Balance: ₹{account.total_balance if account else 'N/A'}
- Amount Invested: ₹{account.amount_invested if account else 'N/A'}
- Monthly Budget: ₹{account.monthly_budget if account else 'N/A'}

You ONLY answer questions about finance, investments, stocks, mutual funds, SIP, PPF, NPS, crypto, real estate, savings, retirement, and economics with a focus on Indian markets (NSE/BSE, SEBI regulations, Indian tax laws).
All monetary amounts should be in Indian Rupees (₹). Address the user by their first name. Refuse politely if the topic is not finance-related.
"""
        ai_response = generate_ai_text(context + "\n\nUser: " + prompt)

        conv = Conversation(user_id=user_id, prompt=prompt, response=ai_response)
        db.session.add(conv)
        db.session.commit()

        return jsonify({"ai_response": ai_response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route("/assistant/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    history = (
        Conversation.query
        .filter_by(user_id=user_id)
        .order_by(Conversation.created_at.asc())
        .all()
    )
    return jsonify({"history": [c.to_dict() for c in history]}), 200


@ai_bp.route("/assistant/history", methods=["DELETE"])
@jwt_required()
def clear_history():
    user_id = int(get_jwt_identity())
    Conversation.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"message": "History cleared"}), 200


# ── Financial Health Score ─────────────────────────────────────────────────────

@ai_bp.route("/financial-health-score", methods=["POST"])
@jwt_required()
def financial_health_score():
    data = request.get_json()
    fields = ["monthly_income", "total_expenses", "total_debt",
              "total_investments", "total_savings", "emergency_fund"]
    for f in fields:
        if data.get(f) is None:
            return jsonify({"error": f"{f} is required"}), 400

    prompt = f"""Analyze the following financial data of an Indian user and provide a financial health score from 0 to 100.
Monthly Income: ₹{data['monthly_income']}
Total Expenses: ₹{data['total_expenses']}
Total Debt: ₹{data['total_debt']}
Total Investments: ₹{data['total_investments']}
Total Savings: ₹{data['total_savings']}
Emergency Fund: ₹{data['emergency_fund']}

Provide:
1. A score out of 100
2. Brief analysis of each metric in Indian context (suggest SIP, PPF, FD, NPS where relevant)
3. Top 3 improvement recommendations tailored for Indian investors
All monetary values are in Indian Rupees (₹).
Format your response in clear sections with headers."""

    try:
        return jsonify({"ai_response": generate_ai_text(prompt)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Risk Assessment ────────────────────────────────────────────────────────────

@ai_bp.route("/risk-assessment", methods=["POST"])
@jwt_required()
def risk_assessment():
    data = request.get_json()
    required = ["age", "income", "savings", "experience", "time_horizon",
                "market_drop", "financial_goal", "loss_tolerance", "take_loan"]
    for f in required:
        if data.get(f) is None:
            return jsonify({"error": f"{f} is required"}), 400

    prompt = f"""Based on the following investor profile, assess the risk level (Low/Medium/High) and suggest an investment strategy:

Age Group: {data['age']}
Income Source: {data['income']}
Monthly Savings %: {data['savings']}
Investment Experience: {data['experience']}
Time Horizon: {data['time_horizon']}
Reaction to 20% market drop: {data['market_drop']}
Financial Goal: {data['financial_goal']}
Maximum Loss Tolerance: {data['loss_tolerance']}
Uses Credit/Loans: {data['take_loan']}

Provide:
1. Risk Category: Low / Medium / High
2. Explanation of the risk category
3. Recommended investment strategy with specific asset allocation percentages
4. Suggested investment instruments"""

    try:
        return jsonify({"ai_response": generate_ai_text(prompt)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Goal-Based Planning ────────────────────────────────────────────────────────

@ai_bp.route("/goal-planning", methods=["POST"])
@jwt_required()
def goal_planning():
    data = request.get_json()
    required = ["title", "target_amount", "savings", "time_horizon",
                "risk_preference", "monthly_investment"]
    for f in required:
        if data.get(f) is None:
            return jsonify({"error": f"{f} is required"}), 400

    prompt = f"""Evaluate the following financial goal of an Indian investor and provide a detailed investment plan:

Goal: {data['title']}
Target Amount: ₹{data['target_amount']}
Current Savings: ₹{data['savings']}
Time Horizon: {data['time_horizon']} years
Risk Preference: {data['risk_preference']}
Monthly Investment Capability: ₹{data['monthly_investment']}

Provide:
1. Is this goal achievable? (Yes/No/Partially)
2. Required monthly SIP/investment to reach the goal
3. Recommended investment mix from Indian instruments (Mutual Funds, SIP, PPF, NPS, FD, Stocks on NSE/BSE, Gold ETF)
4. Key milestones
5. Motivational advice
All amounts are in Indian Rupees (₹)."""

    try:
        return jsonify({"ai_response": generate_ai_text(prompt)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Receipt / Spending Scanner ─────────────────────────────────────────────────

@ai_bp.route("/scan-receipt", methods=["POST"])
@jwt_required()
def scan_receipt():
    if "receipt" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["receipt"]
    image_data = file.read()
    mime_type = file.content_type or "image/jpeg"

    prompt = """Analyze this receipt image and extract the following information in JSON format:
{
  "amount": <number>,
  "date": "<ISO date string>",
  "description": "<brief description>",
  "merchant_name": "<store or merchant name>",
  "category": "<one of: groceries, housing, entertainment, transportation, healthcare, education, shopping, food, personal, utilities, other-expense>"
}
Return ONLY the JSON object, no extra text."""

    try:
        raw = generate_ai_from_image(prompt, image_data, mime_type)
        try:
            result = json.loads(clean_json(raw))
        except json.JSONDecodeError:
            result = {"raw": raw}
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Stock Investment Suggestion ────────────────────────────────────────────────

@ai_bp.route("/stock-suggestion", methods=["POST"])
@jwt_required()
def stock_suggestion():
    data = request.get_json()
    ticker = (data.get("stock") or "").upper().strip()
    if not ticker:
        return jsonify({"error": "Stock ticker is required"}), 400

    # Fetch real data from yfinance
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1mo")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        pe_ratio = info.get("trailingPE", "N/A")
        market_cap = info.get("marketCap", "N/A")
        sector = info.get("sector", "N/A")
        summary = info.get("longBusinessSummary", "")[:500]
        price_change_1mo = None
        if not hist.empty:
            price_change_1mo = round(
                ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100, 2
            )
    except Exception as e:
        return jsonify({"error": f"Could not fetch stock data: {str(e)}"}), 500

    prompt = f"""Provide an investment analysis for {ticker} for an Indian investor:

Company Overview: {summary}
Current Price: {current_price}
P/E Ratio: {pe_ratio}
Market Cap: {market_cap}
Sector: {sector}
1-Month Price Change: {price_change_1mo}%

Provide:
1. Investment recommendation (Buy / Hold / Sell)
2. Risk level (Low/Medium/High)
3. Key strengths
4. Key risks
5. Short-term and long-term outlook
6. Suitability for Indian investors (mention any relevant SEBI/tax considerations if applicable)"""

    try:
        return jsonify({
            "ticker": ticker,
            "current_price": current_price,
            "pe_ratio": pe_ratio,
            "market_cap": market_cap,
            "sector": sector,
            "price_change_1mo": price_change_1mo,
            "ai_response": generate_ai_text(prompt),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── News Summary ───────────────────────────────────────────────────────────────

@ai_bp.route("/news-summary", methods=["POST"])
@jwt_required()
def news_summary():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    prompt = f"""Summarize the financial news article at the following URL for an investor audience.
URL: {url}

Provide:
1. Brief summary (3-4 sentences)
2. Key financial impact
3. Affected sectors or assets
4. Investor takeaway"""

    return jsonify({"ai_response": generate_ai_text(prompt)}), 200


# ── Stock News ─────────────────────────────────────────────────────────────────

@ai_bp.route("/stock-news", methods=["GET"])
@jwt_required()
def stock_news():
    ticker = request.args.get("ticker", "").upper().strip()
    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    news_api_key = current_app.config.get("NEWS_API_KEY", "")
    # Derive a clean search query from ticker (strip .NS/.BO)
    query = ticker.replace(".NS", "").replace(".BO", "")

    # ── Try NewsAPI first ──────────────────────────────────────────────────────
    if news_api_key:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "language": "en", "pageSize": 12, "sortBy": "publishedAt"},
                headers={"X-Api-Key": news_api_key},
                timeout=8,
            )
            articles = resp.json().get("articles", [])
            result = [
                {
                    "title": a.get("title", ""),
                    "publisher": (a.get("source") or {}).get("name", ""),
                    "link": a.get("url", ""),
                    "published_at": a.get("publishedAt", ""),
                    "thumbnail": a.get("urlToImage", ""),
                }
                for a in articles if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
            return jsonify({"news": result, "ticker": ticker}), 200
        except Exception:
            pass  # fall through to yfinance

    # ── Fallback: yfinance ─────────────────────────────────────────────────────
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []
        result = []
        for item in raw_news[:12]:
            content = item.get("content", item)
            thumb = ""
            for src in [content, item]:
                res = (src.get("thumbnail") or {}).get("resolutions", [])
                if res:
                    thumb = res[0].get("url", "")
                    break
            result.append({
                "title": content.get("title") or item.get("title", ""),
                "publisher": (content.get("provider") or {}).get("displayName", "") or item.get("publisher", ""),
                "link": (content.get("canonicalUrl") or {}).get("url", "") or item.get("link", ""),
                "published_at": content.get("pubDate", "") or item.get("providerPublishTime", ""),
                "thumbnail": thumb,
            })
        if not result:
            return jsonify({"error": "No news found. Please add a NEWS_API_KEY in .env for reliable news."}), 404
        return jsonify({"news": result, "ticker": ticker}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
