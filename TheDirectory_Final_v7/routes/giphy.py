from flask import Blueprint, request, current_app, jsonify
import requests
giphy_bp = Blueprint('giphy', __name__)
@giphy_bp.route('/giphy_search')
def giphy_search():
    q = request.args.get('q','').strip()
    if not q: return jsonify({'data':[]})
    key = current_app.config.get('GIPHY_API_KEY') or ''
    if not key: return jsonify({'data':[]})
    r = requests.get('https://api.giphy.com/v1/gifs/search', params={'api_key': key, 'q': q, 'limit': 12, 'rating': 'pg-13'})
    return jsonify(r.json())
