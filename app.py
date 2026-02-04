from flask import Flask, request, redirect, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import string
import random
from datetime import datetime

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<URL {self.original_url} -> {self.short_code}>'

# Create tables
with app.app_context():
    db.create_all()

# Helper function to generate short code
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Home page with form
@app.route('/')
def home():
    return render_template('index.html')

# API to shorten URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    original_url = data['url']
    
    # Generate unique short code
    short_code = generate_short_code()
    while URL.query.filter_by(short_code=short_code).first():
        short_code = generate_short_code()
    
    # Save to database
    new_url = URL(original_url=original_url, short_code=short_code)
    db.session.add(new_url)
    db.session.commit()
    
    # Return shortened URL
    short_url = f"{request.host_url}{short_code}"
    return jsonify({
        'original_url': original_url,
        'short_url': short_url,
        'short_code': short_code
    })

# Redirect to original URL
@app.route('/<short_code>')
def redirect_to_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    
    if url_entry:
        return redirect(url_entry.original_url)
    else:
        return jsonify({'error': 'URL not found'}), 404

# Get all URLs (for testing)
@app.route('/urls')
def get_all_urls():
    urls = URL.query.all()
    result = []
    for url in urls:
        result.append({
            'id': url.id,
            'original_url': url.original_url,
            'short_code': url.short_code,
            'short_url': f"{request.host_url}{url.short_code}",
            'created_at': url.created_at
        })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)