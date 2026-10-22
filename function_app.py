import azure.functions as func
import logging
import json
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ================== CONFIG ==================
VERIFY_TOKEN = "muet123"
WHATSAPP_TOKEN = "EAAXKxT2po3ABSwdUQjnIIVDf5aFHoZCCRJynNqcISim6xukOr91SByBZBAeF0rJAaBASDRDqolJdJBZBdZAmtbLmTR3L2xvUEBNaaXWvjqf3GIAWbWpByoe35AniyE6WDXTh7ec77mcZCrqEDY8Rdo55osYoF2mMccWV2RRabRr3kYPM3QGxmqZCrlivjHxirhkwZDZD"
PHONE_NUMBER_ID = "1458259450693098"
# ============================================

@app.route(route="CampusCompassAPI",auth_level=func.AuthLevel.ANONYMOUS, methods=[func.HttpMethod.GET, func.HttpMethod.POST])
def CampusCompassAPI(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('CampusCompass Triggered')

    # ----- 1. GET - Webhook Verification + Browser View -----
    if req.method == "GET":
        mode = req.params.get('hub.mode')
        token = req.params.get('hub.verify_token')
        challenge = req.params.get('hub.challenge')

        # WhatsApp verification
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logging.info("WEBHOOK_VERIFIED")
            return func.HttpResponse(challenge, status_code=200)

        # Normal browser response with Team Info
        data = {
            "message": "Hello MUET Student! Welcome to CampusCompass",
            "university": "MUET Jamshoro",
            "status": "Running on Azure",
            "project": "CampusCompass - AI Agent for Campus Students",
            "team": [
                {"name": "ASHFAQUE SATHIO", "roll": "25BSAI045"},
                {"name": "SARMAD GABOOL", "roll": "25BSAI038"},
                {"name": "ABDUL AHAD BALOCH", "roll": "25BSAI019"}
            ],
            "department": "Software Engineering, MUET",
            "whatsapp": "Ready"
        }
        return func.HttpResponse(
            json.dumps(data, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    # ----- 2. POST - WhatsApp Message Received -----
    try:
        body = req.get_json()
        logging.info(f"Received: {json.dumps(body)}")

        if not body or 'entry' not in body:
            return func.HttpResponse("OK", status_code=200)

        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']

        if 'messages' in value and len(value['messages']) > 0:
            msg_obj = value['messages'][0]
            from_number = msg_obj['from']
            msg_text = msg_obj.get('text', {}).get('body', 'Hi')

            # BOT REPLY WITH TEAM NAME
            bot_reply = (
                f"You said: '{msg_text}'\n\n"
                f"🎓 CampusCompass - MUET AI Assistant is here!\n\n"
                f"👨‍💻 Developed By:\n"
                f"1. ASHFAQUE SATHIO - 25BSAI045\n"
                f"2. SARMAD GABOOL - 25BSAI038\n"
                f"3. ABDUL AHAD BALOCH - 25BSAI019\n\n"
                f"Dept: Software, MUET Jamshoro"
            )

            # Send back to WhatsApp
            url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": bot_reply}
            }

            resp = requests.post(url, headers=headers, json=payload)
            logging.info(f"WhatsApp API Response: {resp.text}")

        return func.HttpResponse("EVENT_RECEIVED", status_code=200)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse("OK", status_code=200)
