"""
Couche base de données pour l'agent AI de réparation de téléphones.
Utilise SQLite (fichier local) - facile à démarrer pour un PFE.
Si tu utilises déjà MySQL/PostgreSQL, remplace juste les fonctions
ci-dessous par tes propres requêtes (garde les mêmes noms/signatures
et le reste du code - tools.py, main.py - n'aura pas besoin de changer).
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "repairs.db"

# Statuts possibles d'un ticket de réparation
VALID_STATUSES = ["recu", "diagnostic", "en_reparation", "pret", "livre"]

STATUS_LABELS = {
    "recu": "Reçu - en attente de diagnostic",
    "diagnostic": "En cours de diagnostic",
    "en_reparation": "En cours de réparation",
    "pret": "Prêt - à récupérer en magasin",
    "livre": "Livré au client",
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée la table des tickets si elle n'existe pas déjà."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            phone_model TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'recu',
            estimated_price TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def create_ticket(client_name: str, phone_model: str, issue_description: str, phone_number: str = "") -> dict:
    """Crée un nouveau ticket de réparation et retourne ses infos."""
    ticket_id = "TCK-" + uuid.uuid4().hex[:8].upper()
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO tickets
            (ticket_id, client_name, phone_number, phone_model, issue_description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'recu', ?, ?)
        """,
        (ticket_id, client_name, phone_number, phone_model, issue_description, now, now),
    )
    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "client_name": client_name,
        "phone_number": phone_number,
        "phone_model": phone_model,
        "issue_description": issue_description,
        "status": "recu",
        "status_label": STATUS_LABELS["recu"],
    }


def get_ticket_by_id(ticket_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    data = dict(row)
    data["status_label"] = STATUS_LABELS.get(data["status"], data["status"])
    return data


def get_tickets_by_phone(phone_number: str) -> list[dict]:
    """Utile quand le client ne se rappelle plus son numéro de ticket."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tickets WHERE phone_number = ? ORDER BY created_at DESC", (phone_number,)
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        data = dict(row)
        data["status_label"] = STATUS_LABELS.get(data["status"], data["status"])
        results.append(data)
    return results


def update_ticket_status(ticket_id: str, new_status: str, estimated_price: str | None = None) -> dict | None:
    """Pour usage côté admin (pas exposé à l'agent AI côté client)."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Statut invalide: {new_status}")

    conn = get_connection()
    now = datetime.utcnow().isoformat()
    if estimated_price is not None:
        conn.execute(
            "UPDATE tickets SET status = ?, estimated_price = ?, updated_at = ? WHERE ticket_id = ?",
            (new_status, estimated_price, now, ticket_id),
        )
    else:
        conn.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?",
            (new_status, now, ticket_id),
        )
    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_id)
