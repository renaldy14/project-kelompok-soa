const API_URL = "/api/products";

const productForm = document.getElementById("product-form");
const productIdInput = document.getElementById("product-id");
const productNameInput = document.getElementById("product-name");
const categoryInput = document.getElementById("category");
const quantityInput = document.getElementById("quantity");

const productTable = document.getElementById("product-table");
const formTitle = document.getElementById("form-title");
const submitButton = document.getElementById("submit-button");
const cancelButton = document.getElementById("cancel-button");
const refreshButton = document.getElementById("refresh-button");
const messageBox = document.getElementById("message");

// Menampilkan pesan kepada pengguna
function showMessage(message, type = "success") {
  messageBox.textContent = message;
  messageBox.className = `message ${type}`;

  setTimeout(() => {
    messageBox.classList.add("hidden");
  }, 4000);
}

// Mengirim request ke REST API
async function requestAPI(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.message || "Terjadi kesalahan pada server");
  }

  return result;
}

// Mengambil dan menampilkan seluruh data barang
async function loadProducts() {
  productTable.innerHTML = "";

  const loadingRow = document.createElement("tr");
  const loadingCell = document.createElement("td");
  loadingCell.colSpan = 6;
  loadingCell.className = "empty-state";
  loadingCell.textContent = "Memuat data...";
  loadingRow.appendChild(loadingCell);
  productTable.appendChild(loadingRow);

  try {
    const products = await requestAPI(API_URL);

    productTable.innerHTML = "";

    if (products.length === 0) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 6;
      cell.className = "empty-state";
      cell.textContent = "Belum ada data barang.";
      row.appendChild(cell);
      productTable.appendChild(row);
      return;
    }

    products.forEach((product) => {
      const row = document.createElement("tr");

      const values = [
        product.id,
        product.product_name,
        product.category,
        product.quantity,
        formatDate(product.created_at),
      ];

      values.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value ?? "-";
        row.appendChild(cell);
      });

      const actionCell = document.createElement("td");
      actionCell.className = "actions";

      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "button edit";
      editButton.textContent = "Ubah";
      editButton.addEventListener("click", () => editProduct(product));

      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "button delete";
      deleteButton.textContent = "Hapus";
      deleteButton.addEventListener("click", () => deleteProduct(product.id));

      actionCell.append(editButton, deleteButton);
      row.appendChild(actionCell);

      productTable.appendChild(row);
    });
  } catch (error) {
    productTable.innerHTML = "";

    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.className = "empty-state";
    cell.textContent = "Gagal mengambil data: " + error.message;

    row.appendChild(cell);
    productTable.appendChild(row);
  }
}

// Format tanggal dari database
function formatDate(dateValue) {
  if (!dateValue) return "-";

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) return dateValue;

  return date.toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Menambahkan atau memperbarui barang
productForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const id = productIdInput.value;

  const productData = {
    product_name: productNameInput.value.trim(),
    category: categoryInput.value.trim(),
    quantity: Number(quantityInput.value),
  };

  if (
    !productData.product_name ||
    !productData.category ||
    !Number.isInteger(productData.quantity) ||
    productData.quantity < 0
  ) {
    showMessage("Periksa kembali data yang Anda masukkan.", "error");
    return;
  }

  try {
    if (id) {
      // UPDATE
      await requestAPI(`${API_URL}/${id}`, {
        method: "PUT",
        body: JSON.stringify(productData),
      });

      showMessage("Data barang berhasil diperbarui.");
    } else {
      // CREATE
      await requestAPI(API_URL, {
        method: "POST",
        body: JSON.stringify(productData),
      });

      showMessage("Barang berhasil ditambahkan.");
    }

    resetForm();
    await loadProducts();
  } catch (error) {
    showMessage(error.message, "error");
  }
});

// Mengisi form dengan data barang yang akan diedit
function editProduct(product) {
  productIdInput.value = product.id;
  productNameInput.value = product.product_name;
  categoryInput.value = product.category;
  quantityInput.value = product.quantity;

  formTitle.textContent = "Ubah Barang";
  submitButton.textContent = "Perbarui Barang";
  cancelButton.classList.remove("hidden");

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

// Menghapus barang
async function deleteProduct(id) {
  const confirmation = confirm("Apakah Anda yakin ingin menghapus barang ini?");

  if (!confirmation) return;

  try {
    await requestAPI(`${API_URL}/${id}`, {
      method: "DELETE",
    });

    showMessage("Barang berhasil dihapus.");
    await loadProducts();
  } catch (error) {
    showMessage(error.message, "error");
  }
}

// Mengosongkan form dan mengembalikan mode tambah
function resetForm() {
  productForm.reset();
  productIdInput.value = "";

  formTitle.textContent = "Tambah Barang";
  submitButton.textContent = "Simpan Barang";
  cancelButton.classList.add("hidden");
}

// Tombol batal mengubah data
cancelButton.addEventListener("click", resetForm);

// Tombol muat ulang data
refreshButton.addEventListener("click", loadProducts);

// Menampilkan data ketika halaman pertama kali dibuka
loadProducts();
