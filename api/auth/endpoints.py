"""Routes for module books"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, decode_token
from flask_bcrypt import Bcrypt

from helper.db_helper import get_connection

bcrypt = Bcrypt()
auth_endpoints = Blueprint('auth', __name__)


@auth_endpoints.route('/login', methods=['POST'])
def login():
    """Routes for authentication"""
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM md_user WHERE username = %s"
    request_query = (username,)
    cursor.execute(query, request_query)
    user = cursor.fetchone()
    cursor.close()
    print(f"ini user: {user}")
    print(bcrypt.check_password_hash(user.get('password'), password))

    if not user or not bcrypt.check_password_hash(user.get('password'), password):
        return jsonify({"message": "Wrong username or password"}), 401

    access_token = create_access_token(
        identity = username
    )
    decoded_token = decode_token(access_token)
    expires = decoded_token['exp']

    return jsonify({
        "access_token": access_token,
        "expires_in": expires,
        "type": "Bearer"
    })


@auth_endpoints.route('/register', methods=['POST'])
def register():
    """Routes for register"""
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    role = request.form['role']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    
    # Check if the username or email already exists in the database
    connection = get_connection()
    cursor = connection.cursor()

    # Cek apakah produk dengan nama yang sama sudah ada
    select_query = "SELECT * FROM MD_user WHERE username = %s OR email = %s"
    cursor.execute(select_query, (username, email))
    existing_product = cursor.fetchone()

    if existing_product:
        # Jika produk sudah ada, return 409 Conflict
        return jsonify({"message": "User already exists.", "datas": None}), 409
    # To hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Now, reinitialize the cursor for the INSERT query
    cursor = connection.cursor()
    insert_query = "INSERT INTO md_user (username, password, name, role, phone, email, address) values (%s, %s, %s, %s, %s, %s, %s)"
    request_insert = (username, hashed_password, name, role, phone, email, address)
    cursor.execute(insert_query, request_insert)
    connection.commit()
    cursor.close()

    new_id = cursor.lastrowid
    if new_id:
        return jsonify({"message": "User Created", "datas": {"username": username}}), 201
    
    return jsonify({"message": "Failed, can't register user"}), 501

