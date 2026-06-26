# FICHIER UNIQUE : app.py
# INSTALLATION : pip install flask flask-sqlalchemy flask-login flask-mail

from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, static_folder='logos', static_url_path='/logos')
app.config['SECRET_KEY'] = 'aqua_super_secret_key_2026_xyz_123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cheats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration email (remplacez par vos vrais identifiants Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votre_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe_app'
app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com'

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ===== MODÈLES =====
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_owner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Cheat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    download_link = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cheat_id = db.Column(db.Integer, db.ForeignKey('cheat.id'), nullable=False)
    buyer_email = db.Column(db.String(120), nullable=False)
    paypal_transaction_id = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')  # pending, paid, delivered
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    cheat = db.relationship('Cheat', backref='purchases')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== HTML TEMPLATES =====
HTML_BASE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aqua Cheats - Tortank Store</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { 
    font-family: 'Rajdhani', 'Segoe UI', sans-serif; 
    background: #0a0e1a; 
    min-height:100vh; 
    color:white; 
    overflow-x:hidden; 
    position:relative;
}
body::before {
    content: "";
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60vw;
    height: 60vw;
    background: url('https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/9.png') center/contain no-repeat;
    opacity: 0.04;
    pointer-events: none;
    z-index: 0;
    animation: floatTortank 6s ease-in-out infinite;
}
@keyframes floatTortank {
    0%, 100% { transform: translate(-50%, -50%) scale(1); }
    50% { transform: translate(-50%, -52%) scale(1.03); }
}
* { position:relative; z-index:1; }
nav { 
    background: rgba(10,14,26,0.95); 
    padding:18px 0; 
    border-bottom:2px solid rgba(0,180,255,0.2); 
    box-shadow:0 0 60px rgba(0,150,255,0.05); 
    position:sticky; 
    top:0; 
    z-index:999; 
    backdrop-filter:blur(20px);
}
.container { max-width:1200px; margin:0 auto; padding:0 20px; }
.nav-content { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px; }
.brand { 
    display:flex; 
    align-items:center; 
    gap:12px; 
    font-family: 'Orbitron', sans-serif;
    font-size:22px; 
    font-weight:900; 
    background: linear-gradient(135deg, #00b4ff, #0066ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: none;
    letter-spacing:1px;
}
.brand img { 
    width:40px; 
    animation: float 4s ease-in-out infinite;
    -webkit-text-fill-color: initial;
}
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
.nav-links { 
    display:flex; 
    gap:0; 
    flex-wrap:wrap; 
    list-style:none; 
    border:1px solid rgba(0,180,255,0.15); 
    border-radius:50px; 
    overflow:hidden; 
    background:rgba(0,20,50,0.5);
    backdrop-filter:blur(10px);
}
.nav-links li { display:flex; align-items:center; }
.nav-links li:not(:last-child) { border-right:1px solid rgba(0,180,255,0.1); }
.nav-links a { 
    color:rgba(255,255,255,0.8); 
    text-decoration:none; 
    padding:10px 22px; 
    transition:0.3s; 
    font-size:14px; 
    font-weight:600;
    background:transparent; 
    letter-spacing:0.5px;
}
.nav-links a:hover { 
    background:rgba(0,180,255,0.1); 
    color:#00b4ff;
    box-shadow:inset 0 0 30px rgba(0,180,255,0.05);
}
.hero { 
    text-align:center; 
    padding:80px 20px 60px; 
    position:relative;
}
.hero::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,180,255,0.3), transparent);
}
.hero h1 { 
    font-family: 'Orbitron', sans-serif;
    font-size:56px; 
    font-weight:900;
    background: linear-gradient(135deg, #00b4ff, #0088ff, #0066ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom:15px;
    letter-spacing:2px;
}
.hero p { 
    font-size:20px; 
    color:rgba(255,255,255,0.6);
    font-weight:300;
    letter-spacing:2px;
}
.hero .subtitle {
    font-size:14px;
    color:rgba(0,180,255,0.4);
    letter-spacing:4px;
    text-transform:uppercase;
    margin-top:10px;
}
.categories-grid { 
    display:grid; 
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); 
    gap:20px; 
    padding:40px 0 20px; 
}
.category-card { 
    background:rgba(10,14,26,0.8); 
    backdrop-filter:blur(10px); 
    border-radius:16px; 
    padding:35px 20px; 
    text-align:center; 
    border:1px solid rgba(0,180,255,0.08); 
    transition:0.4s ease; 
    cursor:pointer;
    position:relative;
    overflow:hidden;
}
.category-card::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at center, rgba(0,180,255,0.03), transparent 70%);
    opacity: 0;
    transition:0.6s;
}
.category-card:hover::before { opacity:1; }
.category-card:hover { 
    transform:translateY(-8px); 
    border-color:rgba(0,180,255,0.3); 
    box-shadow:0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(0,180,255,0.05);
}
.category-card a { color:white; text-decoration:none; position:relative; z-index:1; }
.category-card .game-logo { 
    width:80px; 
    height:80px; 
    object-fit:contain; 
    display:block; 
    margin:0 auto 15px;
    filter: drop-shadow(0 0 20px rgba(0,180,255,0.1));
    transition:0.3s;
    border-radius:12px;
}
.category-card:hover .game-logo {
    filter: drop-shadow(0 0 40px rgba(0,180,255,0.3));
    transform:scale(1.05);
}
.category-card h2 { 
    font-size:20px; 
    font-weight:700;
    letter-spacing:1px;
    color:rgba(255,255,255,0.9);
}
.category-card .game-tag {
    display:inline-block;
    margin-top:10px;
    padding:4px 16px;
    border-radius:20px;
    font-size:11px;
    font-weight:600;
    letter-spacing:1px;
    background:rgba(0,180,255,0.1);
    color:rgba(0,180,255,0.6);
    border:1px solid rgba(0,180,255,0.05);
}
.auth-form { 
    max-width:420px; 
    margin:60px auto; 
    background:rgba(10,14,26,0.9); 
    backdrop-filter:blur(20px); 
    padding:50px 40px; 
    border-radius:20px; 
    border:1px solid rgba(0,180,255,0.08); 
    box-shadow:0 30px 80px rgba(0,0,0,0.6);
}
.auth-form h2 { 
    font-family: 'Orbitron', sans-serif;
    text-align:center; 
    margin-bottom:35px; 
    font-size:24px;
    font-weight:700;
    background: linear-gradient(135deg, #00b4ff, #0088ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing:2px;
}
.form-group { margin-bottom:22px; }
.form-group label { 
    display:block; 
    margin-bottom:6px; 
    font-weight:600; 
    color:rgba(255,255,255,0.5);
    font-size:13px;
    letter-spacing:1px;
    text-transform:uppercase;
}
.form-group input, .form-group select, .form-group textarea { 
    width:100%; 
    padding:14px 18px; 
    border-radius:12px; 
    border:1px solid rgba(0,180,255,0.08); 
    background:rgba(0,0,0,0.4); 
    color:white; 
    font-size:16px; 
    font-family:'Rajdhani',sans-serif;
    transition:0.3s;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { 
    outline:none; 
    border-color:rgba(0,180,255,0.3); 
    box-shadow:0 0 30px rgba(0,180,255,0.05);
}
.form-group textarea { min-height:120px; resize:vertical; }
.btn-primary { 
    background:linear-gradient(135deg, #0055ff, #0033cc); 
    color:white; 
    border:none; 
    padding:14px 40px; 
    border-radius:50px; 
    font-size:16px; 
    font-weight:700; 
    cursor:pointer; 
    transition:0.3s; 
    width:100%; 
    font-family:'Rajdhani',sans-serif;
    letter-spacing:1px;
    text-transform:uppercase;
    box-shadow:0 0 40px rgba(0,100,255,0.1);
}
.btn-primary:hover { 
    transform:scale(1.02); 
    box-shadow:0 0 60px rgba(0,100,255,0.2);
    background:linear-gradient(135deg, #0066ff, #0044dd);
}
.cheats-grid { 
    display:grid; 
    grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); 
    gap:25px; 
    padding:30px 0; 
}
.cheat-card { 
    background:rgba(10,14,26,0.8); 
    backdrop-filter:blur(10px); 
    border-radius:16px; 
    padding:25px; 
    border:1px solid rgba(0,180,255,0.06); 
    transition:0.4s; 
}
.cheat-card:hover { 
    transform:translateY(-5px); 
    border-color:rgba(0,180,255,0.15); 
    box-shadow:0 15px 50px rgba(0,0,0,0.4);
}
.cheat-card img { 
    width:100%; 
    height:160px; 
    object-fit:cover; 
    border-radius:12px; 
    margin-bottom:15px; 
    border:1px solid rgba(0,180,255,0.05);
}
.cheat-card h3 { 
    margin-bottom:8px; 
    color:#00b4ff; 
    font-size:18px;
    font-weight:700;
    letter-spacing:0.5px;
}
.cheat-card .price { 
    font-size:24px; 
    color:#00ff88; 
    font-weight:700; 
    font-family:'Orbitron',sans-serif;
}
.cheat-card .btn-buy { 
    display:inline-block; 
    background:linear-gradient(135deg, #00ff88, #00cc66); 
    color:#0a0e1a; 
    border:none; 
    padding:10px 30px; 
    border-radius:50px; 
    text-decoration:none; 
    margin-top:15px; 
    transition:0.3s; 
    cursor:pointer; 
    font-weight:700;
    font-size:14px;
    letter-spacing:0.5px;
}
.cheat-card .btn-buy:hover { 
    transform:scale(1.05); 
    box-shadow:0 0 40px rgba(0,255,136,0.2);
}
.flash-messages { padding:15px; border-radius:12px; margin:20px 0; }
.flash-message { 
    padding:14px 22px; 
    border-radius:10px; 
    margin:8px 0; 
    background:rgba(0,180,255,0.05); 
    border-left:3px solid #00b4ff; 
    border:1px solid rgba(0,180,255,0.08);
    color:rgba(255,255,255,0.8);
}
.dashboard { padding:30px 0; }
.dashboard h2 {
    font-family:'Orbitron',sans-serif;
    font-size:28px;
    font-weight:700;
    background: linear-gradient(135deg, #00b4ff, #0088ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing:1px;
}
.owner-actions { margin:20px 0; }
.purchase-item { 
    background:rgba(10,14,26,0.6); 
    padding:18px 22px; 
    border-radius:12px; 
    margin:12px 0; 
    border:1px solid rgba(0,180,255,0.06); 
}
.purchase-item .status-pending { color:#ffaa00; }
.purchase-item .status-paid { color:#00ff88; }
.purchase-item .status-delivered { color:#00b4ff; }
footer { 
    text-align:center; 
    padding:40px 0; 
    opacity:0.3; 
    border-top:1px solid rgba(0,180,255,0.05); 
    margin-top:60px; 
    font-size:14px;
    letter-spacing:1px;
}
@media(max-width:768px){ 
    .nav-content{flex-direction:column;gap:15px} 
    .hero h1{font-size:32px} 
    .nav-links{flex-direction:column;border-radius:12px;width:100%} 
    .nav-links li:not(:last-child){border-right:none;border-bottom:1px solid rgba(0,180,255,0.05)} 
    .nav-links a{text-align:center;padding:12px}
    .brand{font-size:18px}
    .hero{padding:50px 20px}
    .auth-form{padding:30px 20px;margin:30px 15px}
}
</style>
</head>
<body>
<nav><div class="container nav-content">
<div class="brand"><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/9.png">Aqua Cheats</div>
<ul class="nav-links">
<li><a href="/">Accueil</a></li>
<li><a href="/category/fivem">FiveM</a></li>
<li><a href="/category/roblox">Roblox</a></li>
<li><a href="/category/fortnite">Fortnite</a></li>
<li><a href="/category/valorant">Valorant</a></li>
{% if current_user.is_authenticated %}<li><a href="/dashboard">Dashboard</a></li><li><a href="/logout">Deconnexion</a></li>{% else %}<li><a href="/login">Connexion</a></li><li><a href="/register">Inscription</a></li>{% endif %}
</ul></div></nav>
<div class="container">
{% with messages = get_flashed_messages() %}{% if messages %}<div class="flash-messages">{% for m in messages %}<div class="flash-message">{{ m }}</div>{% endfor %}</div>{% endif %}{% endwith %}
{CONTENT}
</div>
<footer><div class="container"><p>2026 Aqua Cheats • Tortank Store</p></div></footer>
</body>
</html>"""

HTML_INDEX = HTML_BASE.replace('{CONTENT}', """
<div class="hero">
    <div class="subtitle">AQUA CHEATS</div>
    <h1>Aqua Cheats Store</h1>
    <p>Les meilleurs cheats pour FiveM, Roblox, Fortnite et Valorant</p>
</div>
<div class="categories-grid">
<div class="category-card"><a href="/category/fivem"><img src="/logos/Fivem.png" alt="FiveM" class="game-logo" onerror="this.style.display='none'"><h2>FiveM</h2><span class="game-tag">GTA V</span></a></div>
<div class="category-card"><a href="/category/roblox"><img src="/logos/Roblox.png" alt="Roblox" class="game-logo" onerror="this.style.display='none'"><h2>Roblox</h2><span class="game-tag">Universal</span></a></div>
<div class="category-card"><a href="/category/fortnite"><img src="/logos/Fortnite.png" alt="Fortnite" class="game-logo" onerror="this.style.display='none'"><h2>Fortnite</h2><span class="game-tag">Battle Royale</span></a></div>
<div class="category-card"><a href="/category/valorant"><img src="/logos/Valorant.png" alt="Valorant" class="game-logo" onerror="this.style.display='none'"><h2>Valorant</h2><span class="game-tag">Tactical FPS</span></a></div>
</div>
""")

HTML_LOGIN = HTML_BASE.replace('{CONTENT}', """
<div class="auth-form"><h2>Connexion</h2>
<form method="POST"><div class="form-group"><label>Nom d'utilisateur</label><input type="text" name="username" required></div>
<div class="form-group"><label>Mot de passe</label><input type="password" name="password" required></div>
<button type="submit" class="btn-primary">Se connecter</button></form>
<p style="text-align:center;margin-top:25px;color:rgba(255,255,255,0.4);">Pas de compte ? <a href="/register" style="color:#00b4ff;text-decoration:none;">Inscription</a></p></div>
""")

HTML_REGISTER = HTML_BASE.replace('{CONTENT}', """
<div class="auth-form"><h2>Inscription</h2>
<form method="POST"><div class="form-group"><label>Nom d'utilisateur</label><input type="text" name="username" required></div>
<div class="form-group"><label>Email</label><input type="email" name="email" required></div>
<div class="form-group"><label>Mot de passe</label><input type="password" name="password" required></div>
<button type="submit" class="btn-primary">S'inscrire</button></form>
<p style="text-align:center;margin-top:25px;color:rgba(255,255,255,0.4);">Deja un compte ? <a href="/login" style="color:#00b4ff;text-decoration:none;">Connexion</a></p></div>
""")

HTML_DASHBOARD_OWNER = HTML_BASE.replace('{CONTENT}', """
<div class="dashboard"><h2>Dashboard Owner</h2>
<a href="/add_cheat" class="btn-primary" style="display:inline-block;width:auto;margin:20px 0;padding:12px 35px;">+ Ajouter un cheat</a>
<h3 style="margin-top:30px;color:rgba(255,255,255,0.6);">Ventes</h3>
<div class="cheats-grid">{% for c in cheats %}<div class="cheat-card"><h3>{{ c.title }}</h3><p style="color:rgba(255,255,255,0.6);">{{ c.description[:100] }}...</p><p style="color:rgba(255,255,255,0.3);font-size:13px;">Cat: {{ c.category }}</p><p class="price">{{ c.price }}€</p></div>{% endfor %}</div></div>
""")

HTML_DASHBOARD_USER = HTML_BASE.replace('{CONTENT}', """
<div class="dashboard"><h2>Mes achats</h2>
{% if purchases %}
    {% for p in purchases %}<div class="purchase-item"><h3 style="color:#00b4ff;">{{ p.cheat.title }}</h3><p style="color:rgba(255,255,255,0.5);">{{ p.cheat.category }} - {{ p.cheat.price }}€</p><p style="color:rgba(255,255,255,0.3);font-size:13px;">Email: {{ p.buyer_email }}</p><p style="color:rgba(255,255,255,0.3);font-size:13px;">Transaction: {{ p.paypal_transaction_id or 'Non fourni' }}</p><p style="color:rgba(255,255,255,0.2);font-size:12px;">Le {{ p.purchased_at.strftime('%d/%m/%Y') }}</p><p>Statut: <span class="status-{{ p.status }}">{{ p.status }}</span></p></div>{% endfor %}
{% else %}
    <p style="color:rgba(255,255,255,0.4);">Aucun achat pour le moment.</p>
{% endif %}
</div>
""")

HTML_ADD_CHEAT = HTML_BASE.replace('{CONTENT}', """
<div class="auth-form"><h2>Ajouter un cheat</h2>
<form method="POST"><div class="form-group"><label>Titre</label><input type="text" name="title" required></div>
<div class="form-group"><label>Description</label><textarea name="description" required></textarea></div>
<div class="form-group"><label>Categorie</label><select name="category"><option value="fivem">FiveM</option><option value="roblox">Roblox</option><option value="fortnite">Fortnite</option><option value="valorant">Valorant</option></select></div>
<div class="form-group"><label>Prix (€)</label><input type="number" step="0.01" name="price" required></div>
<div class="form-group"><label>Lien de telechargement (cache)</label><input type="url" name="download_link" required></div>
<div class="form-group"><label>Image URL (optionnel)</label><input type="url" name="image_url"></div>
<button type="submit" class="btn-primary">Ajouter</button></form></div>
""")

HTML_CATEGORY = HTML_BASE.replace('{CONTENT}', """
<h2 style="margin:30px 0;font-family:'Orbitron',sans-serif;font-weight:700;background:linear-gradient(135deg,#00b4ff,#0088ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:1px;">{{ category_name }}</h2>
<div class="cheats-grid">{% for c in cheats %}<div class="cheat-card"><h3>{{ c.title }}</h3><p style="color:rgba(255,255,255,0.6);">{{ c.description[:100] }}...</p><p class="price">{{ c.price }}€</p><a href="/product/{{ c.id }}" class="btn-buy">Voir</a></div>{% endfor %}</div>
""")

HTML_PRODUCT = HTML_BASE.replace('{CONTENT}', """
<div style="max-width:600px;margin:40px auto;background:rgba(10,14,26,0.9);padding:40px;border-radius:20px;border:1px solid rgba(0,180,255,0.08);">
<h2 style="font-family:'Orbitron',sans-serif;font-weight:700;background:linear-gradient(135deg,#00b4ff,#0088ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:1px;">{{ cheat.title }}</h2>
<p style="color:rgba(255,255,255,0.7);margin:15px 0;">{{ cheat.description }}</p>
<p style="color:rgba(255,255,255,0.4);">Categorie : {{ cheat.category }}</p>
<p class="price" style="font-size:32px;color:#00ff88;font-weight:700;font-family:'Orbitron',sans-serif;margin:15px 0;">{{ cheat.price }}€</p>

<div style="background:rgba(0,180,255,0.05);border-radius:12px;padding:20px;margin:20px 0;border:1px solid rgba(0,180,255,0.08);">
    <h4 style="color:#00b4ff;margin-bottom:10px;">Instructions d'achat :</h4>
    <ol style="color:rgba(255,255,255,0.7);line-height:1.8;padding-left:20px;">
        <li>Envoyez <strong>{{ cheat.price }}€</strong> sur PayPal : <a href="https://www.paypal.com/paypalme/BestPlayer54" target="_blank" style="color:#00ff88;text-decoration:none;">paypal.com/paypalme/BestPlayer54</a></li>
        <li>Entrez votre email et l'ID de transaction PayPal ci-dessous</li>
        <li>Cliquez sur "Valider mon paiement"</li>
        <li>Le lien de telechargement vous sera envoye automatiquement par email</li>
    </ol>
</div>

<form method="POST" action="/buy/{{ cheat.id }}">
<div class="form-group"><label>Votre email pour recevoir le lien</label><input type="email" name="email" placeholder="exemple@email.com" required></div>
<div class="form-group"><label>ID de transaction PayPal</label><input type="text" name="paypal_id" placeholder="Ex: 9JX12345K6789012L" required></div>
<button type="submit" class="btn-primary" style="background:linear-gradient(135deg,#00ff88,#00cc66);color:#0a0e1a;">Valider mon paiement</button>
</form>
</div>
""")

# ===== ROUTES =====
@app.route('/')
def index():
    return render_template_string(HTML_INDEX)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            flash('Connexion reussie !', 'success')
            return redirect(url_for('dashboard'))
        flash('Identifiants invalides.', 'danger')
    return render_template_string(HTML_LOGIN)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Nom d\'utilisateur deja pris.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email deja utilise.', 'danger')
            return redirect(url_for('register'))
        
        is_owner = (username == 'aqua' and password == 'stormthebest123_')
        user = User(username=username, email=email, is_owner=is_owner)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Inscription reussie ! Connectez-vous.', 'success')
        return redirect(url_for('login'))
    return render_template_string(HTML_REGISTER)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Deconnecte.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_owner:
        cheats = Cheat.query.filter_by(owner_id=current_user.id).all()
        return render_template_string(HTML_DASHBOARD_OWNER, cheats=cheats)
    else:
        purchases = Purchase.query.filter_by(user_id=current_user.id).all()
        return render_template_string(HTML_DASHBOARD_USER, purchases=purchases)

@app.route('/add_cheat', methods=['GET', 'POST'])
@login_required
def add_cheat():
    if not current_user.is_owner:
        flash('Seul le proprietaire peut ajouter des cheats.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        cheat = Cheat(
            title=request.form.get('title'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            price=float(request.form.get('price')),
            download_link=request.form.get('download_link'),
            image_url=request.form.get('image_url', ''),
            owner_id=current_user.id
        )
        db.session.add(cheat)
        db.session.commit()
        flash('Cheat ajoute !', 'success')
        return redirect(url_for('dashboard'))
    return render_template_string(HTML_ADD_CHEAT)

@app.route('/category/<category>')
def category(category):
    cheats = Cheat.query.filter_by(category=category, is_active=True).all()
    names = {'fivem': 'FiveM', 'roblox': 'Roblox', 'fortnite': 'Fortnite', 'valorant': 'Valorant'}
    return render_template_string(HTML_CATEGORY, cheats=cheats, category_name=names.get(category, category))

@app.route('/product/<int:cheat_id>')
def product_detail(cheat_id):
    cheat = Cheat.query.get_or_404(cheat_id)
    return render_template_string(HTML_PRODUCT, cheat=cheat)

@app.route('/buy/<int:cheat_id>', methods=['POST'])
@login_required
def buy_cheat(cheat_id):
    cheat = Cheat.query.get_or_404(cheat_id)
    buyer_email = request.form.get('email')
    paypal_id = request.form.get('paypal_id', '')
    
    if not buyer_email:
        flash('Email requis.', 'danger')
        return redirect(url_for('product_detail', cheat_id=cheat_id))
    
    if not paypal_id:
        flash('ID de transaction PayPal requis.', 'danger')
        return redirect(url_for('product_detail', cheat_id=cheat_id))
    
    # Créer l'achat
    purchase = Purchase(
        user_id=current_user.id, 
        cheat_id=cheat.id, 
        buyer_email=buyer_email,
        paypal_transaction_id=paypal_id,
        status='paid'
    )
    db.session.add(purchase)
    db.session.commit()
    
    # Envoyer l'email automatique avec le lien
    try:
        msg = Message(
            subject=f'AQUA CHEATS - Votre cheat {cheat.title}',
            recipients=[buyer_email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        msg.body = f"""
╔═══════════════════════════════════════════════════╗
║              AQUA CHEATS - TORTANK STORE          ║
╚═══════════════════════════════════════════════════╝

Bonjour {current_user.username},

Merci pour votre achat chez Aqua Cheats !

📦 PRODUIT : {cheat.title}
🏷️ CATEGORIE : {cheat.category}
💰 PRIX : {cheat.price}€
📅 DATE : {datetime.now().strftime('%d/%m/%Y à %H:%M')}

🔗 LIEN DE TELECHARGEMENT :
{cheat.download_link}

⚠️ INSTRUCTIONS :
- Ce lien est strictement confidentiel
- Ne le partagez avec personne
- Valable pour une seule utilisation

📧 Email de contact : {buyer_email}
🆔 Transaction PayPal : {paypal_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aqua Cheats - Le meilleur du gaming
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        mail.send(msg)
        flash('✅ Paiement confirmé ! Le lien de téléchargement vous a été envoyé par email.', 'success')
    except Exception as e:
        flash(f'❌ Erreur lors de l\'envoi de l\'email : {str(e)}. Contactez le support.', 'danger')
        print(f"Erreur email: {e}")
    
    return redirect(url_for('dashboard'))

# ===== CREATION BASE + OWNER =====
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='aqua').first():
        owner = User(username='aqua', email='owner@aqua.com', is_owner=True)
        owner.set_password('stormthebest123_')
        db.session.add(owner)
        db.session.commit()
        print("✅ Compte owner cree : aqua / stormthebest123_")

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════╗
    ║   🐢 AQUA CHEATS - TORTANK STORE 🐢      ║
    ║   Site : http://localhost:5000            ║
    ║   Owner : aqua / stormthebest123_         ║
    ╚═══════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)