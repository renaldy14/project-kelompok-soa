import os
import threading
import uuid

import psycopg2
import pytest
from psycopg2 import sql
from werkzeug.serving import make_server

from app import app as flask_app

os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "")


def connect(database):
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        database=database,
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


@pytest.fixture(scope="session")
def test_database():
    name = f"db_soa_test_{uuid.uuid4().hex[:8]}"
    identifier = sql.Identifier(name)

    admin = connect("postgres")
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(identifier))

    yield name

    with admin.cursor() as cur:
        cur.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(identifier)
        )
    admin.close()


@pytest.fixture(autouse=True)
def products_table(test_database, monkeypatch):
    monkeypatch.setenv("DB_NAME", test_database)

    conn = connect(test_database)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS products;
            CREATE TABLE products (
                id SERIAL PRIMARY KEY,
                product_name VARCHAR(100) NOT NULL,
                category VARCHAR(100) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO products (product_name, category, quantity) VALUES
                ('Laptop Lenovo', 'Elektronik', 5),
                ('Mouse Wireless', 'Aksesoris', 20);
        """)

    yield conn

    conn.close()


@pytest.fixture
def client():
    return flask_app.test_client()


@pytest.fixture(scope="session")
def live_server():
    server = make_server("127.0.0.1", 0, flask_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    thread.join()
