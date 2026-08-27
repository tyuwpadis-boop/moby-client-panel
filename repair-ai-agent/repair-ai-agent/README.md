# Agent AI - Site de réparation de téléphones

Prototype fonctionnel pour ton PFE : un agent IA (Claude + function calling)
intégré dans ton site, capable de créer des tickets de réparation et de
suivre leur statut.

## Structure du projet

```
repair-ai-agent/
  backend/
    main.py           -> API FastAPI, endpoint /chat, boucle agentique
    tools.py          -> définition des tools + dispatcher
    database.py       -> couche base de données (SQLite)
    requirements.txt
  widget/
    chat-widget.html  -> widget de chat à copier dans ton site
```

## 1. Installer et lancer le backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # sous Windows: venv\Scripts\activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="ta_clé_api"   # obtenue sur console.anthropic.com
uvicorn main:app --reload --port 8000
```

Vérifie que ça marche : ouvre `http://localhost:8000/health` → tu dois voir `{"status":"ok"}`.

## 2. Intégrer le widget dans ton site

Copie tout le contenu de `widget/chat-widget.html` juste avant la balise
`</body>` de tes pages HTML (ou dans ton composant layout si tu utilises
un framework comme React/Vue).

Si ton backend n'est pas sur `localhost:8000`, change la ligne suivante
dans le widget :
```js
const BACKEND_URL = "http://localhost:8000/chat";
```

## 3. Comment ça marche (pour ta soutenance)

1. Le client tape un message dans le widget → envoyé à `/chat`.
2. Le backend transmet le message à Claude avec la liste des **tools**
   disponibles (`create_repair_ticket`, `get_ticket_status`, `find_tickets_by_phone`).
3. Claude décide **lui-même** s'il a besoin d'un tool pour répondre
   (par exemple, s'il a assez d'infos pour créer un ticket).
4. Si oui, le backend exécute la vraie fonction Python sur ta base de
   données, et renvoie le résultat à Claude.
5. Claude formule la réponse finale en langage naturel pour le client.

C'est ce mécanisme (le modèle qui choisit d'appeler des fonctions) qui
s'appelle **function calling / tool use**, et c'est ce qui transforme un
simple chatbot en "agent" capable d'agir sur un vrai système.

## 4. Adapter à ta propre base de données

Le prototype utilise SQLite (fichier `repairs.db`, créé automatiquement)
pour que ce soit simple à démarrer. Si ton site utilise déjà MySQL ou
PostgreSQL :

- Remplace uniquement les fonctions dans `database.py`
  (`create_ticket`, `get_ticket_by_id`, `get_tickets_by_phone`) par tes
  propres requêtes SQL vers ta vraie base.
- Garde les mêmes noms de fonctions et les mêmes clés dans les
  dictionnaires retournés : `tools.py` et `main.py` n'auront besoin
  d'aucune modification.

## 5. Pistes pour aller plus loin (bonus PFE)

- **RAG pour la FAQ** : si tu as beaucoup de questions/politiques
  (garantie, prix indicatifs, délais par type de panne), ajoute une
  petite base vectorielle (ChromaDB) et un tool `search_faq` pour que
  l'agent réponde avec des infos exactes plutôt que générées.
- **Authentification** : ajouter une vérification (ex: dernier 4
  chiffres du numéro) avant de révéler le statut d'un ticket.
- **Notifications** : ajouter un tool qui envoie un SMS/email au
  client quand le statut passe à "pret".
- **Dashboard admin** : une petite interface pour que l'équipe mette à
  jour le statut des tickets (`update_ticket_status` existe déjà dans
  `database.py`).
- **Déploiement** : héberger le backend sur Render/Railway/VPS, et
  utiliser HTTPS avant la mise en prod.
