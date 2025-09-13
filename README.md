# AQMS FastAPI (MQTT → MySQL) + Maintenance History

### Jalankan lokal
```bash
python -m venv .venv && . .venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # isi kredensial
uvicorn app.main:app --host 0.0.0.0 --port 8000
