import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, make_response
import google.generativeai as genai

app = Flask(__name__)
# Kunci rahasia session Flask
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cosmic-ai-secret-key-2026")

# Konfigurasi Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Konfigurasi Akses Kunci URL (Disesuaikan dengan link kamu)
ACCESS_KEY = os.environ.get("ACCESS_KEY", "dullahstudio_rahasia_2026")

@app.route('/')
def home():
    url_key = request.args.get('key')
    if url_key == ACCESS_KEY:
        session['unlocked'] = True
    
    is_unlocked = session.get('unlocked', False)
    return render_template('index.html', is_unlocked=is_unlocked)

@app.route('/logout-access')
def logout_access():
    session.pop('unlocked', None)
    return redirect(url_for('home'))

@app.route('/generate', methods=['POST'])
def generate():
    if not session.get('unlocked', False):
        return redirect(url_for('home'))
    
    content_type = request.form.get('content_type', 'general')
    topic = request.form.get('topic')
    duration = request.form.get('duration')
    language = request.form.get('language')
    audience = request.form.get('audience')
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if content_type == 'dracin':
            prompt = f"""
            Bertindaklah sebagai Head Writer Drama China (Dracin) miniseri vertikal yang sangat viral.
            Buatkan naskah drama pendek berdasarkan detail berikut:
            - Premis/Judul Cerita: {topic}
            - Durasi/Format: {duration}
            - Bahasa: {language}
            - Target Penonton: {audience}

            Keluarkan hasil dalam format JSON murni TANPA markdown block (tanpa ```json ... ```), dengan struktur persis seperti ini:
            {{
                "outline": {{
                    "sections": [
                        {{
                            "name": "Episode 1: Hook & Konflik Utama",
                            "approximate_duration": "0-60 detik",
                            "purpose": "Memancing emosi penonton di detik awal",
                            "key_points": ["Tokoh utama dihina", "Plot twist tersembunyi terungkap"],
                            "narrative_goal": "Membuat penonton penasaran setengah mati"
                        }}
                    ]
                }},
                "script": "Tulis naskah lengkap adegan demi adegan di sini (lengkap dengan nama karakter, dialog emosional, ekspresi, dan cliffhanger di akhir cerita)...",
                "metadata": {{
                    "hooks": [
                        {{"type": "Emotional Hook", "text": "Contoh kalimat pembuka emosional..."}},
                        {{"type": "Shocking Hook", "text": "Contoh kalimat pembuka penuh kejutan..."}}
                    ],
                    "titles": [
                        {{"title": "Judul Dracin Menarik 1", "angle": "Balas Dendam"}},
                        {{"title": "Judul Dracin Menarik 2", "angle": "CEO Menyamar"}}
                    ],
                    "description": "Deskripsi singkat untuk platform penayangan video pendek...",
                    "call_to_action": "Tonton kelanjutan episodenya dan klik tombol subscribe!"
                }}
            }}
            """
        else:
            prompt = f"""
            Bertindaklah sebagai Content Strategist dan Professional Scriptwriter.
            Buatkan skrip konten dan metadata lengkap berdasarkan detail berikut:
            - Topik: {topic}
            - Durasi: {duration}
            - Bahasa: {language}
            - Target Audience: {audience}

            Keluarkan hasil dalam format JSON murni TANPA markdown block (tanpa ```json ... ```), dengan struktur persis seperti ini:
            {{
                "outline": {{
                    "sections": [
                        {{
                            "name": "Pendahuluan / Hook",
                            "approximate_duration": "0-1 menit",
                            "purpose": "Menarik perhatian penonton",
                            "key_points": ["Pernyataan kontroversial atau masalah utama", "Janji solusi di video"],
                            "narrative_goal": "Retensi penonton tinggi di awal"
                        }}
                    ]
                }},
                "script": "Tulis naskah/narasi lengkap word-for-word di sini...",
                "metadata": {{
                    "hooks": [
                        {{"type": "Question", "text": "Pertanyaan pemancing rasa penasaran..."}},
                        {{"type": "Statistic", "text": "Fakta menarik atau angka mengejutkan..."}}
                    ],
                    "titles": [
                        {{"title": "Judul Video Menarik 1", "angle": "Rasa Penasaran"}},
                        {{"title": "Judul Video Menarik 2", "angle": "Solusi Instan"}}
                    ],
                    "description": "Deskripsi video yang ramah SEO...",
                    "call_to_action": "Jangan lupa like, comment, dan subscribe channel ini."
                }}
            }}
            """

        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        parsed_data = json.loads(raw_text)
        
        outline = parsed_data.get("outline", {})
        script = parsed_data.get("script", "")
        metadata = parsed_data.get("metadata", {})
        
    except Exception as e:
        outline = {"sections": [{"name": "Error", "purpose": str(e)}]}
        script = f"Terjadi kesalahan saat memproses data AI: {str(e)}"
        metadata = {"hooks": [], "titles": [], "description": "", "call_to_action": ""}

    return render_template(
        'result.html', 
        topic=topic, 
        duration=duration, 
        audience=audience, 
        language=language, 
        outline=outline, 
        script=script, 
        metadata=metadata
    )

if __name__ == '__main__':
    app.run(debug=True)