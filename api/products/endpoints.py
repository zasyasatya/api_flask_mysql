import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
import glob
import re

def validate_inputs(limit, page, search, sort_column, sort_direction):
    try:
        limit = int(limit)  # Konversi ke integer
        page = int(page)    # Konversi ke integer
    except ValueError:
        raise ValueError("Limit and page must be numeric integers.")
    
    # Validasi sort_direction
    if sort_direction not in ['asc', 'desc']:
        raise ValueError("Sort direction must be 'ASC' or 'DESC'.")
    
    # Validasi sort_column
    allowed_sort_columns = ['product_name', 'price', 'stock', 'created_at', 'updated_at', 'category_id']
    if sort_column not in allowed_sort_columns:
        raise ValueError("Invalid sort column.")
    
    # Validasi search
    if len(search) > 255 or not re.match(r'^[a-zA-Z0-9\s]*$', search):
        raise ValueError("Search term is invalid, only receive alphabet and numerical parameter")

    return limit, page, search, sort_column, sort_direction


products_endpoints = Blueprint('products', __name__)
UPLOAD_FOLDER = "img"
# Endpoint untuk membaca daftar produk
@products_endpoints.route('/read', methods=['GET'])
def read():
    """Routes for module get list products with pagination"""
    
    try:
        # Mendapatkan koneksi dari pool dan cursor menggunakan konteks manajer
        with get_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                
                # Ambil parameter pagination dari query string
                try:
                    page = int(request.args.get('page', 1))  # Default page adalah 1
                    limit = int(request.args.get('limit', 10))  # Default limit adalah 10
                    search = request.args.get('search', ' ')  # Default search adalah empty string
                    sort_column = request.args.get('sort_column', 'product_name')  # Default sort_column
                    sort_direction = request.args.get('sort_direction', 'ASC')  # Default sort_direction
                except ValueError:
                    return jsonify({"message": "Invalid pagination parameters", "datas": None}), 400

                if page < 1 or limit < 1:
                    return jsonify({"message": "Page and limit must be positive integers", "datas": None}), 400

                # Hitung offset untuk query SQL
                # offset = (page - 1) * limit

                print(page
                ,limit
                ,search
                ,sort_column
                ,sort_direction)

                # Hitung total produk (untuk total_pages)
                count_query = """
                    SELECT COUNT(*) as total
                    FROM MD_Product product
                    LEFT JOIN REF_Category category ON product.category_id = category.category_id
                    WHERE product.is_deleted = FALSE
                    AND (
                        product.product_name LIKE CONCAT('%', %s, '%') OR
                        CAST(product.price AS CHAR) LIKE CONCAT('%', %s, '%') OR
                        CAST(product.stock AS CHAR) LIKE CONCAT('%', %s, '%') OR
                        DATE_FORMAT(product.created_at, '%Y-%m-%d') LIKE CONCAT('%', %s, '%') OR
                        DATE_FORMAT(product.updated_at, '%Y-%m-%d') LIKE CONCAT('%', %s, '%') OR
                        category.category_name LIKE CONCAT('%', %s, '%')
                    )
                """

                # Eksekusi query
                cursor.execute(count_query, (search, search, search, search, search, search))
                total_products = cursor.fetchone()["total"]

                # Sanitize parameter
                limit, page, search, sort_column, sort_direction = validate_inputs(limit, page, search, sort_column, sort_direction)

                # Call Stored Procedure
                cursor.callproc('sp_get_product_data', [limit, page, search, sort_column, sort_direction])

                results = cursor.stored_results

                for result in cursor.stored_results():
                    # If the stored procedure returns a result set, fetch all rows
                    results = result.fetchall()
                    print(results)
  

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
    
    except Exception as e:
        # Tangani error dan pastikan koneksi ditutup meskipun terjadi error
        return jsonify({"message": "Error occurred", "error": str(e)}), 500


@products_endpoints.route('/create', methods=['POST'])
def create():
    """Routes for module create a product"""
    # Ambil data wajib
    required = get_form_data(["product_name", "price", "category_id"])
    product_name = required.get("product_name")
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    stock = request.form.get('stock', 0)  # Default 0 jika tidak ada
    supplier = request.form.get('supplier', '')  # Default kosong jika tidak ada

    # Validasi input
    if not product_name or not price or not category_id:
        return jsonify({"message": "Product name, price, and category_id are required.", "datas": None}), 400

    try:
        # Koneksi ke database
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Cek apakah produk dengan nama yang sama sudah ada
        select_query = "SELECT * FROM MD_Product WHERE product_name = %s"
        cursor.execute(select_query, (product_name,))
        existing_product = cursor.fetchone()

        if existing_product:
            # Jika produk sudah ada, return 409 Conflict
            return jsonify({"message": "Product already exists.", "datas": None}), 409

        # Panggil Stored Procedure
        cursor.callproc('sp_create_product_data', [product_name, price, category_id, stock, supplier])

        # Ambil hasil dari prosedur tersimpan jika ada
        results = []
        for result in cursor.stored_results():
            rows = result.fetchall()
            for row in rows:
                # Pastikan data bisa diserialisasi ke JSON
                results.append({key: str(value) if isinstance(value, (bytes, bytearray)) else value for key, value in row.items()})

        connection.commit()  # Commit perubahan ke database

    except mysql.connector.Error as err:
        return jsonify({"message": f"Database error: {err}", "datas": None}), 500
    except Exception as e:
        return jsonify({"message": f"Internal error: {e}", "datas": None}), 500
    finally:
        cursor.close()
        connection.close()

    if results:
        return jsonify({"message": "Product created successfully.", "datas": results}), 201
    return jsonify({"message": "Product created but no data returned.", "datas": None}), 201

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

    return jsonify({"message": "Can't upload image"}), 400


