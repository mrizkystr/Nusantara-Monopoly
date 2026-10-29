# Nusantara Property Tycoon

**Nusantara Property Tycoon** adalah permainan papan strategi perdagangan dan pengelolaan properti kasual klasik bertema kota-kota dan ikon ekonomi Indonesia. Dibangun menggunakan Python dan Pygame, game ini mendukung multipemain lokal (*pass-and-play*) untuk 2 hingga 4 pemain pada satu komputer desktop (Windows dan Linux).

Game ini terinspirasi dari mekanik klasik Monopoli dengan sentuhan modern, menyajikan antarmuka visual khas Nusantara yang elegan, pion vektor kultural orisinal, efek suara prosedural dan musik gamelan pentatonik yang menenangkan, serta sistem animasi yang mulus.

---

## 🌟 Fitur Utama Permainan

### 1. Papan Monopoli Nusantara 40 Petak Lengkap
- **8 Kelompok Warna Kota**:
  - Cokelat: Bogor, Depok
  - Biru Muda: Tangerang, Bekasi, Cirebon
  - Merah Muda: Bandung, Cimahi, Garut
  - Oranye: Semarang, Solo, Yogyakarta
  - Merah: Surabaya, Malang, Sidoarjo
  - Kuning: Denpasar, Singaraja, Mataram
  - Hijau: Balikpapan, Samarinda, Pontianak
  - Biru Tua: Medan, Makassar
- **4 Petak Sudut Tradisional**: **MULAI** (gaji Rp2.000.000), **PENJARA / KUNJUNGAN**, **PARKIR GRATIS**, dan **MASUK PENJARA**.
- **4 Stasiun Kereta Api Nusantara**: Stasiun Gambir, Stasiun Bandung, Stasiun Surabaya Gubeng, dan Stasiun Medan (sewa progresif Rp250.000 – Rp2.000.000).
- **2 Utilitas Nasional**: Perusahaan Listrik (PLN) dan Perusahaan Air (PDAM) dengan pengali lemparan dadu (4x / 10x).
- **Petak Pajak**: Pajak Penghasilan (Rp2.000.000) dan Pajak Kekayaan (Rp1.000.000).

### 2. Pion Vektor Kultural Asli Indonesia (*Original Vector Tokens*)
Enam pion vektor orisinal yang digambar secara prosedural dengan geometri bersih beresolusi tinggi dan cincin cahaya (*active player glow*):
1. **Monas**: Ikon Monumen Nasional Jakarta dengan cawan dan lidah api emas kemerdekaan.
2. **Becak**: Kendaraan roda tiga tradisional khas Nusantara.
3. **Angkot**: Angkutan kota ikonik dengan siluet khas perkotaan.
4. **Kapal Pinisi**: Perahu layar tradisional legendaris suku Bugis-Makassar.
5. **Wayang**: Siluet wayang kulit tradisional Jawa yang anggun.
6. **Komodo**: Siluet fauna purba reptil raksasa endemik Nusa Tenggara Timur.

### 3. Sistem Desain Visual & Antarmuka Modern
- **Palet Warna Modern Bertema Nusantara**:
  - Latar Belakang: `#14202B` (Biru Tua Maritim)
  - Permukaan Panel: `#203241` & `#2B4050`
  - Aksen Utama: `#E8B86D` (Emas Nusantara)
  - Aksen Sekunder: `#5FB3A2` (Toska Laut Tropis)
  - Teks Utama & Sekunder: `#F8F5EE` & `#B8C6CC`
  - Status Bahaya / Pailit: `#D96C6C`
  - Status Sukses / Keuntungan: `#65BD8B`
- **Ornamen Geometris Batik**: Latar belakang menu utama dihiasi motif intan belah ketupat khas tenun dan batik Nusantara.
- **Kartu Sertifikat Tanah Interaktif (*Property Inspection Modal*)**: Klik sembarang petak properti di papan kapan saja untuk melihat sertifikat tanah, nama pemilik, status hipotek, harga beli, biaya bangunan, dan rincian lengkap uang sewa dari rumah 1–4 hingga hotel.
- **Papan Teroptimasi 60 FPS**: Latar belakang papan 40 petak di-*render* ke dalam *cached surface* terpisah sehingga beban GPU/CPU sangat ringan dan stabil pada 60 FPS.

### 4. Sistem Animasi & Efek Visual Dinamis
- **Animasi Lemparan Dadu 3D Berguling (*Dice Animation*)**: Menampilkan animasi dadu berputar dengan mata dadu acak selama jeda waktu (*delta-time*) dan mendarat sesuai nilai acak hasil lemparan mesin game.
- **Animasi Pergerakan Pion Langkah demi Langkah (*Movement Animation*)**: Pion melangkah mulus petak demi petak mengelilingi papan dengan efek suara langkah, indikator sisa langkah, dan dapat dilewati seketika menggunakan tombol **Spasi**.
- **Notifikasi Transaksi Melayang (*Floating Toast Notifications*)**: Setiap transaksi uang (gaji MULAI, bayar sewa, beli tanah, dividen kartu) memunculkan teks notifikasi melayang dengan animasi memudar (*fade-out*) di tengah papan.

### 5. Mesin Audio Prosedural & Musik Gamelan
- **Sintesis Audio Prosedural**: Seluruh berkas audio format 16-bit 44.1kHz PCM WAV di-*generate* secara murni oleh modul Python bawaan (`wave` dan `struct`) tanpa memerlukan unduhan berkas eksternal atau dependensi pihak ketiga.
- **12 Efek Suara (SFX)**:
  - `click`: Suara klik tombol responsif
  - `dice_roll` & `dice_land`: Suara putaran dan pendaratan dadu
  - `step`: Suara langkah pion pada petak papan
  - `buy` & `rent`: Suara transaksi uang masuk dan keluar
  - `card`: Suara pengambilan kartu kesempatan/dana umum
  - `build_house` & `build_hotel`: Suara palu konstruksi dan arpeggio megah
  - `jail`: Suara dentang jeruji besi
  - `bankruptcy`: Suara penurunan nada pailit
  - `victory`: Melodi pentatonik perayaan kemenangan
- **Musik Latar Belakang (BGM)**: Instrumen lonceng pentatonik terinspirasi laras gamelan Jawa/Bali yang menenangkan (*ambient loop*).
- **Dukungan Audio Aman**: Dilengkapi *fallback* otomatis tanpa *crash* apabila perangkat sistem tidak memiliki kartu suara.

### 6. Layar Pengaturan & Kustomisasi Lengkap
- Kontrol Volume Master (0–100%)
- Kontrol Volume Musik Latar (0–100%)
- Kontrol Volume Efek Suara (0–100%)
- Sakelar Bisu (*Mute Toggle*)
- Pilihan Kecepatan Animasi: **Normal**, **Cepat**, atau **Instan**
- Sakelar Lewati Animasi Gerak (*Skip Movement*)
- Sakelar Mode Layar Penuh (*Fullscreen Toggle*)
- Konfigurasi tersimpan otomatis ke `data/settings.json`.

### 7. Panduan Lengkap Cara Bermain (11 Halaman)
Layar panduan interaktif berbahasa Indonesia dengan navigasi halaman:
1. Tujuan Permainan
2. Pergerakan & Dadu
3. Pembelian & Lelang Properti
4. Uang Sewa & Monopoli
5. Pembangunan Rumah
6. Pembangunan Hotel
7. Kartu Dana Umum & Kesempatan
8. Aturan Masuk & Keluar Penjara
9. Menggadaikan Properti
10. Penyelesaian Utang & Pailit
11. Kondisi Kemenangan

---

## 🛠️ Arsitektur & Struktur Proyek

```
Nusantara-Monopoly/
├── main.py                     # Entry point aplikasi, event loop, dan delta-time clock
├── requirements.txt            # Dependensi (pygame>=2.5.0)
├── README.md                   # Dokumentasi lengkap proyek
├── data/
│   ├── board.json              # Definisi 40 petak papan Nusantara dan tabel sewa
│   ├── cards.json              # 32 kartu Dana Umum & Kesempatan bertema Indonesia
│   └── settings.json           # Berkas konfigurasi pengaturan pemain
├── assets/
│   ├── audio/
│   │   ├── music/              # Musik latar ambient loop (WAV)
│   │   └── sfx/                # 12 efek suara prosedural (WAV)
│   └── fonts/                  # Direktori font sistem
├── game/
│   ├── __init__.py
│   ├── state.py                # Enum GameState, TileType, PropertyColorGroup
│   ├── player.py               # Model pemain, kekayaan bersih, dan tipe pion
│   ├── property.py             # Model petak, hak milik, dan rumah/hotel
│   ├── board.py                # Loader data papan dan validasi 40 petak
│   ├── dice.py                 # Dadu 2d6 dan pelacak dadu kembar berturut-turut
│   ├── economy.py              # Perhitungan sewa, inventaris bank, dan format Rupiah
│   ├── cards.py                # Dek kartu Kesempatan & Dana Umum
│   ├── auction.py              # Mekanisme lelang publik bergiliran
│   ├── trading.py              # Penawaran dan negosiasi tukar-menukar properti
│   ├── save_manager.py         # Penyimpanan dan pemuatan game atomik
│   ├── settings.py             # Model pengaturan dan persistensi JSON
│   └── engine.py               # Mesin pengatur aturan otoritatif & pergerakan tertunda
├── ui/
│   ├── __init__.py
│   ├── audio.py                # Generator WAV prosedural & AudioManager
│   ├── tokens.py               # TokenRenderer untuk 6 pion kultural Nusantara
│   ├── animation.py            # DiceAnimation, MovementAnimation, & ToastManager
│   ├── components.py           # Widget UI Button, Panel, dan Font Cache
│   ├── renderer.py             # BoardRenderer, caching papan statis, & HUD bilah sisi
│   ├── screens.py              # MainMenu, Setup, Settings, Rules, & GamePlayScreen
│   └── input_handler.py        # Pengarah input, pintasan global, & resize window
└── tests/
    ├── test_game_core.py       # 29 unit tests logika aturan, sewa, lelang, & kartu
    ├── test_ui_flow.py         # 3 integration tests antarmuka & modal
    ├── test_full_game_simulation.py  # 1 simulasi penuh 2.000 aksi permainan
    └── test_step2_features.py  # 10 tests fitur Step 2 (audio, animasi, token, settings)
```

---

## 🚀 Kebutuhan Sistem & Instalasi

### Kebutuhan:
- **Python**: 3.11 atau lebih baru
- **Pygame**: 2.5 atau lebih baru
- **Sistem Operasi**: Linux, Windows, atau macOS

### Langkah Instalasi:

1. **Masuk ke direktori proyek**:
   ```bash
   cd /home/rezzypu/belajar/Nusantara-Monopoly
   ```

2. **Buat dan aktifkan lingkungan virtual (opsional tapi disarankan)**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Untuk Linux / macOS
   # .venv\Scripts\activate   # Untuk Windows
   ```

3. **Pasang dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 Cara Menjalankan & Memainkan Game

Jalankan perintah berikut pada terminal:
```bash
python3 main.py
```

### Navigasi Menu Utama:
- **MAIN BARU**: Pilih jumlah pemain (2–4), ketik nama, pilih jenis pion kultural dan warna, lalu mulai bertanding.
- **LANJUTKAN PERMAINAN**: Memuat permainan terakhir yang tersimpan dari `saves/autosave.json`.
- **CARA BERMAIN**: Membuka buku panduan interaktif 11 halaman.
- **PENGATURAN**: Mengatur volume suara/musik, bisu, kecepatan animasi, lewati gerak, dan layar penuh.
- **KELUAR**: Menutup permainan.

### ⌨️ Tombol Pintasan & Navigasi (*Hotkeys*):
- **Mouse Klik Kiri**: Memilih menu, menekan tombol aksi, menawar lelang, membeli petak, membangun rumah/hotel, menggadaikan aset, atau mengklik petak untuk melihat Sertifikat Tanah.
- **Spasi (*Spacebar*)**: Mengocok dadu pada giliran berjalan / Melewati animasi langkah pion seketika.
- **Esc (*Escape*)**: Menutup modal yang sedang terbuka / Keluar dari tampilan Sertifikat Tanah.
- **M**: Sakelar cepat untuk membisukan (*Mute*) atau menyalakan kembali seluruh suara permainan.
- **F11**: Mengalihkan mode Layar Penuh (*Toggle Fullscreen*).

---

## 🧪 Pengujian Otomatis (*Automated Tests*)

Seluruh pengujian unit, integrasi, simulasi bot, dan fitur visual dapat dijalankan tanpa membutuhkan layar fisik (*headless*):

```bash
# Menjalankan seluruh pengujian (43 tests)
python3 -m unittest discover -s tests -p "test_*.py"
```

Semua 43 pengujian mencakup:
- Validasi 40 petak papan dan konsistensi data harga properti.
- Algoritma sewa tanah, kelipatan sewa monopoli kelompok warna, sewa bertingkat stasiun kereta api, dan utilitas PLN/PDAM.
- Sistem inventaris Bank untuk pembatasan 32 rumah dan 12 hotel serta aturan pembangunan merata.
- Mekanik lelang publik bertahap dan transfer kepemilikan.
- Mekanik keluar-masuk penjara (penebusan Rp500.000, kartu bebas penjara, dan 3x lemparan dadu).
- Dek kartu Kesempatan dan Dana Umum (siklus kartu, kartu tahanan, dan aksi kartu).
- Resolusi utang antar pemain atau ke bank, serta penyerahan aset saat pailit.
- Penyimpanan dan pemuatan game (*atomic save/load*).
- Simulasi permainan komprehensif 2.000 aksi tanpa mengalami *deadlock*.
- Sintesis audio WAV dan pengujian volume `AudioManager`.
- *Rendering* 6 pion kultural vektor (Monas, Becak, Angkot, Kapal Pinisi, Wayang, Komodo).
- Sistem animasi dadu (*DiceAnimation*), langkah pion (*MovementAnimation*), dan notifikasi melayang (*ToastManager*).
- Deteksi koordinat klik petak papan (*tile hit-testing*).
- Persistensi pengaturan pemain pada berkas JSON.

---

## 📄 Lisensi & Hak Cipta

Game ini dibuat sebagai karya independen bertema budaya dan perekonomian Indonesia. Seluruh nama petak kota, desain visual vektor pion, ilustrasi antarmuka, tata letak, dan berkas audio disintesis secara orisinal dan bebas dari aset berhak cipta.
