"""
Définition des "tools" (function calling) que Claude peut utiliser,
et le dispatcher qui exécute la vraie fonction Python quand Claude
décide d'appeler un tool.
"""

import database as db

# --- Schéma des tools envoyé à l'API Claude ---------------------------------

TOOLS = [
    {
        "name": "create_repair_ticket",
        "description": (
            "Crée un nouveau ticket (reçu) de réparation pour un téléphone. "
            "À utiliser seulement après avoir confirmé avec le client son nom, "
            "son numéro de téléphone, le modèle du téléphone à réparer et le "
            "problème rencontré."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Nom complet du client"},
                "phone_number": {"type": "string", "description": "Numéro de téléphone du client (pour le contacter)"},
                "phone_model": {"type": "string", "description": "Modèle du téléphone à réparer, ex: iPhone 13, Samsung A54"},
                "issue_description": {"type": "string", "description": "Description du problème, ex: écran cassé, batterie qui ne charge pas"},
            },
            "required": ["client_name", "phone_number", "phone_model", "issue_description"],
        },
    },
    {
        "name": "get_ticket_status",
        "description": "Récupère le statut d'un ticket de réparation à partir de son identifiant (ex: TCK-A1B2C3D4).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "Identifiant du ticket, ex: TCK-A1B2C3D4"},
            },
            "required": ["ticket_id"],
        },
    },
    {
        "name": "find_tickets_by_phone",
        "description": (
            "Recherche les tickets de réparation d'un client à partir de son numéro "
            "de téléphone, utile quand le client ne se souvient plus de son numéro de ticket."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "description": "Numéro de téléphone du client"},
            },
            "required": ["phone_number"],
        },
    },
]


# --- Dispatcher --------------------------------------------------------------

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Exécute la vraie fonction Python correspondant au tool demandé par Claude."""

    if tool_name == "create_repair_ticket":
        return db.create_ticket(
            client_name=tool_input["client_name"],
            phone_number=tool_input["phone_number"],
            phone_model=tool_input["phone_model"],
            issue_description=tool_input["issue_description"],
        )

    if tool_name == "get_ticket_status":
        ticket = db.get_ticket_by_id(tool_input["ticket_id"])
        if ticket is None:
            return {"error": "Aucun ticket trouvé avec cet identifiant."}
        return ticket

    if tool_name == "find_tickets_by_phone":
        tickets = db.get_tickets_by_phone(tool_input["phone_number"])
        if not tickets:
            return {"error": "Aucun ticket trouvé pour ce numéro de téléphone."}
        return {"tickets": tickets}

    return {"error": f"Tool inconnu: {tool_name}"}
