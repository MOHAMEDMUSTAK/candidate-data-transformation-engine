# Candidate Data Transformation Engine

Eightfold AI - Production-grade multi-source candidate data transformation engine.

## Overview

This project is a powerful candidate data transformation engine designed to accept structured and unstructured candidate data from various sources (JSON, CSV, DOCX, TXT, PDF). It extracts information, normalizes values, canonicalizes fields, merges records, resolves conflicts deterministically, tracks provenance, and exports a clean, consolidated JSON record for each candidate.

The application consists of:
- **Backend**: A robust FastAPI application that handles the data processing pipeline.
- **Frontend**: A modern React/Vite web application that provides a user interface for uploading data, exploring conflicts, inspecting rules, and viewing the analytics pipeline.

## Features

- **Multi-Format Extraction**: Parses various file formats including structured (JSON, CSV) and unstructured (DOCX, PDF, TXT) data.
- **Normalization Pipeline**: Cleans and standardizes data such as dates, emails, locations, phone numbers, and skills.
- **Canonicalization**: Maps different naming conventions and synonymous terms into a single standard field schema.
- **Deterministic Conflict Resolution**: Employs robust rules and confidence scoring to resolve conflicting data from different sources when merging records.
- **Provenance Tracking**: Maintains a complete history of data transformations, allowing for explainability of every resolved field.
- **RESTful API**: Fast and scalable endpoints to interact with the transformation pipeline and fetch configurations.

## Architecture

The project is structured into two main directories:

- `backend/`: Contains the FastAPI application, data models, processing pipeline stages (extractors, normalizers, canonicalizer, merger, conflict resolver), routers, and utilities.
- `frontend/`: Contains the React/Vite frontend application (built with modern UI components like Tailwind/Radix UI).

## Prerequisites

- Python 3.9+
- Node.js 16+ & npm (or yarn/pnpm)

## Installation & Setup

### Backend (FastAPI)

1. Navigate to the root directory:
   ```bash
   cd candidate-data-transformation-engine
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   The backend API will be available at `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.

### Frontend (React / Vite)

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend application will be available at `http://localhost:5173` (or another port specified by Vite).

## Sample Inputs

Sample data files for testing the pipeline are provided in the `sample_inputs/` directory. These include mock ATS records, LinkedIn profile exports, recruiter CSVs, and unstructured recruiter notes.

## License

This project is licensed under the MIT License.
