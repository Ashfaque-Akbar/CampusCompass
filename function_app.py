import azure.functions as func
import logging
import json
import os
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

VERIFY_TOKEN = "muet123"

@app.route(route="CampusCompassAPI", auth_level=func.AuthLevel.ANONYMOUS, methods=[func.HttpMethod.GET, func.HttpMethod.POST])
def CampusCompassAPI(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('CampusCompass Triggered')
    if req.method == "GET":
        mode = req.params.get('hub.mode')
        token = req.params.get('hub.verify_token')
        challenge = req.params.get('hub.challenge')
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return func.HttpResponse(challenge, status_code=200)
        else:
            return func.HttpResponse("Verification Failed", status_code=403)
    if req.method == "POST":
        try:
            data = req.get_json()
            logging.info(f"Received data: {json.dumps(data)}")
            if data.get("object") == "whatsapp_business_account":
                for entry in data.get("entry", []):
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        messages = value.get("messages", [])
                        if messages:
                            for msg in messages:
                                from_number = msg.get("from")
                                msg_body = msg.get("text", {}).get("body", "")
                                logging.info(f"Message from {from_number}: {msg_body}")
                                send_whatsapp_reply(from_number, f"Hello MUET! You said: {msg_body} - Bot is Working!")
            return func.HttpResponse("EVENT_RECEIVED", status_code=200)
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return func.HttpResponse(f"Error: {str(e)}", status_code=200)

def send_whatsapp_reply(to_number, message_text):
    try:
        token = os.environ.get("WHATSAPP_TOKEN")
        phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp","to": to_number,"type": "text","text": {"body": message_text}}
        response = requests.post(url, headers=headers, json=payload)
        logging.info(f"WhatsApp API Response: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Failed to send reply: {e}")
