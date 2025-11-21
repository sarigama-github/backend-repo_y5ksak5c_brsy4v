import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Material, Video, Photo, Quiz, Question, Submission

app = FastAPI(title="Religious Education API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "secret-admin-token")


# -------- Root & Health --------
@app.get("/")
def read_root():
    return {"message": "Backend siap digunakan"}


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
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# -------- Auth --------
class LoginBody(BaseModel):
    password: str


def require_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.post("/auth/login")
def login(body: LoginBody):
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Password salah")
    return {"token": ADMIN_TOKEN}


# -------- Helpers --------
class IdModel(BaseModel):
    id: str


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="ID tidak valid")


# -------- Materials --------
@app.post("/materials")
def create_material(material: Material, _: bool = Depends(require_admin)):
    inserted_id = create_document("material", material)
    return {"id": inserted_id}


@app.get("/materials")
def list_materials(limit: Optional[int] = 50):
    docs = get_documents("material", limit=limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.put("/materials/{material_id}")
def update_material(material_id: str, material: Material, _: bool = Depends(require_admin)):
    mid = to_object_id(material_id)
    res = db["material"].update_one({"_id": mid}, {"$set": material.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan")
    return {"updated": True}


# -------- Videos --------
@app.post("/videos")
def create_video(video: Video, _: bool = Depends(require_admin)):
    inserted_id = create_document("video", video)
    return {"id": inserted_id}


@app.get("/videos")
def list_videos(limit: Optional[int] = 50):
    docs = get_documents("video", limit=limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -------- Photos --------
@app.post("/photos")
def create_photo(photo: Photo, _: bool = Depends(require_admin)):
    inserted_id = create_document("photo", photo)
    return {"id": inserted_id}


@app.get("/photos")
def list_photos(limit: Optional[int] = 50):
    docs = get_documents("photo", limit=limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -------- Quizzes & Questions --------
@app.post("/quizzes")
def create_quiz(quiz: Quiz, _: bool = Depends(require_admin)):
    inserted_id = create_document("quiz", quiz)
    return {"id": inserted_id}


@app.get("/quizzes")
def list_quizzes(limit: Optional[int] = 50):
    docs = get_documents("quiz", limit=limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.put("/quizzes/{quiz_id}")
def update_quiz(quiz_id: str, quiz: Quiz, _: bool = Depends(require_admin)):
    qid = to_object_id(quiz_id)
    res = db["quiz"].update_one({"_id": qid}, {"$set": quiz.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan")
    return {"updated": True}


@app.post("/questions")
def create_question(question: Question, _: bool = Depends(require_admin)):
    # validate quiz id format
    _ = to_object_id(question.quiz_id)
    inserted_id = create_document("question", question)
    return {"id": inserted_id}


@app.get("/quizzes/{quiz_id}/questions")
def list_questions(quiz_id: str):
    _ = to_object_id(quiz_id)
    docs = get_documents("question", {"quiz_id": quiz_id})
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.put("/questions/{question_id}")
def update_question(question_id: str, question: Question, _: bool = Depends(require_admin)):
    qoid = to_object_id(question_id)
    res = db["question"].update_one({"_id": qoid}, {"$set": question.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan")
    return {"updated": True}


@app.post("/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: str, submission: Submission):
    # Ambil semua pertanyaan kuis
    questions = get_documents("question", {"quiz_id": quiz_id})
    if not questions:
        raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan")

    if len(submission.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Jumlah jawaban tidak sesuai")

    total = len(questions)
    correct = 0
    results = []

    for idx, q in enumerate(questions):
        is_correct = int(submission.answers[idx]) == int(q.get("correct_index", -1))
        correct += 1 if is_correct else 0
        results.append({
            "question": q.get("text"),
            "your_answer": submission.answers[idx],
            "correct_answer": q.get("correct_index"),
            "is_correct": is_correct,
            "options": q.get("options", [])
        })

    score = round((correct / total) * 100, 2)

    # Simpan hasil submission (opsional)
    create_document("submission", {
        "quiz_id": quiz_id,
        "answers": submission.answers,
        "score": score,
        "correct": correct,
        "total": total
    })

    return {"score": score, "correct": correct, "total": total, "results": results}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
