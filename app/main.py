import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as PathParameter, status
from pydantic import BaseModel, ConfigDict, Field
import uvicorn

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "documents.db"))


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    name: str
    phone_name: list[str]
    location: str


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone_name TEXT NOT NULL,
                location TEXT NOT NULL
            )
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Document API",
    description="A small SQLite-backed document server.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post(
    "/documents",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
    summary="Create a document",
)
def create_document(document: Document) -> Document:
    try:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (id, name, phone_name, location)
                VALUES (?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.name,
                    json.dumps(document.phone_name),
                    document.location,
                ),
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document with id {document.id} already exists",
        ) from error
    return document


@app.get(
    "/document/{id}",
    response_model=Document,
    summary="Get a document by ID",
)
def get_document(
    document_id: Annotated[int, PathParameter(alias="id", ge=1)],
) -> Document:
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, phone_name, location FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} was not found",
        )

    return Document(
        id=row["id"],
        name=row["name"],
        phone_name=json.loads(row["phone_name"]),
        location=row["location"],
    )


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
