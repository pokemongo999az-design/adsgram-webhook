import os, hmac, hashlib, logging, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# === Config via variables d’environnement ===
ADSGRAM_SECRET = os.environ.get("ADSGRAM_SECRET", "").encode()  # <— à mettre sur Render
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")   # optionnel: pour prévenir l’utilisateur
# (facultatif) URL de l’API Telegram
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else None

# Petit ping pour tester le déploiement
@app.get("/ping")
def ping():
    return "pong", 200

def verify_signature(raw_body: bytes, signature: str) -> bool:
    """
    Vérifie la signature HMAC envoyée par AdsGram.
    On suppose l’en-tête: X-Adsgram-Signature avec hex digest sha256.
    """
    if not ADSGRAM_SECRET:
        app.logger.error("ADSGRAM_SECRET manquant !")
        return False
    expected = hmac.new(ADSGRAM_SECRET, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")

def notify_user(chat_id: int, text: str):
    """Optionnel: envoie un message Telegram à l’utilisateur (si TELEGRAM_BOT_TOKEN est défini)."""
    if not TG_API or not chat_id:
        return
    try:
        requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as e:
        app.logger.warning(f"Impossible d’envoyer le message Telegram: {e}")

@app.post("/adsgram/callback")
def adsgram_callback():
    """
    Endpoint appelé par AdsGram après une pub vue.
    Attendus (exemple): userId, reward, adId, meta (où tu peux mettre ton chat_id).
    La signature est dans l’en-tête X-Adsgram-Signature.
    """
    signature = request.headers.get("X-Adsgram-Signature", "")
    raw = request.get_data()  # corps brut pour HMAC
    if not verify_signature(raw, signature):
        return jsonify({"error": "invalid signature"}), 403

    data = request.get_json(silent=True) or {}
    user_id = data.get("userId")               # identifiant côté AdsGram
    reward = float(data.get("reward", 0))
    ad_id  = data.get("adId")
    meta   = data.get("meta")  # champ libre: tu peux y passer le chat_id Telegram, etc.

    app.logger.info(f"✅ Callback AdsGram OK | userId={user_id} reward={reward} adId={ad_id} meta={meta}")

    # 👉 Ici: crédite TON dans ta base (Postgres conseillé sur Render).
    # Ex: update_balance(user_id, reward)

    # Option (facile): si tu as généré la pub en incluant chat_id dans meta, tu peux prévenir l’utilisateur :
    chat_id = None
    if isinstance(meta, dict):
        chat_id = meta.get("chat_id")
    if chat_id:
        notify_user(chat_id, f"👏 Pub validée ! Récompense : +{reward:.2f} TON")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # En local: Flask sur le port 5000 (Render fournira $PORT en prod)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
