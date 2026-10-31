
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlsplit
import ipaddress
import re

app = Flask(__name__)


# ==========================================
# AUTHENTIX DETECTION DATASET
# ==========================================

# 1. URGENCY AND PRESSURE PHRASES
URGENT_PHRASES = [
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
    "claim before midnight", "respond within minutes" , "immediately"
]


# 2. SENSITIVE INFORMATION REQUESTS
SENSITIVE_PHRASES = [
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


# 3. MONEY, PRIZE AND REWARD SCAMS
REWARD_PHRASES = [
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


# 4. IMPERSONATION AND DELIVERY SCAMS
IMPERSONATION_PHRASES = [
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


# 5. SUSPICIOUS WEBSITE TERMS
SUSPICIOUS_URL_WORDS = [
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


# ==========================================
# HELPER: CHECK SUSPICIOUS URL SIGNS
# ==========================================

def check_url(url):
    warnings = []

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname

        if parsed.scheme not in ("http", "https") or not hostname:
            raise ValueError()

        # IP address instead of domain
        try:
            ipaddress.ip_address(hostname)
            warnings.append(
                "The website uses an IP address instead of a normal domain."
            )
        except ValueError:
            pass

        # Misleading @ symbol
        if "@" in parsed.netloc:
            warnings.append(
                "The URL contains a potentially misleading @ symbol."
            )

        # Encoded domain
        if "xn--" in hostname.lower():
            warnings.append(
                "The domain contains encoded characters."
            )

        # Unencrypted connection
        if parsed.scheme == "http":
            warnings.append(
                "The website uses HTTP instead of encrypted HTTPS."
            )

        # Suspicious words
        address = (hostname + parsed.path + parsed.query).lower()

        if any(word in address for word in SUSPICIOUS_URL_WORDS):
            warnings.append(
                "The address contains terms commonly seen in deceptive links."
            )

        # Unusually long domain
        if len(hostname) > 60:
            warnings.append(
                "The domain name is unusually long."
            )

        # Many subdomains can sometimes be misleading
        if hostname.count(".") >= 5:
            warnings.append(
                "The website address contains an unusually large number of subdomains."
            )

    except ValueError:
        return None, ["Please enter a valid website address."]

    return url, warnings


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# MESSAGE ANALYSIS API
# ==========================================

@app.route("/api/analyze", methods=["POST"])
def analyze():

    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "Please enter a message."
        }), 400

    message = message.strip()
    lower_message = message.lower()

    # Normalize repeated spaces
    lower_message = re.sub(r"\s+", " ", lower_message)

    warnings = []

    # Urgency detection
    if any(phrase in lower_message for phrase in URGENT_PHRASES):
        warnings.append(
            "The message uses urgent or pressure-based language."
        )

    # Sensitive information detection
    if any(phrase in lower_message for phrase in SENSITIVE_PHRASES):
        warnings.append(
            "The message may request sensitive personal or financial information."
        )

    # Reward and money detection
    if any(phrase in lower_message for phrase in REWARD_PHRASES):
        warnings.append(
            "The message contains a potentially misleading money or reward promise."
        )

    # Impersonation and delivery detection
    if any(phrase in lower_message for phrase in IMPERSONATION_PHRASES):
        warnings.append(
            "The message may involve impersonation, delivery or payment-related deception."
        )

    # URL detection
    links = re.findall(
        r"(?:https?://|www\.)\S+",
        message,
        flags=re.IGNORECASE
    )

    if links:
        warnings.append(
            "The message contains a website link. Check the address carefully before visiting it."
        )

    # Final result
    if warnings:
        risk_level = "Potential warning signs"
        result = (
            "Potential warning signs detected:\n• "
            + "\n• ".join(warnings)
        )
    else:
        risk_level = "No obvious warning signs"
        result = (
            "No obvious warning signs detected in this message. "
            "This does not guarantee that the message is genuine."
        )

    return jsonify({
        "status": "analysed",
        "risk_level": risk_level,
        "warnings": warnings,
        "result": result
    })


# ==========================================
# URL ANALYSIS API
# ==========================================

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

    if warnings:
        risk_level = "Potential warning signs"
        result = (
            "Potential warning signs detected:\n• "
            + "\n• ".join(warnings)
        )
    else:
        risk_level = "No obvious warning signs"
        result = (
            "No obvious warning signs detected in this URL. "
            "This does not guarantee that the website is safe."
        )

    return jsonify({
        "url": checked_url,
        "risk_level": risk_level,
        "warnings": warnings,
        "result": result
    })


# ==========================================
# RUN AUTHENTIX
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
