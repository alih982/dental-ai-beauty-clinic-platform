<div align="center">

# 🔌 Backend Core — Django REST API

**Django 5 + DRF backend that powers the Dental & AI Beauty Clinic Platform — appointments, beauty product store, dental records, e-prescriptions, and role-based access.**

[![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django)](https://djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-A30000)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)

</div>

---

## 📖 Overview

This is the **core backend** of the Dental & AI Beauty Clinic Platform. It owns all transactional business logic and data:

- **Appointments** — booking dental and beauty treatments with specialists
- **Beauty Product Store** — product catalog, cart, orders
- **E-Prescriptions** — issued by doctors, linked to patient records
- **Dental Records** — treatment history, charts, and photos
- **Users & Roles** — JWT-based auth with Role-Based Access Control (Admin / Doctor / Patient)

It is deliberately kept separate from the **AI service** (FastAPI):
- Django owns **business data and consistency**.
- FastAPI owns **LLM inference and retrieval**.
- The AI service uses its **own database** for embeddings and model artifacts — so training/embedding I/O never contends with transactional queries.

This is a **modular service architecture with independent Docker images**: each service (Django, FastAPI, frontend, Nginx) has its own Dockerfile and can be deployed independently, while sharing a PostgreSQL instance for transactional consistency.

---

## 🏗️ Architecture

```mermaid
flowchart LR
    FE["🌐 Next.js Frontend"]
    NG["🛡️ Nginx<br/>(reverse proxy)"]
    DJ["🔌 Django REST API<br/>(this service)"]
    AI["🧠 FastAPI AI Service"]
    DB[("🗄️ PostgreSQL<br/>(business data)")]
    AIDB[("📐 PostgreSQL + pgvector<br/>(AI service only)")]

    FE -->|HTTPS| NG
    NG -->|/api/*| DJ
    NG -->|/ai/*| AI
    DJ -->|ORM| DB
    AI -->|similarity search| AIDB
