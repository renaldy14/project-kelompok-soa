import os

import psycopg2
from database import get_db_connection
from flask import Flask, jsonify, render_template, request
from psycopg2.extras import RealDictCursor
from werkzeug.exceptions import HTTPException

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "..", "frontend", "templates")
static_dir = os.path.join(base_dir, "..", "frontend", "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

MAX_TEXT_LENGTH = 100
MAX_QUANTITY = 2147483647
HTTP_ERROR_MESSAGES = {
    404: "Endpoint tidak ditemukan",
    405: "Metode HTTP tidak diizinkan",
}


def api_response(message, data=None, status=200):
    return jsonify({"message": message, "data": data}), status


def read_product_values():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, "Request body harus berupa JSON object"

    product_name = data.get("product_name")
    category = data.get("category")
    quantity = data.get("quantity")

    if not isinstance(product_name, str) or not product_name.strip():
        return None, "Nama barang wajib diisi"

    if not isinstance(category, str) or not category.strip():
        return None, "Kategori wajib diisi"

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return None, "Quantity harus berupa bilangan bulat"

    product_name = product_name.strip()
    category = category.strip()

    if len(product_name) > MAX_TEXT_LENGTH:
        return None, f"Nama barang maksimal {MAX_TEXT_LENGTH} karakter"

    if len(category) > MAX_TEXT_LENGTH:
        return None, f"Kategori maksimal {MAX_TEXT_LENGTH} karakter"

    if quantity < 0:
        return None, "Quantity tidak boleh kurang dari 0"

    if quantity > MAX_QUANTITY:
        return None, f"Quantity maksimal {MAX_QUANTITY}"

    return (product_name, category, quantity), None


@app.errorhandler(HTTPException)
def handle_http_error(error):
    message = HTTP_ERROR_MESSAGES.get(error.code, error.description)
    return api_response(message, status=error.code)


@app.errorhandler(psycopg2.OperationalError)
def handle_database_outage(error):
    app.logger.error("Database tidak tersedia: %s", error)
    return api_response("Database tidak tersedia", status=503)


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Kesalahan tidak terduga")
    return api_response("Terjadi kesalahan pada server", status=500)


# =====================================
# 0. HALAMAN UTAMA
# =====================================


@app.route("/")
def home():
    return render_template("index.html")


# =====================================
# 1. GET ALL PRODUCTS
# =====================================


@app.route("/api/products", methods=["GET"])
def get_products():
    conn = get_db_connection()

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT * FROM products
            ORDER BY id ASC
        """)

        products = cur.fetchall()

        cur.close()

        return api_response("Daftar barang berhasil diambil", products)

    finally:
        conn.close()


# =====================================
# 2. GET PRODUCT BY ID
# =====================================


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db_connection()

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))

        product = cur.fetchone()

        cur.close()

        if product is None:
            return api_response("Product not found", status=404)

        return api_response("Detail barang berhasil diambil", product)

    finally:
        conn.close()


# =====================================
# 3. CREATE PRODUCT
# =====================================


@app.route("/api/products", methods=["POST"])
def create_product():
    values, error = read_product_values()

    if error:
        return api_response(error, status=400)

    conn = get_db_connection()

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            INSERT INTO products
            (product_name, category, quantity)
            VALUES (%s, %s, %s)
            RETURNING *
        """,
            values,
        )

        product = cur.fetchone()
        conn.commit()

        cur.close()

        return api_response("Product created successfully", product, 201)

    finally:
        conn.close()


# =====================================
# 4. UPDATE PRODUCT
# =====================================


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    values, error = read_product_values()

    if error:
        return api_response(error, status=400)

    conn = get_db_connection()

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            UPDATE products
            SET product_name = %s,
                category = %s,
                quantity = %s
            WHERE id = %s
            RETURNING *
        """,
            (*values, product_id),
        )

        product = cur.fetchone()

        if product is None:
            conn.rollback()
            return api_response("Product not found", status=404)

        conn.commit()
        cur.close()

        return api_response("Product updated successfully", product)

    finally:
        conn.close()


# =====================================
# 5. DELETE PRODUCT
# =====================================


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM products
            WHERE id = %s
            RETURNING id
        """,
            (product_id,),
        )

        deleted_product = cur.fetchone()

        if deleted_product is None:
            conn.rollback()
            return api_response("Product not found", status=404)

        conn.commit()
        cur.close()

        return api_response("Product deleted successfully")

    finally:
        conn.close()


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
