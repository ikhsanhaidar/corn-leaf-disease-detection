import os
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# ——— Konfigurasi dasar Flask ———
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # max 5MB
app.secret_key = "secret_key"

# ——— Pastikan folder uploads ada ———
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ——— Load model ———
MODEL_PATH = os.path.join(app.root_path, "Model", "Model_CNN_256px.keras")
model = load_model(MODEL_PATH)

# ——— Label kelas ———
class_labels = {0: "Bercak", 1: "Hawar", 2: "Karat", 3: "Sehat"}


# ——— Fungsi prediksi ———
def predict_image(model, img_path):
    img = image.load_img(img_path, target_size=(256, 256))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    preds = model.predict(img_array, verbose=0)
    idx = np.argmax(preds)

    return idx, preds[0]


# ——— Fungsi untuk sistem pakar berbasis aturan ———
def rule_based_system(
    humidity, season, temperature, plant_age, predicted_label, cnn_confidence
):
    """
    Inputs:
      - humidity: 'rendah'|'sedang'|'tinggi'
      - season: 'kemarau'|'peralihan'|'hujan'
      - temperature: 'rendah'|'normal'|'tinggi'
      - plant_age: '<30'|'30-60'|'>60'
      - predicted_label: string label dari CNN (mis. "Hawar")
      - cnn_confidence: float (0-100)

    Returns:
      - explanation: str (human readable reasons)
      - modifier: float (penyesuaian dalam persen, bisa negatif/positif, range recommended -40..+40)
      - expert_confidence: float (0-100) => cnn_confidence + modifier (clipped)
    """
    # normalisasi input (aman)
    humidity = (humidity or "").lower()
    season = (season or "").lower()
    temperature = (temperature or "").lower()
    plant_age = (plant_age or "").lower()
    label = (predicted_label or "").capitalize()

    reasons = []
    modifier = 0.0

    # RULES: general environment influence (affect all diseases mildly)
    if season == "hujan" and humidity == "tinggi":
        reasons.append(
            "Musim hujan & kelembaban tinggi — kondisi umum mendukung penyakit daun."
        )
        modifier += 8.0

    if season == "kemarau" and humidity == "rendah" and temperature == "tinggi":
        reasons.append(
            "Musim kemarau & kondisi kering/suhu tinggi — meningkatkan risiko bercak daun."
        )
        modifier += 6.0

    if season == "peralihan" and humidity in ("sedang", "tinggi"):
        reasons.append(
            "Musim peralihan dengan kelembaban sedang/tinggi — kondisi cocok untuk karat."
        )
        modifier += 5.0

    # RULES: berdasarkan predicted_label (stronger rules)
    if label == "Hawar":
        # hawar suka kelembaban tinggi + sedikit suhu rendah/normal
        if (
            season == "hujan"
            and humidity == "tinggi"
            and temperature in ("rendah", "normal")
        ):
            reasons.append(
                "Hawar: kelembaban tinggi + musim hujan mendukung perkembangan hawar."
            )
            modifier += 18.0
        if plant_age == "<30":
            reasons.append("Hawar: tanaman muda cenderung rentan terhadap hawar.")
            modifier += 8.0
        if temperature == "tinggi":
            reasons.append("Hawar: suhu tinggi sedikit mengurangi kondisi ideal hawar.")
            modifier -= 6.0

    if label == "Bercak":
        # bercak lebih mungkin di kondisi kering/panas dan tanaman stres
        if season == "kemarau" and humidity == "rendah" and temperature == "tinggi":
            reasons.append("Bercak: kondisi kemarau & panas mendukung bercak daun.")
            modifier += 18.0
        if plant_age == "<30":
            reasons.append("Bercak: tanaman muda bisa menunjukkan bercak saat stres.")
            modifier += 6.0
        if season == "hujan" and humidity == "tinggi":
            reasons.append(
                "Bercak: musim hujan dapat menurunkan kemungkinan bercak tipe kering."
            )
            modifier -= 8.0

    if label == "Karat":
        # karat berkembang di kelembaban sedang/tinggi tapi tidak selalu hujan deras
        if (
            season == "peralihan"
            and humidity in ("sedang", "tinggi")
            and temperature in ("normal", "rendah")
        ):
            reasons.append(
                "Karat: musim peralihan & kelembaban sedang/tinggi mendukung karat."
            )
            modifier += 16.0
        if plant_age == ">60":
            reasons.append("Karat: tanaman tua meningkatkan kerentanan karat.")
            modifier += 8.0
        if season == "kemarau" and humidity == "rendah":
            reasons.append("Karat: kondisi kering menurunkan kemungkinan karat.")
            modifier -= 12.0

    # small penalty if CNN confidence already high -> be conservative with overrides
    if cnn_confidence >= 85:
        reasons.append(
            "Confidence CNN sangat tinggi -> aturan pakar hanya memberi pengaruh kecil."
        )
        modifier *= 0.35  # kurangi pengaruh aturan jika CNN sudah kuat
    elif cnn_confidence >= 60:
        reasons.append("Confidence CNN moderat -> aturan pakar mempengaruhi sedang.")
        modifier *= 0.6
    else:
        reasons.append("Confidence CNN rendah -> aturan pakar mempengaruhi lebih kuat.")
        modifier *= 1.0

    # clip modifier to a reasonable range
    if modifier > 40:
        modifier = 40.0
    if modifier < -40:
        modifier = -40.0

    # compute expert_confidence (cnn_confidence + modifier) and clip 0..100
    expert_confidence = cnn_confidence + modifier
    expert_confidence = max(0.0, min(100.0, expert_confidence))

    # build explanation text
    explanation = "; ".join(reasons)

    return explanation, modifier, round(expert_confidence, 2)

# ——— Fungsi untuk rekomendasi penanganan berbasis IPM ———
def generate_recommendations(predicted_label, final_confidence, humidity, season, temperature, plant_age):
    """
    Fungsi untuk menghasilkan rekomendasi penanganan penyakit berbasis Integrated Pest Management (IPM)
    
    Parameters:
    - predicted_label: string ("Bercak", "Hawar", "Karat", "Sehat")
    - final_confidence: float (0-100)
    - humidity: string ('rendah'/'sedang'/'tinggi')
    - season: string ('kemarau'/'peralihan'/'hujan')
    - temperature: string ('rendah'/'normal'/'tinggi')
    - plant_age: string ('<30'/'30-60'/>'60')
    
    Returns:
    - dictionary berisi:
        - urgency_level: string ('rendah'/'sedang'/'tinggi')
        - actions: list of string (daftar tindakan)
        - environmental_notes: list of string (catatan lingkungan)
        - follow_up_advice: string (saran tindak lanjut)
    """
    
    # Normalisasi input
    predicted_label = predicted_label.capitalize()
    humidity = humidity.lower() if humidity else ''
    season = season.lower() if season else ''
    temperature = temperature.lower() if temperature else ''
    plant_age = plant_age.lower() if plant_age else ''
    
    # ===== 1. Tentukan Tingkat Urgensi Berdasarkan Confidence =====
    if final_confidence >= 80:
        urgency_level = "Tinggi"
        urgency_description = "Perlu penanganan segera"
    elif final_confidence >= 60:
        urgency_level = "Sedang"
        urgency_description = "Perlu penanganan dalam waktu dekat"
    else:
        urgency_level = "Rendah"
        urgency_description = "Monitoring rutin cukup"
    
    # ===== 2. Daftar Aksi Umum Berdasarkan Prinsip IPM =====
    ipm_general_actions = [
        "Monitoring tanaman secara rutin (minimal 2x seminggu)",
        "Pertahankan kebersihan kebun dari gulma dan sisa tanaman",
        "Gunakan varietas tahan penyakit jika tersedia",
        "Terapkan rotasi tanaman dengan tanaman non-serealia"
    ]
    
    # ===== 3. Rekomendasi Spesifik Berdasarkan Penyakit =====
    disease_specific_actions = []
    
    if predicted_label == "Bercak":
        disease_specific_actions = [
            "Sanitasi daun terinfeksi: petik dan buang daun yang sakit (bakar atau kubur)",
            "Tingkatkan sirkulasi udara dengan pengaturan jarak tanam optimal",
            "Kelola stres tanaman dengan irigasi teratur dan pemupukan berimbang",
            "Aplikasi agen hayati seperti Trichoderma spp. atau Bacillus subtilis",
            "Jika diperlukan, gunakan fungisida kontak berspektrum luas sebagai pilihan terakhir"
        ]
    
    elif predicted_label == "Hawar":
        disease_specific_actions = [
            "Sanitasi lahan: bersihkan sisa tanaman terinfeksi dari musim sebelumnya",
            "Perbaiki drainase untuk menghindari genangan air",
            "Kurangi kepadatan tanaman untuk meningkatkan aerasi",
            "Hindari penyiraman dari atas (overhead irrigation)",
            "Pemantauan intensif terutama pada musim hujan",
            "Pertimbangkan aplikasi fungisida pelindung pada fase rentan"
        ]
    
    elif predicted_label == "Karat":
        disease_specific_actions = [
            "Kurangi kelembaban mikro dengan pengaturan jarak tanam",
            "Kendalikan gulma inang alternatif di sekitar pertanaman",
            "Pantau daun muda yang lebih rentan terhadap infeksi",
            "Terapkan rotasi tanaman minimal 2-3 tahun dengan tanaman bukan jagung",
            "Pertimbangkan aplikasi fungisida sistemik pada fase awal infeksi"
        ]
    
    elif predicted_label == "Sehat":
        disease_specific_actions = [
            "Pertahankan praktik budidaya yang baik",
            "Lanjutkan pemantauan rutin setiap minggu",
            "Dokumentasikan kondisi tanaman untuk referensi",
            "Waspadai perubahan cuaca mendadak yang dapat memicu penyakit"
        ]
    
    # ===== 4. Catatan Tambahan Berdasarkan Kondisi Lingkungan =====
    environmental_notes = []
    
    # Catatan berdasarkan kelembaban
    if humidity == 'tinggi':
        environmental_notes.append("Kelembaban tinggi meningkatkan risiko penyakit jamur")
    elif humidity == 'rendah' and predicted_label != 'Bercak':
        environmental_notes.append("Kelembaban rendah mengurangi risiko penyakit jamur")
    
    # Catatan berdasarkan musim
    if season == 'hujan':
        environmental_notes.append("Musim hujan - periode kritis untuk penyakit daun")
    elif season == 'kemarau' and predicted_label == 'Bercak':
        environmental_notes.append("Kondisi kering dapat memicu bercak daun")
    
    # Catatan berdasarkan suhu
    if temperature == 'tinggi' and predicted_label in ['Hawar', 'Karat']:
        environmental_notes.append("Suhu tinggi dapat mempercepat perkembangan penyakit")
    elif temperature == 'rendah' and predicted_label == 'Bercak':
        environmental_notes.append("Suhu rendah mengurangi aktivitas patogen")
    
    # Catatan berdasarkan umur tanaman
    if plant_age == '<30':
        environmental_notes.append("Tanaman muda lebih rentan terhadap infeksi - perlu perhatian ekstra")
    elif plant_age == '>60' and predicted_label == 'Karat':
        environmental_notes.append("Tanaman tua rentan karat - fokus pada pencegahan penyebaran")
    
    # ===== 5. Saran Tindak Lanjut =====
    follow_up_advice = ""
    
    if predicted_label == "Sehat":
        follow_up_advice = (
            "Pertahankan kondisi baik tanaman. Lakukan pemantauan rutin dan "
            "waspadai perubahan cuaca yang dapat mempengaruhi kesehatan tanaman."
        )
    else:
        if urgency_level == "Tinggi":
            follow_up_advice = (
                "Evaluasi efektivitas tindakan dalam 7 hari. "
                "Jika gejala bertambah parah, konsultasikan dengan penyuluh pertanian setempat."
            )
        elif urgency_level == "Sedang":
            follow_up_advice = (
                "Pantau perkembangan penyakit dalam 10-14 hari. "
                "Dokumentasikan perubahan gejala untuk evaluasi."
            )
        else:
            follow_up_advice = (
                "Lanjutkan observasi selama 2-3 minggu. "
                "Catat perubahan untuk menentukan apakah penanganan lebih lanjut diperlukan."
            )
    
    # ===== 6. Gabungkan Semua Rekomendasi =====
    all_actions = ipm_general_actions + disease_specific_actions
    
    # Batasi jumlah aksi jika terlalu banyak (maks 8)
    if len(all_actions) > 8:
        all_actions = all_actions[:8]
    
    return {
        'urgency_level': urgency_level,
        'urgency_description': urgency_description,
        'actions': all_actions,
        'environmental_notes': environmental_notes,
        'follow_up_advice': follow_up_advice,
        'ipm_principles_applied': [
            "Pengendalian secara kultur teknis",
            "Pengendalian hayati",
            "Pengendalian kimiawi sebagai alternatif terakhir",
            "Monitoring dan evaluasi berkelanjutan"
        ]
    }


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # ===== 1. ambil input sistem pakar =====
        humidity = request.form.get("humidity")
        season = request.form.get("season")
        temperature = request.form.get("temperature")
        plant_age = request.form.get("plant_age")

        # ===== 2. ambil file gambar =====
        file = request.files["file"]
        filename = secure_filename(file.filename)
        image_path = os.path.join("static/uploads", filename)
        file.save(image_path)

        # ===== 3. preprocessing gambar =====
        img = image.load_img(image_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # ===== 4. PREDIKSI CNN =====
        preds = model.predict(img_array)
        probs = preds[0]
        idx = np.argmax(probs)
        predicted_label = class_labels[idx]

        probabilities = {
            class_labels[i]: round(float(probs[i]) * 100, 2)
            for i in range(len(class_labels))
        }

        # ===================================================
        # ===== 5. HYBRID: SISTEM PAKAR + FUSION (DI SINI) ===
        # ===================================================

        # confidence asli dari CNN
        cnn_confidence = round(float(probs[idx]) * 100, 2)

        # panggil sistem pakar
        explanation, modifier, expert_conf = rule_based_system(
            humidity,
            season,
            temperature,
            plant_age,
            predicted_label,
            cnn_confidence
        )

        # fusion CNN + expert
        w_cnn = 0.75
        w_expert = 0.25
        final_confidence = round(
            (w_cnn * cnn_confidence) + (w_expert * expert_conf), 2
        )

        final_confidence = max(0.0, min(100.0, final_confidence))

        full_explanation = (
            f"{explanation}. "
            f"CNN confidence: {cnn_confidence}%. "
            f"Expert adjustment: {modifier}%. "
            f"Expert confidence: {expert_conf}%."
        )

        # ===== BARU: GENERATE REKOMENDASI PENANGANAN =====
        recommendations = generate_recommendations(
            predicted_label=predicted_label,
            final_confidence=final_confidence,
            humidity=humidity,
            season=season,
            temperature=temperature,
            plant_age=plant_age
        )
        
        # ===== 6. kirim ke template =====
        return render_template(
            "index.html",
            image_path=image_path,
            predicted_label=predicted_label,
            probability=final_confidence,
            probabilities_dict=probabilities,
            explanation=full_explanation,
            cnn_confidence=cnn_confidence,
            expert_conf=expert_conf,
            modifier=modifier,
            # Data rekomendasi baru
            recommendations=recommendations,
            urgency_level=recommendations['urgency_level'],
            urgency_description=recommendations['urgency_description'],
            actions=recommendations['actions'],
            environmental_notes=recommendations['environmental_notes'],
            follow_up_advice=recommendations['follow_up_advice'],
            ipm_principles=recommendations['ipm_principles_applied']
        )

    # GET request
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
