---
date: "D:20260413043931+05'00'"
source: "18_nested_tables.pdf"
pages: 2
---

## Multiple Tables

#### Data Team

#### April 13, 2026

### 1 Server Configuration

Table 1: Production Servers

Server CPU Cores RAM (GB) Role
web-01

8

32 Load Balancer

web-02

16

64 Application

web-03

16

64 Application

db-01

32

128 Primary DB

db-02

32

128 Replica DB

cache-01

8

64 Redis Cache

### 2 API Endpoints

Table 2: REST API Routes

Method Path

Description Auth

POST /api/upload

Upload PDF file API Key

GET /api/jobs/{id}/status Check job status API Key
GET /api/jobs/{id}/result Download result API Key
GET /api/health

Health check None

DELETE /api/jobs/{id}

Cancel job

API Key

### 3 Performance Metrics


Table 3: Conversion Benchmarks by Document Type
Document Type Pages Time (s) Blocks Score
Simple Article

2

0.3 12 98%

Technical Report

15

2.1 89 95%

Academic Paper

10

1.8 67 93%

Financial Report

30

4.5 203 91%

User Manual

50

7.2 412 89%
