import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
import glob

products_endpoints = Blueprint('products', __name__)
UPLOAD_FOLDER = "img"

# Endpoint untuk membaca daftar produk
@products_endpoints.route('/read', methods=['GET'])
def read():
    """Routes for module get list products with pagination"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Ambil parameter pagination dari query string
    try:
        page = int(request.args.get('page', 1))  # Default page adalah 1
        limit = int(request.args.get('limit', 10))  # Default limit adalah 10
    except ValueError:
        return jsonify({"message": "Invalid pagination parameters", "datas": None}), 400

    if page < 1 or limit < 1:
        return jsonify({"message": "Page and limit must be positive integers", "datas": None}), 400

    # Hitung offset untuk query SQL
    offset = (page - 1) * limit

    # Hitung total produk (untuk total_pages)
    count_query = "SELECT COUNT(*) as total FROM MD_Product WHERE is_deleted = FALSE"
    cursor.execute(count_query)
    total_products = cursor.fetchone()["total"]

    # Ambil data produk dengan batasan limit dan offset
    select_query = """
        SELECT * 
        FROM MD_Product 
        WHERE is_deleted = FALSE
        LIMIT %s OFFSET %s
    """
    cursor.execute(select_query, (limit, offset))
    results = cursor.fetchall()

    # Tutup koneksi database
    cursor.close()

    # Hitung total halaman
    total_pages = (total_products + limit - 1) // limit  # Pembulatan ke atas

    # Menambahkan informasi jumlah data pada halaman saat ini
    current_data_count = len(results)

    # Struktur respons
    response = {
        "message": "Data successfully retrieved",
        "datas": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_items": total_products,
            "current_data_count": current_data_count  # Menambahkan jumlah data yang ada di halaman ini
        }
    }
    return jsonify(response), 200



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
        return jsonify({"message": "Product name, price, and category_id are required.", "datas": None}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Cek apakah produk dengan nama yang sama sudah ada
    select_query = "SELECT * FROM MD_Product WHERE product_name = %s"
    cursor.execute(select_query, (product_name,))
    existing_product = cursor.fetchone()

    if existing_product:
        # Jika produk sudah ada, return 409 Conflict
        return jsonify({"message": "Product already exists.", "datas": None}), 409

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
        return jsonify({"message": "Inserted", "datas": {"product_id": new_id, "product_name": product_name}}), 201
    return jsonify({"message": "Can't Insert Data"}), 500

# Endpoint untuk menampilkana detail produk berdasarkan id
@products_endpoints.route('/detail/<int:product_id>', methods=['GET'])
def get_detail(product_id):
    """Routes for module get product detail"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Query untuk mengambil data produk berdasarkan product_id
    select_query = "SELECT * FROM MD_Product WHERE product_id = %s AND is_deleted = FALSE"
    cursor.execute(select_query, (product_id,))
    result = cursor.fetchone()  # Ambil satu data saja
    cursor.close()  # Tutup cursor setelah eksekusi

    # Jika data tidak ditemukan
    if not result:
        return jsonify({"message": "Product not found"}), 404

    return jsonify({"message": "OK", "datas": result}), 200


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
        return jsonify({"message": "Product name, price, and category_id are required.", "datas": None}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Query untuk memperbarui produk
    update_query = """
        UPDATE MD_Product 
        SET product_name=%s, price=%s, category_id=%s, stock=%s 
        WHERE product_id=%s
    """
    update_request = (product_name, price, category_id, stock, product_id)
    cursor.execute(update_query, update_request)
    connection.commit()

    # Ambil data produk yang telah diperbarui
    select_query = "SELECT * FROM MD_Product WHERE product_id = %s"
    cursor.execute(select_query, (product_id,))
    updated_product = cursor.fetchone()
    cursor.close()

    if updated_product:
        # Kembalikan data produk yang telah diperbarui
        data = {
            "message": "Product updated successfully",
            "datas": updated_product
        }
        return jsonify(data), 200
    else:
        # Jika produk tidak ditemukan
        return jsonify({"message": "Product not found", "datas": None}), 404



# Endpoint untuk menghapus produk (Soft Delete)
@products_endpoints.route('/delete/<int:product_id>', methods=['DELETE'])
def soft_delete(product_id):
    """Routes for module to soft delete a product"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)  # Pastikan dictionary=True agar hasilnya berupa dictionary

    # Ambil data produk sebelum dihapus (untuk menampilkan data di respons)
    select_query = "SELECT * FROM MD_Product WHERE product_id = %s AND is_deleted = FALSE"
    cursor.execute(select_query, (product_id,))
    product_to_delete = cursor.fetchone()

    if not product_to_delete:
        cursor.close()
        return jsonify({"message": "Product not found or already deleted"}), 404

    # Perbarui is_deleted menjadi TRUE untuk produk tertentu
    update_query = "UPDATE MD_Product SET is_deleted = TRUE WHERE product_id = %s AND is_deleted = FALSE"
    cursor.execute(update_query, (product_id,))
    connection.commit()

    cursor.close()

    # Kembalikan data produk yang telah dihapus
    data = {
        "message": "Product soft deleted",
        "datas": {
            "product_id": product_to_delete["product_id"],
            "product_name": product_to_delete["product_name"],
            "price": product_to_delete["price"],
            "category_id": product_to_delete["category_id"],
            "stock": product_to_delete["stock"],
            "image_path": product_to_delete["image_path"],
            "created_at": product_to_delete["created_at"],
            "updated_at": product_to_delete["updated_at"],
            "is_deleted": product_to_delete["is_deleted"]
        }
    }

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
        # Tentukan folder tempat file disimpan (img/products/)
        folder_path = os.path.join(UPLOAD_FOLDER, "products")
        
        # Pastikan folder ada, jika belum buat folder
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Hapus semua file lama yang cocok dengan pattern "product_id.*"
        old_files_pattern = os.path.join(folder_path, f"{product_id}.*")
        old_files = glob.glob(old_files_pattern)  # Cari semua file dengan nama yang cocok
        for old_file in old_files:
            os.remove(old_file)  # Hapus file lama
        
        # Membuat nama file baru berdasarkan product_id dan ekstensi file yang diunggah
        file_extension = os.path.splitext(uploaded_file.filename)[1]  # Ambil ekstensi file (.jpg, .png, dll.)
        new_filename = f"{product_id}{file_extension}"  # Buat nama file baru
        file_path = os.path.join(folder_path, new_filename)
        
        # Simpan file yang diunggah
        uploaded_file.save(file_path)
        
        # Perbarui produk dengan path gambar di database
        connection = get_connection()
        cursor = connection.cursor()
        update_query = "UPDATE MD_Product SET image_path = %s WHERE product_id = %s"
        cursor.execute(update_query, (file_path, product_id))
        connection.commit()
        cursor.close()
        
        return jsonify({"message": "ok", "datas": "uploaded", "file_path": file_path}), 200

    return jsonify({"err_message": "Can't upload image"}), 400


