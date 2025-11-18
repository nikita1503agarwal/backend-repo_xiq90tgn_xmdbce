import os
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import create_document, get_documents, db
from schemas import Participant, PictureCard, VoiceNote, Thread, Attendance, Pitch, Selection, SessionTopic

app = FastAPI(title="LDI/SD Skill Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "LDI/SD API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Utility

def collection_name(model_cls) -> str:
    return model_cls.__name__.lower()

# Participant basic create/list
@app.post("/api/participants")
def create_participant(p: Participant):
    pid = create_document(collection_name(Participant), p)
    return {"id": pid}

@app.get("/api/participants")
def list_participants():
    docs = get_documents(collection_name(Participant))
    return docs

# Session topic create/list (to tag uploads automatically)
@app.post("/api/topics")
def create_topic(topic: SessionTopic):
    tid = create_document(collection_name(SessionTopic), topic)
    return {"id": tid}

@app.get("/api/topics")
def list_topics():
    return get_documents(collection_name(SessionTopic))

# Picture cards
@app.post("/api/picture-cards")
def upload_picture_card(data: PictureCard):
    doc_id = create_document(collection_name(PictureCard), data)
    return {"id": doc_id}

@app.get("/api/picture-cards")
def list_picture_cards(user_id: Optional[str] = None):
    flt = {"user_id": user_id} if user_id else {}
    return get_documents(collection_name(PictureCard), flt)

# Voice notes
@app.post("/api/voice-notes")
def upload_voice_note(data: VoiceNote):
    doc_id = create_document(collection_name(VoiceNote), data)
    return {"id": doc_id}

@app.get("/api/voice-notes")
def list_voice_notes(user_id: Optional[str] = None):
    flt = {"user_id": user_id} if user_id else {}
    return get_documents(collection_name(VoiceNote), flt)

# Threads
@app.post("/api/threads")
def create_thread(t: Thread):
    doc_id = create_document(collection_name(Thread), t)
    return {"id": doc_id}

@app.get("/api/threads")
def list_threads(user_id: Optional[str] = None, topic: Optional[str] = None):
    flt = {}
    if user_id: flt["user_id"] = user_id
    if topic: flt["topic"] = topic
    return get_documents(collection_name(Thread), flt)

# Attendance and Pitches
@app.post("/api/attendance")
def mark_attendance(a: Attendance):
    doc_id = create_document(collection_name(Attendance), a)
    return {"id": doc_id}

@app.get("/api/attendance")
def list_attendance(user_id: Optional[str] = None):
    flt = {"user_id": user_id} if user_id else {}
    return get_documents(collection_name(Attendance), flt)

@app.post("/api/pitches")
def create_pitch(p: Pitch):
    doc_id = create_document(collection_name(Pitch), p)
    return {"id": doc_id}

@app.get("/api/pitches")
def list_pitches(user_id: Optional[str] = None):
    flt = {"user_id": user_id} if user_id else {}
    return get_documents(collection_name(Pitch), flt)

@app.post("/api/selections")
def create_selection(s: Selection):
    doc_id = create_document(collection_name(Selection), s)
    return {"id": doc_id}

@app.get("/api/selections")
def list_selections(user_id: Optional[str] = None):
    flt = {"user_id": user_id} if user_id else {}
    return get_documents(collection_name(Selection), flt)

# Metrics aggregation (simple counts per participant)
@app.get("/api/metrics/{user_id}")
def get_metrics(user_id: str):
    def count(coll, flt=None):
        return db[coll].count_documents(flt or {})

    metrics = {
        "sessions_attended": count(collection_name(Attendance), {"user_id": user_id}),
        "pitches_attempted": count(collection_name(Pitch), {"user_id": user_id}),
        "sd_selected": count(collection_name(Selection), {"user_id": user_id, "status": "selected"}),
        "picture_cards": count(collection_name(PictureCard), {"user_id": user_id}),
        "voice_notes": count(collection_name(VoiceNote), {"user_id": user_id}),
        "thread_contributions": count(collection_name(Thread), {"user_id": user_id}),
    }

    # Week-to-week improvement graph proxy: count items per ISO week
    def weekly_counts(coll: str):
        docs = db[coll].find({"user_id": user_id}, {"created_at": 1})
        buckets = {}
        for d in docs:
            ts = d.get("created_at", datetime.utcnow())
            iso_year, iso_week, _ = ts.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            buckets[key] = buckets.get(key, 0) + 1
        # sort
        return [{"week": k, "count": buckets[k]} for k in sorted(buckets.keys())]

    metrics["weekly_progress"] = weekly_counts(collection_name(VoiceNote))
    return metrics

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
