"""Small apps to demonstrate endpoints with basic feature - CRUD"""

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import jwt
from api.books.endpoints import books_endpoints
from api.products.endpoints import products_endpoints
from api.auth.endpoints import auth_endpoints
from api.data_protected.endpoints import protected_endpoints
# from api.fcm.endpoints import firebase_messaging
from config import Config
from static.static_file_server import static_file_server


# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


jwt.init_app(app)

# register the blueprint
app.register_blueprint(auth_endpoints, url_prefix='/api/v1/auth')
app.register_blueprint(protected_endpoints,
                       url_prefix='/api/v1/protected')
app.register_blueprint(books_endpoints, url_prefix='/api/v1/books')
app.register_blueprint(products_endpoints, url_prefix='/api/v1/products')
app.register_blueprint(static_file_server, url_prefix='/static/')
# app.register_blueprint(firebase_messaging, url_prefix="/api/v1/private/fcm")

if __name__ == '__main__':
    app.run(debug=True)
