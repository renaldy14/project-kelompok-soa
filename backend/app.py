import os

from database import get_db_connection
from flask import Flask, jsonify, render_template, request
from psycopg2.extras import RealDictCursor

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "..", "frontend", "templates")
static_dir = os.path.join(base_dir, "..", "frontend", "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

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

        return jsonify(products), 200

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
            return jsonify({"message": "Product not found"}), 404

        return jsonify(product), 200

    finally:
        conn.close()


# =====================================
# 3. CREATE PRODUCT
# =====================================


@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"message": "Request body harus berupa JSON object"}), 400

    product_name = data.get("product_name")
    category = data.get("category")
    quantity = data.get("quantity")

    if not isinstance(product_name, str) or not product_name.strip():
        return jsonify({"message": "Nama barang wajib diisi"}), 400

    if not isinstance(category, str) or not category.strip():
        return jsonify({"message": "Kategori wajib diisi"}), 400

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return jsonify({"message": "Quantity harus berupa bilangan bulat"}), 400

    if quantity < 0:
        return jsonify({"message": "Quantity tidak boleh kurang dari 0"}), 400

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
            (product_name.strip(), category.strip(), quantity),
        )

        product = cur.fetchone()
        conn.commit()

        cur.close()

        return jsonify(
            {"message": "Product created successfully", "data": product}
        ), 201

    finally:
        conn.close()


# =====================================
# 4. UPDATE PRODUCT
# =====================================


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"message": "Request body harus berupa JSON object"}), 400

    product_name = data.get("product_name")
    category = data.get("category")
    quantity = data.get("quantity")

    if not isinstance(product_name, str) or not product_name.strip():
        return jsonify({"message": "Nama barang wajib diisi"}), 400

    if not isinstance(category, str) or not category.strip():
        return jsonify({"message": "Kategori wajib diisi"}), 400

    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return jsonify({"message": "Quantity harus berupa bilangan bulat"}), 400

    if quantity < 0:
        return jsonify({"message": "Quantity tidak boleh kurang dari 0"}), 400

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
            (product_name.strip(), category.strip(), quantity, product_id),
        )

        product = cur.fetchone()

        if product is None:
            conn.rollback()
            return jsonify({"message": "Product not found"}), 404

        conn.commit()
        cur.close()

        return jsonify(
            {"message": "Product updated successfully", "data": product}
        ), 200

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
            return jsonify({"message": "Product not found"}), 404

        conn.commit()
        cur.close()

        return jsonify({"message": "Product deleted successfully"}), 200

    finally:
        conn.close()


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
