import pytest
from playwright.sync_api import expect


@pytest.fixture
def inventory_page(page, live_server):
    page.goto(f"{live_server}/")
    return page


def product_row(page, name):
    return page.locator("#product-table tr", has_text=name)


def fill_product_form(page, name, category, quantity):
    page.get_by_label("Nama Barang").fill(name)
    page.get_by_label("Kategori").fill(category)
    page.get_by_label("Jumlah").fill(str(quantity))


def test_page_lists_products(inventory_page):
    expect(product_row(inventory_page, "Laptop Lenovo")).to_contain_text(
        "Elektronik"
    )
    expect(product_row(inventory_page, "Mouse Wireless")).to_contain_text(
        "Aksesoris"
    )


def test_user_can_add_product(inventory_page):
    fill_product_form(inventory_page, "Headset Gaming", "Aksesoris", 10)
    inventory_page.get_by_role("button", name="Simpan Barang").click()

    expect(inventory_page.locator("#message")).to_have_text(
        "Barang berhasil ditambahkan."
    )
    expect(product_row(inventory_page, "Headset Gaming")).to_contain_text("10")


def test_user_can_edit_product(inventory_page):
    row = product_row(inventory_page, "Mouse Wireless")
    row.get_by_role("button", name="Ubah").click()
    fill_product_form(inventory_page, "Mouse Gaming", "Aksesoris", 7)
    inventory_page.get_by_role("button", name="Perbarui Barang").click()

    expect(inventory_page.locator("#message")).to_have_text(
        "Data barang berhasil diperbarui."
    )
    expect(product_row(inventory_page, "Mouse Gaming")).to_contain_text("7")
    expect(product_row(inventory_page, "Mouse Wireless")).to_have_count(0)


def test_user_can_delete_product(inventory_page):
    inventory_page.on("dialog", lambda dialog: dialog.accept())

    row = product_row(inventory_page, "Laptop Lenovo")
    row.get_by_role("button", name="Hapus").click()

    expect(inventory_page.locator("#message")).to_have_text(
        "Barang berhasil dihapus."
    )
    expect(product_row(inventory_page, "Laptop Lenovo")).to_have_count(0)


def test_user_sees_server_validation_message(inventory_page):
    expect(product_row(inventory_page, "Laptop Lenovo")).to_be_visible()

    fill_product_form(inventory_page, "a" * 101, "Aksesoris", 1)
    inventory_page.get_by_role("button", name="Simpan Barang").click()

    expect(inventory_page.locator("#message")).to_have_text(
        "Nama barang maksimal 100 karakter"
    )


def test_user_sees_database_outage(page, live_server, monkeypatch):
    monkeypatch.setenv("DB_PORT", "1")

    page.goto(f"{live_server}/")

    expect(page.locator("#product-table")).to_contain_text(
        "Gagal mengambil data: Database tidak tersedia"
    )
