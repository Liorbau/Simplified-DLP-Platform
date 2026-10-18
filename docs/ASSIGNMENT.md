# DLP Full Stack Home Assignment – Simplified DLP Platform

> Verbatim transcription of [`DLP_Full_Stack_Assignment_Simplified.pdf`](DLP_Full_Stack_Assignment_Simplified.pdf). The PDF is the source of truth.
>
> Delivery notes from the accompanying email: deliverables must be on an accessible version-control platform and include all source code, a working `docker-compose.yml`, and a Postman collection (mandatory, overriding the "optional" note below). Due within 4 days of receipt.

## Overview

This assignment focuses on building a simple DLP backend application that allows managing inspection rules, grouping them into policies, and scanning text input to detect sensitive content.
The goal is to demonstrate clear backend design, correct logic implementation, and a basic understanding of API and data modeling.

## Objective

Implement a backend application that exposes HTTP APIs to:

- Manage Data Types (DTs)
- Manage Data Sets (DSs)
- Scan input text and return inspection results

## Architecture

The solution should be implemented as a single backend application, structured into three logical API modules:

- `/api/datatypes` – Data Types management
- `/api/datasets` – Data Sets management
- `/api/scan` – Scan endpoint

## Core Requirements

- A single backend service
- A single database
- CRUD operations for Data Types and Data Sets
- A synchronous scan endpoint returning immediate results

## Data Models

### Data Types (DTs)

Attributes:

- `id`: UUID (generated internally)
- `name`: STRING
- `description`: STRING
- `type`: ENUM (keywords only)
- `content`: STRING ARRAY
- `threshold`: NUMBER

At the moment, only keyword-based inspection is required.

### Data Sets (DSs)

Attributes:

- `id`: UUID (generated internally)
- `name`: STRING
- `data_type_ids`: ARRAY of DT UUIDs

## Scan Flow

1. Receive scan request (input text, Data Set ID)
2. Load Data Set
3. Load referenced Data Types
4. Execute scan logic
5. Return result

## Matching Logic

- Each Data Type evaluated independently
- Match if keyword count ≥ threshold
- Whole-word keyword matching
- OR logic across Data Types

## Scan Result Examples

Match:

```json
{
  "status": "match",
  "detected_objects": [
    {
      "id": "dt-uuid",
      "name": "Sensitive Keywords",
      "match_count": 3
    }
  ]
}
```

Not matched:

```json
{
  "status": "not matched"
}
```

## Optional (Nice to Have)

- Docker or docker-compose setup
- Basic input validation
- Clear project structure
- README explaining how to run the application
