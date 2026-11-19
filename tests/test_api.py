import pytest

VALID_PRODUCT = {
    "product_name": "Headset Gaming",
    "category": "Aksesoris",
    "quantity": 10,
}


def request_for(client, method):
    url = "/api/products" if method == "post" else "/api/products/1"
    send = getattr(client, method)
    return lambda **kwargs: send(url, **kwargs)


def test_list_products_returns_message_and_data(client):
    response = client.get("/api/products")

    assert response.status_code == 200
    body = response.get_json()
    assert body["message"] == "Daftar barang berhasil diambil"
    assert [p["product_name"] for p in body["data"]] == [
        "Laptop Lenovo",
        "Mouse Wireless",
    ]


def test_get_product_returns_message_and_data(client):
    response = client.get("/api/products/1")

    assert response.status_code == 200
    body = response.get_json()
    assert body["message"] == "Detail barang berhasil diambil"
    assert body["data"]["product_name"] == "Laptop Lenovo"
    assert body["data"]["quantity"] == 5


def test_missing_product_returns_404_with_null_data(client):
    responses = [
        client.get("/api/products/999"),
        client.put("/api/products/999", json=VALID_PRODUCT),
        client.delete("/api/products/999"),
    ]

    for response in responses:
        assert response.status_code == 404
        assert response.get_json() == {
            "message": "Product not found",
            "data": None,
        }


def test_delete_product_removes_it(client):
    response = client.delete("/api/products/1")

    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Product deleted successfully",
        "data": None,
    }
    assert client.get("/api/products/1").status_code == 404


def test_create_product_then_read_it_back(client):
    response = client.post("/api/products", json=VALID_PRODUCT)

    assert response.status_code == 201
    body = response.get_json()
    assert body["message"] == "Product created successfully"
    assert body["data"]["id"] == 3

    saved = client.get("/api/products/3").get_json()["data"]
    assert saved["product_name"] == "Headset Gaming"
    assert saved["category"] == "Aksesoris"
    assert saved["quantity"] == 10


def test_update_product_then_read_it_back(client):
    response = client.put("/api/products/1", json=VALID_PRODUCT)

    assert response.status_code == 200
    assert response.get_json()["message"] == "Product updated successfully"

    saved = client.get("/api/products/1").get_json()["data"]
    assert saved["product_name"] == "Headset Gaming"
    assert saved["quantity"] == 10


@pytest.mark.parametrize("method", ["post", "put"])
@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"product_name": "   "}, "Nama barang wajib diisi"),
        ({"category": None}, "Kategori wajib diisi"),
        ({"quantity": "10"}, "Quantity harus berupa bilangan bulat"),
        ({"quantity": True}, "Quantity harus berupa bilangan bulat"),
        ({"quantity": -1}, "Quantity tidak boleh kurang dari 0"),
    ],
)
def test_invalid_product_is_rejected(client, method, change, message):
    send = request_for(client, method)

    response = send(json={**VALID_PRODUCT, **change})

    assert response.status_code == 400
    assert response.get_json() == {"message": message, "data": None}


@pytest.mark.parametrize("method", ["post", "put"])
def test_non_json_body_is_rejected(client, method):
    response = request_for(client, method)(data="bukan json")

    assert response.status_code == 400
    assert response.get_json() == {
        "message": "Request body harus berupa JSON object",
        "data": None,
    }


@pytest.mark.parametrize("method", ["post", "put"])
@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"product_name": "a" * 101}, "Nama barang maksimal 100 karakter"),
        ({"category": "a" * 101}, "Kategori maksimal 100 karakter"),
        ({"quantity": 2147483648}, "Quantity maksimal 2147483647"),
    ],
)
def test_value_above_limit_is_rejected(client, method, change, message):
    send = request_for(client, method)

    response = send(json={**VALID_PRODUCT, **change})

    assert response.status_code == 400
    assert response.get_json() == {"message": message, "data": None}


@pytest.mark.parametrize("method", ["post", "put"])
def test_values_at_limit_are_saved(client, method):
    product = {
        "product_name": "  " + "a" * 100 + "  ",
        "category": "b" * 100,
        "quantity": 2147483647,
    }

    response = request_for(client, method)(json=product)

    assert response.status_code in (200, 201)
    saved = response.get_json()["data"]
    assert saved["product_name"] == "a" * 100
    assert saved["category"] == "b" * 100
    assert saved["quantity"] == 2147483647


@pytest.fixture(params=[False, True], ids=["production", "debug"])
def error_client(client, request, monkeypatch):
    monkeypatch.setitem(client.application.config, "DEBUG", request.param)
    return client


def assert_json_error(response, status, message):
    assert response.status_code == status
    assert response.get_json() == {"message": message, "data": None}


@pytest.mark.parametrize("url", ["/api/tidak-ada", "/api/products/abc"])
def test_unknown_url_returns_json_404(error_client, url):
    response = error_client.get(url)

    assert_json_error(response, 404, "Endpoint tidak ditemukan")


def test_unsupported_method_returns_json_405(error_client):
    response = error_client.patch("/api/products/1", json=VALID_PRODUCT)

    assert_json_error(response, 405, "Metode HTTP tidak diizinkan")


def test_database_outage_returns_json_503(error_client, monkeypatch):
    monkeypatch.setenv("DB_PORT", "1")

    response = error_client.get("/api/products")

    assert_json_error(response, 503, "Database tidak tersedia")


def test_unexpected_failure_returns_json_500(error_client, products_table):
    with products_table.cursor() as cur:
        cur.execute("DROP TABLE products")

    response = error_client.get("/api/products")

    assert_json_error(response, 500, "Terjadi kesalahan pada server")
