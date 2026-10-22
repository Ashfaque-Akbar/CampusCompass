import azure.functions as func
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="CampusCompassAPI", methods=["GET", "POST"])
def CampusCompassAPI(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get('name', 'MUET Student')
    query = req.params.get('query', '')
    try:
        import json as js
        body = req.get_json()
        if body:
            name = body.get('name', name)
            query = body.get('query', query)
    except:
        pass
    response = {
        "message": f"Hello {name}! Welcome to CampusCompass",
        "university": "MUET - Making AI Agent for Campus students",
        "bot_reply": f"You asked: '{query}'. I am your Campus Assistant.",
        "status": "Running on Azure"
    }
    return func.HttpResponse(json.dumps(response, indent=2), mimetype="application/json", status_code=200)
