import azure.functions as func
import logging
import json
import os
import requests
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Environment Variables
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT")
PROJECT_API_KEY = os.environ.get("PROJECT_API_KEY")
AGENT_ID = os.environ.get("AGENT_ID") # Foundry Agent ID (asst_...)

@app.route(route="CampusCompassAPI")
def CampusCompassAPI(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('WhatsApp Webhook triggered.')

    # 1. Meta Webhook Verification (GET Request)
    if req.method == 'GET':
        mode = req.params.get('hub.mode')
        token = req.params.get('hub.verify_token')
        challenge = req.params.get('hub.challenge')

        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                logging.info('WEBHOOK_VERIFIED')
                return func.HttpResponse(challenge, status_code=200)
            else:
                return func.HttpResponse("Verification token mismatch", status_code=403)
        return func.HttpResponse("Missing parameters", status_code=400)

    # 2. Incoming WhatsApp Message Handler (POST Request)
    elif req.method == 'POST':
        try:
            body = req.get_json()
            logging.info(f"Incoming payload: {json.dumps(body)}")

            # Extract message & sender info from Meta payload
            entry = body.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])

            if messages:
                message = messages[0]
                from_number = message.get('from') # User's WhatsApp number
                
                if message.get('type') == 'text':
                    user_text = message.get('text', {}).get('body', '')
                    
                    # AI Agent Response Generation
                    ai_response = get_agent_response(user_text)
                    
                    # Reply back via WhatsApp API
                    send_whatsapp_message(from_number, ai_response)

            return func.HttpResponse("EVENT_RECEIVED", status_code=200)

        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return func.HttpResponse("Error", status_code=200) # Always return 200 to Meta

def get_agent_response(user_prompt):
    """Azure AI Foundry Agent Call"""
    try:
        # Connect to Azure AI Project
        project_client = AIProjectClient.from_connection_string(
            conn_str=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential()
        )
        
        # Create Thread & Run Agent
        thread = project_client.agents.create_thread()
        project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=user_prompt
        )
        
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=AGENT_ID
        )
        
        if run.status == "completed":
            messages = project_client.agents.list_messages(thread_id=thread.id)
            for msg in messages.data:
                if msg.role == "assistant":
                    return msg.content[0].text.value
                    
        return "Sorry, main abhi aapka jawab nahi dhoond saka."
    except Exception as e:
        logging.error(f"Azure AI Agent Error: {str(e)}")
        # Fallback response
        return "Internal AI processing error. Please try again."

def send_whatsapp_message(recipient, text):
    """Send Message back to WhatsApp User"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"WhatsApp Send Status: {response.status_code}, Response: {response.text}")
