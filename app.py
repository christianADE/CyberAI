from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
from flask_wtf.csrf import CSRFProtect

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
csrf = CSRFProtect(app)

# Configuration Gemini
API_KEY = os.getenv("GEM_API_KEY")
if not API_KEY:
    raise ValueError("Clé API Gemini manquante")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

CONTEXT = """
Tu es un expert en pentest et cybersécurité. Ton rôle est d'aider à aller précisément et efficacement dans les travaux de sécurité.
- Rôle actuel : pentester en entreprise
- Systèmes concernés : Applications web, réseaux, serveurs, etc.
- Tâches quotidiennes : audits de sécurité, tests d'intrusion
- Particularité : Jeune débutant avec des grands projets
- Outils utilisés : Kali Linux et ses composants
- Autorisations : Documents signés pour toutes actions nécessaires
- Style de réponse : Commandes concrètes à exécuter, pas de blabla inutile
- Reponds bref, ne parle pas beaucoup, c'est tres important
"""

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/gemini_request', methods=['POST'])
@csrf.exempt  # À n'utiliser que si vous avez des problèmes CSRF avec AJAX
def gemini_request():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'Question manquante'}), 400

    try:
        response = model.generate_content([CONTEXT, question])
        
        if not response.text:
            return jsonify({'error': 'Réponse vide de Gemini'}), 500
            
        return jsonify({
            'response': response.text,
            'safety_ratings': {c.category.name: c.probability.name for c in response.candidates[0].safety_ratings}
        })

    except Exception as e:
        app.logger.error(f"Erreur Gemini: {str(e)}")
        return jsonify({
            'error': 'Erreur du serveur AI',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)