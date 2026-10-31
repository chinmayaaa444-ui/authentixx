
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlsplit
from pathlib import Path
from datetime import datetime
import sqlite3
import ipaddress
import json
import re
import difflib

app = Flask(__name__)

# ==========================================================
# PATHS AND DATABASE
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "authentix.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_type TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        connection.commit()


def record_scan(scan_type, risk_score, risk_level):
    with get_db_connection() as connection:
        connection.execute("""
            INSERT INTO scans (
                scan_type, risk_score, risk_level, created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            scan_type,
            int(risk_score),
            risk_level,
            datetime.now().astimezone().isoformat(timespec="seconds")
        ))
        connection.commit()


def get_dashboard_stats():
    with get_db_connection() as connection:
        totals = connection.execute("""
            SELECT
                COUNT(*) AS total_scans,
                SUM(CASE WHEN risk_score < 25 THEN 1 ELSE 0 END)
                    AS low_risk_scans,
                SUM(CASE WHEN risk_score >= 25 THEN 1 ELSE 0 END)
                    AS flagged_scans
            FROM scans
        """).fetchone()

        recent = connection.execute("""
            SELECT scan_type, risk_score, risk_level, created_at
            FROM scans
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

    return {
        "total_scans": totals["total_scans"] or 0,
        "low_risk_scans": totals["low_risk_scans"] or 0,
        "flagged_scans": totals["flagged_scans"] or 0,
        "recent_activity": [
            {
                "scan_type": row["scan_type"],
                "risk_score": row["risk_score"],
                "risk_level": row["risk_level"],
                "created_at": row["created_at"]
            }
            for row in recent
        ]
    }


initialize_database()


# ==========================================================
# DATASET LOADER
# ==========================================================

def load_dataset(filename):
    path = BASE_DIR / filename

    if not path.exists() or path.stat().st_size == 0:
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        print(f"Warning: Could not load {filename}.")
        return {}


DATASET_1 = load_dataset("dataset.json")
DATASET_2 = load_dataset("dataset_v2.json")
DATASETS = [DATASET_1, DATASET_2]


def unique_items(items):
    result = []
    seen = set()

    for item in items:
        if isinstance(item, str):
            cleaned = item.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)

    return result


def flatten_category(value):
    phrases = []

    if isinstance(value, list):
        phrases.extend(value)
    elif isinstance(value, dict):
        for language_phrases in value.values():
            if isinstance(language_phrases, list):
                phrases.extend(language_phrases)

    return unique_items(phrases)


def get_dataset_phrases(category, flattened_key=None):
    phrases = []

    for dataset in DATASETS:
        phrases.extend(flatten_category(dataset.get(category, [])))

        if flattened_key:
            phrases.extend(
                flatten_category(dataset.get(flattened_key, []))
            )

    return unique_items(phrases)


# ==========================================================
# ORIGINAL DETECTION PHRASES
# ==========================================================

ORIGINAL_URGENT_PHRASES = [
    "act now", "act immediately", "urgent action required",
    "immediate action required", "respond immediately",
    "respond now", "final warning", "final notice",
    "last chance", "limited time", "expires today",
    "offer expires soon", "within 24 hours",
    "within 48 hours", "account blocked",
    "account suspended", "account deactivated",
    "account will be closed", "account will be terminated",
    "your account is at risk", "avoid account suspension",
    "security alert", "unusual activity detected",
    "suspicious activity detected", "unauthorized login",
    "your account has been compromised",
    "verify your account immediately",
    "failure to respond", "immediate verification",
    "payment overdue", "payment failed",
    "service will be disconnected", "your access will expire",
    "action needed", "urgent notification",
    "important security update", "confirm immediately",
    "your profile is restricted", "your account is on hold",
    "final reminder", "deadline approaching",
    "claim before midnight", "respond within minutes",
    "immediately"
]

ORIGINAL_SENSITIVE_PHRASES = [
    "share your otp", "send your otp", "enter your otp",
    "provide your otp", "verify using otp", "otp verification",
    "share your password", "enter your password",
    "provide your password", "give out your password",
    "bank account password", "internet banking password",
    "account credentials", "login credentials",
    "bank details", "bank account details",
    "credit card details", "debit card details",
    "card number", "card security code", "cvv number",
    "share your cvv", "enter your cvv",
    "security code", "upi pin", "share your upi pin",
    "enter your upi pin", "net banking details",
    "online banking details", "payment credentials",
    "personal identification number",
    "share your aadhaar number", "aadhaar details",
    "share your pan number", "pan card details",
    "social security number", "ssn number",
    "national insurance number", "tax identification number",
    "passport number", "upload your identity document",
    "send your identity card", "share your id proof",
    "recovery phrase", "crypto wallet seed phrase",
    "private wallet key", "private key",
    "share your verification code", "send your verification code",
    "remote access code", "one time password"
]

ORIGINAL_REWARD_PHRASES = [
    "free money", "get money instantly", "win money",
    "claim your prize", "you have won", "you are a winner",
    "congratulations winner", "guaranteed reward",
    "instant cashback", "free gift card", "claim your reward",
    "earn money instantly", "limited time offer",
    "you are selected", "lucky winner", "cash prize",
    "get rich quickly", "free cash", "bonus payment",
    "exclusive reward", "unclaimed prize", "million dollar prize",
    "you won a lottery", "lottery winner", "jackpot winner",
    "claim your bonus", "free shopping voucher",
    "gift voucher", "shopping coupon", "special cash offer",
    "double your money", "guaranteed returns",
    "risk free investment", "instant profit",
    "passive income guaranteed", "make money from home",
    "work from home and earn", "investment opportunity",
    "receive free funds", "government cash benefit",
    "tax refund waiting", "refund approved",
    "free cryptocurrency", "airdrop reward",
    "claim free tokens", "exclusive giveaway"
]

ORIGINAL_IMPERSONATION_PHRASES = [
    "we are your bank", "bank security department",
    "official bank representative", "government verification",
    "tax department notification", "revenue department",
    "customs department", "police department",
    "law enforcement notice", "official support team",
    "customer care representative", "technical support team",
    "your parcel is on hold", "package delivery failed",
    "delivery address incomplete", "customs fee required",
    "pay delivery fee", "parcel awaiting payment",
    "track your package", "shipment is delayed",
    "delivery attempt failed", "pay customs charges",
    "your electricity will be disconnected",
    "your sim card will be blocked",
    "mobile number will be deactivated",
    "government subsidy approved",
    "benefit payment pending", "tax refund notification",
    "job offer selected", "you are shortlisted",
    "pay registration fee", "training fee required",
    "job security deposit", "processing fee required"
]


URGENT_PHRASES = unique_items(
    ORIGINAL_URGENT_PHRASES
    + get_dataset_phrases("urgency", "urgency_all")
)

SENSITIVE_PHRASES = unique_items(
    ORIGINAL_SENSITIVE_PHRASES
    + get_dataset_phrases("sensitive", "sensitive_all")
)

REWARD_PHRASES = unique_items(
    ORIGINAL_REWARD_PHRASES
    + get_dataset_phrases("rewards", "rewards_all")
)

IMPERSONATION_PHRASES = unique_items(
    ORIGINAL_IMPERSONATION_PHRASES
    + get_dataset_phrases("impersonation", "impersonation_all")
)


SUSPICIOUS_URL_WORDS = unique_items(
    [
        "verify", "verification", "login", "signin", "sign-in",
        "password", "banking", "secure-login", "account-update",
        "account-verify", "free-prize", "claim-reward",
        "claim-prize", "instant-reward", "gift-card",
        "winner", "lottery", "cashback", "refund",
        "payment-update", "kyc-update", "kyc-verification",
        "upi-payment", "netbanking", "credential",
        "reset-password", "confirm-identity", "security-alert",
        "suspended-account", "unlock-account", "urgent-action",
        "account-validation", "identity-check", "wallet-connect",
        "free-token", "crypto-airdrop", "bonus-claim",
        "prize-claim", "tax-refund", "customs-payment",
        "delivery-fee", "parcel-update", "track-package",
        "job-registration", "instant-loan", "loan-approval",
        "support-login", "customer-care", "account-recovery",
        "payment-confirm", "card-activation", "bank-update",
        "mobile-verification", "sim-update", "secure-payment",
        "government-benefit", "claim-benefit"
    ]
    + [
        word
        for dataset in DATASETS
        for word in flatten_category(dataset.get("url_words", []))
    ]
)


# ==========================================================
# PATTERNS AND SCORING
# ==========================================================

def get_patterns():
    combined = {}

    for dataset in DATASETS:
        patterns = dataset.get("patterns", {})

        if not isinstance(patterns, dict):
            continue

        for group, words in patterns.items():
            if isinstance(words, list):
                combined.setdefault(group, []).extend(words)

    return {
        group: unique_items(words)
        for group, words in combined.items()
    }


PATTERNS = get_patterns()


def get_scoring_weights():
    defaults = {
        "sensitive_phrase": 35,
        "urgency_phrase": 15,
        "reward_phrase": 15,
        "impersonation_phrase": 10,
        "suspicious_url": 20,
        "request_plus_sensitive_pattern": 25,
        "money_plus_urgency_pattern": 15,
        "impersonation_plus_sensitive_pattern": 20,
        "delivery_fee_plus_payment_pattern": 20,
        "max_score": 100,
    }

    for dataset in DATASETS:
        scoring = dataset.get("scoring", {})

        if isinstance(scoring, dict):
            for key, value in scoring.items():
                if key in defaults and isinstance(value, (int, float)):
                    defaults[key] = value

    return defaults


SCORING = get_scoring_weights()


# ==========================================================
# DETECTION HELPERS
# ==========================================================

def normalize_text(value):
    return re.sub(r"\s+", " ", value.lower()).strip()


def find_matches(text, phrases):
    return [phrase for phrase in phrases if phrase in text]


def detect_patterns(message):
    matches = {}

    for group, words in PATTERNS.items():
        found = find_matches(message, words)

        if found:
            matches[group] = found

    return matches


def calculate_risk_score(signals):
    score = 0

    if signals.get("sensitive"):
        score += SCORING["sensitive_phrase"]

    if signals.get("urgency"):
        score += SCORING["urgency_phrase"]

    if signals.get("reward"):
        score += SCORING["reward_phrase"]

    if signals.get("impersonation"):
        score += SCORING["impersonation_phrase"]

    if signals.get("suspicious_url"):
        score += SCORING["suspicious_url"]

    pattern_groups = signals.get("pattern_groups", {})

    if pattern_groups.get("request") and pattern_groups.get("sensitive"):
        score += SCORING["request_plus_sensitive_pattern"]

    if pattern_groups.get("money") and pattern_groups.get("urgency"):
        score += SCORING["money_plus_urgency_pattern"]

    if pattern_groups.get("impersonation") and pattern_groups.get("sensitive"):
        score += SCORING["impersonation_plus_sensitive_pattern"]

    if pattern_groups.get("delivery") and pattern_groups.get("money"):
        score += SCORING["delivery_fee_plus_payment_pattern"]

    return min(int(score), int(SCORING["max_score"]))


def get_risk_level(score):
    if score >= 75:
        return "Very high risk"
    if score >= 50:
        return "High risk"
    if score >= 25:
        return "Moderate risk"
    if score > 0:
        return "Low risk"

    return "No obvious warning signs"


def extract_links(message):
    return re.findall(
        r"(?:https?://|www\.)[^\s<>\"]+",
        message,
        flags=re.IGNORECASE
    )


# ==========================================================
# OFFICIAL BRAND DATABASE
# ==========================================================

OFFICIAL_BRANDS = [
    "SBI", "HDFC", "ICICI", "Axis", "Kotak", "IndusInd",
    "YesBank", "IDFC", "Federal", "Canara", "PNB",
    "BankOfBaroda", "UnionBank", "IndianBank", "BOI",
    "HSBC", "Citi", "StandardChartered", "AmericanExpress",
    "Mastercard", "Visa", "Razorpay", "CRED",
    "PhonePe", "Paytm", "GooglePay", "BHIM", "Mobikwik",
    "Freecharge", "Jupiter", "FiMoney", "Groww",
    "Zerodha", "Upstox", "AngelOne", "PolicyBazaar",
    "Amazon", "Flipkart", "Myntra", "Meesho", "Ajio",
    "Nykaa", "Snapdeal", "Shopsy", "TataCliq",
    "JioMart", "BigBasket", "Blinkit", "Zepto",
    "Swiggy", "Zomato", "DMart", "IKEA",
    "Google", "Microsoft", "Apple", "Samsung", "Dell",
    "HP", "Lenovo", "Asus", "Acer", "Intel", "AMD",
    "Nvidia", "Adobe", "Oracle", "Cisco", "IBM",
    "Wipro", "Infosys", "TCS", "Accenture", "OpenAI",
    "ChatGPT", "GitHub", "LinkedIn", "Zoom", "Dropbox",
    "PayPal", "Cloudflare", "Canva", "Autodesk",
    "Instagram", "Facebook", "WhatsApp", "Telegram",
    "Snapchat", "X", "Twitter", "Pinterest", "Reddit",
    "Discord", "YouTube", "Netflix", "Spotify",
    "Threads", "Twitch",
    "Jio", "Airtel", "Vi", "Vodafone", "Idea",
    "BSNL", "ACT", "Hathway",
    "IRCTC", "MakeMyTrip", "Goibibo", "Cleartrip",
    "Yatra", "RedBus", "Ola", "Uber", "Rapido",
    "AirIndia", "IndiGo", "SpiceJet", "Akasa",
    "Delhivery", "BlueDart", "DTDC", "FedEx",
    "DHL", "Shiprocket",
    "Dominos", "PizzaHut", "McDonalds", "KFC",
    "Starbucks", "Subway", "BurgerKing", "Popeyes",
    "Oyo", "Airbnb", "Marriott", "Booking",
    "UIDAI", "Aadhaar", "DigiLocker", "UMANG",
    "IncomeTax", "GST", "EPFO", "PassportSeva",
    "Parivahan", "NPCI",
    "Disney", "Hotstar", "SonyLIV", "JioCinema",
    "PrimeVideo", "BookMyShow", "Steam", "EpicGames",
    "Reliance", "Tata", "Mahindra",
    "LIC", "IRDAI", "Naukri", "Indeed",
    "Coursera", "Udemy", "Unacademy", "PhysicsWallah"
]


# ==========================================================
# BRAND LOOKALIKE DETECTION
# ==========================================================

def normalize_brand_name(name):
    substitutions = str.maketrans({
        "0": "o",
        "1": "l",
        "I": "l",
        "5": "s",
        "3": "e",
        "4": "a",
        "@": "a"
    })

    return name.lower().translate(substitutions)


def detect_brand_mismatches(message):
    detected = []
    words = re.findall(r"[a-zA-Z0-9@]+", message)

    for word in words:
        if len(word) < 3:
            continue

        for brand in OFFICIAL_BRANDS:
            if word.lower() == brand.lower():
                continue

            normalized_word = normalize_brand_name(word)
            normalized_brand = normalize_brand_name(brand)

            similarity = difflib.SequenceMatcher(
                None,
                normalized_word,
                normalized_brand
            ).ratio()

            if similarity >= 0.80:
                if similarity >= 0.95:
                    priority = "High"
                elif similarity >= 0.85:
                    priority = "Medium"
                else:
                    priority = "Low"

                detected.append({
                    "detected_name": word,
                    "official_brand": brand,
                    "similarity": round(similarity * 100),
                    "priority": priority
                })

    return detected


# ==========================================================
# URL CHECKER
# ==========================================================

def check_url(url):
    warnings = []

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname

        if parsed.scheme not in ("http", "https") or not hostname:
            raise ValueError()

        try:
            ipaddress.ip_address(hostname)
            warnings.append(
                "The website uses an IP address instead of a normal domain."
            )
        except ValueError:
            pass

        if "@" in parsed.netloc:
            warnings.append(
                "The URL contains a potentially misleading @ symbol."
            )

        if "xn--" in hostname.lower():
            warnings.append(
                "The domain contains encoded characters."
            )

        if parsed.scheme == "http":
            warnings.append(
                "The website uses HTTP instead of encrypted HTTPS."
            )

        address = (hostname + parsed.path + parsed.query).lower()

        if any(word in address for word in SUSPICIOUS_URL_WORDS):
            warnings.append(
                "The address contains terms commonly seen in deceptive links."
            )

        if len(hostname) > 60:
            warnings.append(
                "The domain name is unusually long."
            )

        if hostname.count(".") >= 5:
            warnings.append(
                "The website address contains an unusually large number of subdomains."
            )

    except (ValueError, TypeError):
        return None, ["Please enter a valid website address."]

    return url, warnings


# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/")
def home():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)


# ==========================================================
# DASHBOARD STATISTICS API
# ==========================================================

@app.route("/api/dashboard", methods=["GET"])
def dashboard_api():
    return jsonify(get_dashboard_stats())


# ==========================================================
# MESSAGE ANALYSIS API
# ==========================================================

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "Please enter a message."
        }), 400

    message = message.strip()
    lower_message = normalize_text(message)

    warnings = []

    signals = {
        "sensitive": False,
        "urgency": False,
        "reward": False,
        "impersonation": False,
        "suspicious_url": False,
        "pattern_groups": {},
    }

    detected_categories = []

    # Brand mismatch detection.
    brand_mismatches = detect_brand_mismatches(message)

    for mismatch in brand_mismatches:
        warnings.append(
            f"Possible {mismatch['official_brand']} impersonation: "
            f"'{mismatch['detected_name']}' detected "
            f"({mismatch['similarity']}% similarity). "
            f"Warning priority: {mismatch['priority']}."
        )

        if "Possible brand impersonation" not in detected_categories:
            detected_categories.append("Possible brand impersonation")

    if brand_mismatches:
        signals["impersonation"] = True

    # Urgency detection.
    if find_matches(lower_message, URGENT_PHRASES):
        signals["urgency"] = True
        detected_categories.append("Urgency and pressure")
        warnings.append(
            "The message uses urgent or pressure-based language."
        )

    # Sensitive information detection.
    if find_matches(lower_message, SENSITIVE_PHRASES):
        signals["sensitive"] = True
        detected_categories.append("Sensitive information request")
        warnings.append(
            "The message may request sensitive personal or financial information."
        )

    # Reward detection.
    if find_matches(lower_message, REWARD_PHRASES):
        signals["reward"] = True
        detected_categories.append("Money or reward promise")
        warnings.append(
            "The message contains a potentially misleading money or reward promise."
        )

    # Impersonation and delivery detection.
    if find_matches(lower_message, IMPERSONATION_PHRASES):
        signals["impersonation"] = True
        detected_categories.append("Impersonation or delivery")
        warnings.append(
            "The message may involve impersonation, delivery or payment-related deception."
        )

    # Dataset pattern combinations.
    pattern_matches = detect_patterns(lower_message)
    signals["pattern_groups"] = pattern_matches

    if pattern_matches:
        detected_categories.append("Combined suspicious patterns")
        warnings.append(
            "The message contains a combination of wording patterns that may be suspicious."
        )

    # Inspect links.
    links = extract_links(message)

    if links:
        detected_categories.append("Website link")

        for link in links:
            cleaned_link = link.rstrip(".,!?;:)]}")
            _, url_warnings = check_url(cleaned_link)

            if url_warnings and url_warnings[0] != "Please enter a valid website address.":
                signals["suspicious_url"] = True

            for warning in url_warnings:
                if (
                    warning not in warnings
                    and warning != "Please enter a valid website address."
                ):
                    warnings.append(warning)

    # Calculate risk.
    risk_score = calculate_risk_score(signals)
    risk_level = get_risk_level(risk_score)

    if warnings:
        result = (
            f"Potential warning signs detected (risk score: {risk_score}/100):\n• "
            + "\n• ".join(warnings)
        )
    else:
        result = (
            "No obvious warning signs detected in this message. "
            "This does not guarantee that the message is genuine."
        )

    # Save scan statistics without storing the message.
    record_scan("Message", risk_score, risk_level)

    return jsonify({
        "status": "analysed",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "brand_mismatches": brand_mismatches,
        "warnings": warnings,
        "detected_categories": detected_categories,
        "result": result,
        "disclaimer": (
            "Authentix uses text and URL patterns. Its result is an estimate, "
            "not proof that a message is fraudulent or genuine."
        )
    })


# ==========================================================
# URL ANALYSIS API
# ==========================================================

@app.route("/api/analyze-url", methods=["POST"])
def analyze_url():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")

    if not isinstance(url, str) or not url.strip():
        return jsonify({
            "error": "Please enter a website URL."
        }), 400

    checked_url, warnings = check_url(url.strip())

    if checked_url is None:
        return jsonify({
            "error": warnings[0]
        }), 400

    risk_score = min(
        len(warnings) * 25,
        int(SCORING["max_score"])
    )

    risk_level = get_risk_level(risk_score)

    if warnings:
        result = (
            f"Potential warning signs detected (risk score: {risk_score}/100):\n• "
            + "\n• ".join(warnings)
        )
    else:
        result = (
            "No obvious warning signs detected in this URL. "
            "This does not guarantee that the website is safe."
        )

    # Save scan statistics without storing the URL.
    record_scan("Website", risk_score, risk_level)

    return jsonify({
        "url": checked_url,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "warnings": warnings,
        "result": result,
        "disclaimer": (
            "Authentix checks visible URL characteristics only. "
            "It does not verify a website's ownership, reputation or live safety status."
        )
    })


# ==========================================================
# RUN AUTHENTIX
# ==========================================================

if __name__ == "__main__":
    app.run(debug=True)
