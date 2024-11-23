import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data

products_endpoints = Blueprint('products', __name__)
UPLOAD_FOLDER = "img"

# Endpoint untuk membaca daftar produk
@products_endpoints.route('/read', methods=['GET'])
def read():
    """Routes for module get list products"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    select_query = "SELECT * FROM MD_Product"
    cursor.execute(select_query)
    results = cursor.fetchall()
    cursor.close()  # Close the cursor after query execution
    return jsonify({"message": "OK", "datas": results}), 200

@products_endpoints.route('/create', methods=['POST'])
def create():
    """Routes for module create a product"""
    required = get_form_data(["product_name", "price", "category_id"])  # Ambil data wajib
    product_name = required["product_name"]
    price = request.form['price']
    category_id = request.form['category_id']
    stock = request.form.get('stock', 0)  # Default 0 jika tidak ada

    # Cek validasi untuk harga dan stok
    if not product_name or not price or not category_id:
        return jsonify({"message": "Product name, price, and category_id are required."}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Cek apakah produk dengan nama yang sama sudah ada
    select_query = "SELECT * FROM MD_Product WHERE product_name = %s"
    cursor.execute(select_query, (product_name,))
    existing_product = cursor.fetchone()

    if existing_product:
        # Jika produk sudah ada, return 409 Conflict
        return jsonify({"message": "Product already exists."}), 409

    # Jika produk belum ada, lakukan insert
    insert_query = """
        INSERT INTO MD_Product (product_name, price, category_id, stock) 
        VALUES (%s, %s, %s, %s)
    """
    request_insert = (product_name, price, category_id, stock)
    cursor.execute(insert_query, request_insert)
    connection.commit()  # Commit changes to the database
    cursor.close()
    new_id = cursor.lastrowid  # Get the newly inserted product's ID

    if new_id:
        return jsonify({"message": "Inserted", "product_id": new_id, "product_name": product_name}), 201
    return jsonify({"message": "Can't Insert Data"}), 500



# Endpoint untuk memperbarui produk
@products_endpoints.route('/update/<int:product_id>', methods=['PUT'])
def update(product_id):
    """Routes for module update a product"""
    required = get_form_data(["product_name", "price", "category_id"])  # Ambil data wajib
    product_name = required["product_name"]
    price = request.form['price']
    category_id = request.form['category_id']
    stock = request.form.get('stock', 0)  # Default 0 jika tidak ada

    # Cek validasi untuk harga dan stok
    if not product_name or not price or not category_id:
        return jsonify({"message": "Product name, price, and category_id are required."}), 400

    connection = get_connection()
    cursor = connection.cursor()

    update_query = """
        UPDATE MD_Product 
        SET product_name=%s, price=%s, category_id=%s, stock=%s 
        WHERE product_id=%s
    """
    update_request = (product_name, price, category_id, stock, product_id)
    cursor.execute(update_query, update_request)
    connection.commit()
    cursor.close()

    data = {"message": "Product updated", "product_id": product_id}
    return jsonify(data), 200


# Endpoint untuk menghapus produk
@products_endpoints.route('/delete/<int:product_id>', methods=['DELETE'])
def delete(product_id):
    """Routes for module to delete a product"""
    connection = get_connection()
    cursor = connection.cursor()

    print(product_id)

    delete_query = "DELETE FROM MD_Product WHERE product_id = %s"
    cursor.execute(delete_query, (product_id,))
    connection.commit()
    cursor.close()

    data = {"message": "Product deleted", "product_id": product_id}
    return jsonify(data), 200


# Endpoint untuk upload gambar produk
@products_endpoints.route("/upload", methods=["POST"])
def upload():
    """Routes for upload product image"""
    # Ambil product_id dari form data
    product_id = request.form.get('product_id')
    uploaded_file = request.files.get('file')
    
    if not product_id:
        return jsonify({"err_message": "Product ID is required"}), 400

    if uploaded_file and uploaded_file.filename != '':
        # Tentukan path file
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        
        # Simpan file di folder yang ditentukan
        uploaded_file.save(file_path)
        
        # Perbarui produk dengan path gambar di database
        connection = get_connection()
        cursor = connection.cursor()
        update_query = "UPDATE MD_Product SET image_path = %s WHERE product_id = %s"
        cursor.execute(update_query, (file_path, product_id))
        connection.commit()
        cursor.close()
        
        return jsonify({"message": "ok", "data": "uploaded", "file_path": file_path}), 200

    return jsonify({"err_message": "Can't upload image"}), 400

