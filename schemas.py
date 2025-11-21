"""
Database Schemas for Religious Education App

Each Pydantic model represents a collection in MongoDB. The collection name
is the lowercase class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class Material(BaseModel):
    """Collection: material"""
    title: str = Field(..., description="Judul materi")
    content: str = Field(..., description="Isi materi (teks panjang)")
    category: Optional[str] = Field(None, description="Kategori materi")
    thumbnail_url: Optional[str] = Field(None, description="URL thumbnail (opsional)")


class Video(BaseModel):
    """Collection: video"""
    title: str = Field(..., description="Judul video")
    url: str = Field(..., description="URL video YouTube/Vimeo/MP4")
    description: Optional[str] = Field(None, description="Deskripsi singkat")


class Photo(BaseModel):
    """Collection: photo"""
    title: str = Field(..., description="Judul foto")
    image_url: str = Field(..., description="URL gambar")
    caption: Optional[str] = Field(None, description="Keterangan foto")


class Quiz(BaseModel):
    """Collection: quiz"""
    title: str = Field(..., description="Judul kuis")
    description: Optional[str] = Field(None, description="Deskripsi kuis")


class Question(BaseModel):
    """Collection: question"""
    quiz_id: str = Field(..., description="ID kuis terkait (string ObjectId)")
    text: str = Field(..., description="Teks pertanyaan")
    options: List[str] = Field(..., min_items=2, description="Pilihan jawaban")
    correct_index: int = Field(..., ge=0, description="Index jawaban benar dalam options")


class Submission(BaseModel):
    """Body untuk submit jawaban kuis"""
    answers: List[int] = Field(..., description="Daftar index jawaban untuk tiap pertanyaan berurutan")
