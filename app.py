from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json, os, threading, time
from dataclasses import dataclass, asdict

app = Flask(__name__)
app.secret_key = "stok123"  # untuk session flash

# ========== MODEL ==========
@dataclass
class Barang:
    id: str
    nama: str
    kategori: str
    harga: float
    stok: int


# ========== DATABASE SEDERHANA ==========
DATABASE_FILE = "data_barang.json"
BACKUP_FILE = "backup_barang.json"

def load_data():
    if not os.path.exists(DATABASE_FILE):
        return []
    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        return [Barang(**b) for b in json.load(f)]

def save_data(data):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(b) for b in data], f, indent=2, ensure_ascii=False)


# ========== BACKUP SERVICE (THREAD TERPISAH) ==========
def backup_service(interval=10):
    """Backup otomatis tiap interval detik"""
    while True:
        try:
            if os.path.exists(DATABASE_FILE):
                with open(DATABASE_FILE, "r", encoding="utf-8") as src, open(BACKUP_FILE, "w", encoding="utf-8") as dst:
                    data = json.load(src)
                    json.dump({
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "jumlah_barang": len(data),
                        "barang": data
                    }, dst, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[BackupService] Error: {e}")
        time.sleep(interval)

threading.Thread(target=backup_service, daemon=True).start()


# ========== ROUTES ==========
@app.route("/")
def index():
    barang = load_data()
    total_stok = sum(b.stok for b in barang)
    total_nilai = sum(b.stok * b.harga for b in barang)
    return render_template("index.html", barang=barang, total_stok=total_stok, total_nilai=total_nilai)


@app.route("/add", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        data = load_data()
        id_ = request.form["id"]
        nama = request.form["nama"]
        kategori = request.form["kategori"]
        harga = float(request.form["harga"])
        stok = int(request.form["stok"])

        if any(b.id == id_ for b in data):
            flash("ID barang sudah ada!", "danger")
            return redirect(url_for("add_item"))

        data.append(Barang(id_, nama, kategori, harga, stok))
        save_data(data)
        flash("Barang berhasil ditambahkan!", "success")
        return redirect(url_for("index"))
    return render_template("add_item.html")


@app.route("/sell/<id>", methods=["POST"])
def sell_item(id):
    qty = int(request.form["qty"])
    data = load_data()
    for b in data:
        if b.id == id:
            if b.stok >= qty:
                b.stok -= qty
                save_data(data)
                flash(f"Berhasil menjual {qty} unit dari {b.nama}", "success")
            else:
                flash("Stok tidak cukup!", "danger")
            break
    return redirect(url_for("index"))


@app.route("/restock/<id>", methods=["POST"])
def restock_item(id):
    qty = int(request.form["qty"])
    data = load_data()
    for b in data:
        if b.id == id:
            b.stok += qty
            save_data(data)
            flash(f"Berhasil menambah stok {qty} unit untuk {b.nama}", "info")
            break
    return redirect(url_for("index"))


@app.route("/search", methods=["GET", "POST"])
def search():
    result = []
    query = ""
    if request.method == "POST":
        query = request.form["query"].lower()
        data = load_data()
        result = [b for b in data if query in b.nama.lower() or query in b.kategori.lower() or query in b.id.lower()]
    return render_template("search.html", result=result, query=query)


@app.route("/api/barang")
def api_barang():
    data = load_data()
    return jsonify([asdict(b) for b in data])


# ========== JALANKAN ==========
# untuk vercel
app.run = lambda *args, **kwargs: None
# if __name__ == "__main__":
#     if not os.path.exists(DATABASE_FILE):
#         # generate 20 sample barang
#         sample = [Barang(f"BRG{i:03d}", f"Produk-{i}", "umum", 10000 + i * 500, 10 + i) for i in range(1, 21)]
#         save_data(sample)
#     app.run(debug=True)
if __name__ == "__main__":
    app.run(debug=True)



