"""
Backend FastAPI pour l'agent AI de réparation de téléphones.

Lancer avec:
    uvicorn main:app --reload --port 8000

Nécessite la variable d'environnement ANTHROPIC_API_KEY
(obtenue sur https://console.anthropic.com).
"""

import os

import anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database as db
from tools import TOOLS, execute_tool

app = FastAPI(title="Agent AI - Réparation Téléphones")

# Autoriser les requêtes depuis le front (à restreindre à ton domaine en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Tu es l'assistant virtuel d'un magasin de réparation de téléphones.

Ton rôle:
- Aider les clients à créer un ticket (reçu) de réparation pour leur téléphone.
- Aider les clients à suivre le statut de leur réparation.
- Répondre aux questions générales sur les services (délais moyens, garantie de 30 jours sur les réparations, moyens de paiement: espèces ou carte).

Règles importantes:
- Avant de créer un ticket, confirme toujours avec le client: son nom, son numéro de téléphone, le modèle du téléphone, et le problème rencontré. Ne crée jamais un ticket avec des informations manquantes ou devinées.
- Une fois le ticket créé, donne toujours au client son numéro de ticket (ticket_id) clairement, et dis-lui de le garder pour suivre sa réparation.
- Si le client ne connaît pas son numéro de ticket, utilise son numéro de téléphone pour retrouver ses tickets.
- Réponds toujours dans la langue utilisée par le client (français, arabe tunisien, ou un mélange des deux) sur un ton amical et professionnel.
- Reste concis, comme dans une vraie conversation de support client.
"""


class ChatRequest(BaseModel):
    message: str
    # Historique de la conversation envoyé par le front à chaque appel
    # (le backend est "stateless" - il ne garde pas de mémoire entre les requêtes)
    history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str
    history: list[dict]


class QuickTicketRequest(BaseModel):
    client_name: str
    marque: str
    modele: str = ""
    panne: str
    prix_estime: str = ""


class QuickTicketResponse(BaseModel):
    ticket_id: str
    client_name: str
    marque: str
    modele: str
    panne: str
    prix_estime: str
    status_label: str


@app.on_event("startup")
def on_startup():
    db.init_db()


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    messages = req.history + [{"role": "user", "content": req.message}]

    # Boucle agentique: on appelle Claude, et tant qu'il demande des tools,
    # on les exécute et on lui renvoie le résultat, jusqu'à avoir une réponse finale.
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Réponse finale texte
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return ChatResponse(reply=final_text, history=messages)

        # Le modèle veut utiliser un ou plusieurs tools
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )

        messages.append({"role": "user", "content": tool_results})


@app.post("/quick-ticket", response_model=QuickTicketResponse)
def quick_ticket(req: QuickTicketRequest):
    """
    Création rapide d'un ticket depuis le formulaire simplifié du site
    (nom + marque + modèle + panne, sans passer par l'agent conversationnel).
    """
    phone_model = f"{req.marque} {req.modele}".strip()
    ticket = db.create_ticket(
        client_name=req.client_name,
        phone_model=phone_model,
        issue_description=req.panne,
    )
    return QuickTicketResponse(
        ticket_id=ticket["ticket_id"],
        client_name=ticket["client_name"],
        marque=req.marque,
        modele=req.modele,
        panne=ticket["issue_description"],
        prix_estime=req.prix_estime,
        status_label=ticket["status_label"],
    )


@app.get("/health")
def health():
    return {"status": "ok"}
