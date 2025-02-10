from decimal import Decimal
import logging
from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)

# Thông tin Telegram bot
TELEGRAM_BOT_TOKEN = "8130296940:AAHYKRkCWdQHmr0NIquzO-3pGVD_JMlMPeI"
TELEGRAM_CHAT_ID = "5437744704"

HELIUS_API_KEY = '084508df-ed6c-4a57-bcc6-9c7958296b3e'
HELIUS_BASE_URL = 'https://api.helius.xyz/v0'
HOOK_ID = 'a2af8ef7-5fa9-4425-94b7-413cc3ab179c'


def send_telegram_message(message):
    """Gửi tin nhắn đến Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

@app.before_request
def log_request_info():
    """Ghi lại thông tin của yêu cầu trước khi xử lý"""
    app.logger.debug("Headers: %s", request.headers)
    app.logger.debug("Body: %s", request.get_data())

def get_webhook_by_id(webhook_id):
    """Lấy thông tin chi tiết về một webhook cụ thể."""
    url = f"{HELIUS_BASE_URL}/webhooks/{webhook_id}?api-key={HELIUS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve webhook: {response.status_code}")
        return None

def convert_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/solana-webhook', methods=['POST'])
def solana_webhook():
    """Nhận dữ liệu từ webhook của Helius"""
    data = request.json
    if not data:
        return jsonify({"message": "Invalid data"}), 400

    webhookById = get_webhook_by_id(HOOK_ID)
    if not webhookById:
        return jsonify({"message": "Invalid webhookById"}), 400

    listAccountConfig = webhookById.get("accountAddresses")
    if not webhookById:
        return jsonify({"message": "Invalid listAccountConfig"}), 400

    for txn in data:
        tx_hash = txn.get("signature", "N/A")
        tx_time = convert_timestamp(txn.get("timestamp", 0))
    
    # Kiểm tra và xử lý các giao dịch nativeTransfers
    if "nativeTransfers" in txn:
        for transfer in txn["nativeTransfers"]:
            from_account = transfer.get("fromUserAccount", "Unknown")
            to_account = transfer.get("toUserAccount", "Unknown")
            amount = transfer.get("amount", 0) / 1e9  # Chuyển đổi từ lamports sang SOL
            if amount >= Decimal('0.1'):
                formatted_amount = "{:.9f}".format(amount).rstrip('0').rstrip('.')
                # Kiểm tra nếu from_account hoặc to_account nằm trong danh sách quan tâm
                if from_account in listAccountConfig:
                    message = (
                        f"🚀 Có giao dịch mua token từ ví đã theo dõi!\n"
                        f"🔄 Ví đang follow: {from_account}\n"
                        f"🔹 Mã giao dịch: {tx_hash}\n"
                        f"💰 Số tiền: {formatted_amount} SOL\n"
                        f"⏰ Thời gian: {tx_time}\n"
                        f"🔄 Từ: {from_account}\n"
                        f"➡️ Đến: {to_account}"
                    )
                if to_account in listAccountConfig:
                    message = (
                        f"🚀 Có giao dịch chuyển SOL đến ví đã theo dõi!\n"
                        f"🔹 Ví follow: {to_account}\n"
                        f"🔹 Tx Hash: {tx_hash}\n"
                        f"💰 Số tiền: {formatted_amount} SOL\n"
                        f"⏰ Thời gian: {tx_time}\n"
                        f"🔄 Từ: {from_account}\n"
                        f"➡️ Đến: {to_account}"
                    )
                if from_account in listAccountConfig or to_account in listAccountConfig:
                    send_telegram_message(message)

    return jsonify({"message": "Đã nhận giao dịch và gửi message Telegram thành công"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)