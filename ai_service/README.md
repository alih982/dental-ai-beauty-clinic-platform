<div align="center">

# 🧠 AI Service — RAG-Powered Clinic Assistant

**FastAPI microservice that exposes a custom Retrieval-Augmented Generation (RAG) pipeline on top of the Dental & AI Beauty Clinic Platform.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

</div>

---

## 📖 Overview

This service is the **AI layer** of the clinic platform. It provides a context-aware assistant that answers patient and staff questions using a **RAG pipeline** over clinic-specific documents (dental guidelines, beauty treatment references, clinic FAQ).

It is intentionally decoupled from the Django core API:
- **Django** owns business data (users, appointments, orders).
- **FastAPI (this service)** owns the LLM, embeddings, retrieval, and evaluation.
- **PostgreSQL + pgvector** is the shared vector store.

This separation keeps the AI workload isolated — model inference and embedding generation never block transactional queries.

---

## 🏗️ Architecture

```mermaid
flowchart LR
    FE["🌐 Next.js Frontend"]
    API["🔌 FastAPI<br/>(this service)"]
    LLM["🧠 Gemma 2<br/>(Ollama / vLLM)"]
    EMB["📐 Embedding Model<br/>(multilingual)"]
    DB[("🗄️ PostgreSQL<br/>+ pgvector")]

    FE -->|POST /chat| API
    API -->|embed query| EMB
    API -->|similarity search| DB
    API -->|prompt + context| LLM
    LLM -->|answer| API
    API -->|JSON response| FE
