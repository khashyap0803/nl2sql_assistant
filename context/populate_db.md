# populate_db.py - Database Population Script

## File Location
```
nl2sql_assistant/src/database/populate_db.py
```

## Purpose
This script creates and populates the database with sample sales data. It provides:
- Database and table creation
- Sample data generation (60 records)
- Verification of inserted data
- Progress output during execution

---

## When to Use

Run this script when:
1. Setting up a new installation
2. Resetting the database to initial state
3. Testing database connectivity

```bash
python src/database/populate_db.py
```

---

## What It Does

```
┌─────────────────────────────────────────────┐
│ 1. Drop existing 'sales' table (if exists)  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. Create 'sales' table with columns:       │
│    - id (SERIAL PRIMARY KEY)                │
│    - date (DATE)                            │
│    - amount (DECIMAL)                       │
│    - product (VARCHAR)                      │
│    - region (VARCHAR)                       │
│    - quantity (INTEGER)                     │
│    - customer_type (VARCHAR)                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 3. Create indexes on:                       │
│    - date, product, region, amount          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 4. Insert 60 sample sales records           │
│    - Q1 2025 (Jan-Mar)                      │
│    - 10 products × 4 regions                │
│    - 3 customer types                       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 5. Display summary statistics               │
│    - Total rows, sum, average               │
│    - By product, by region                  │
└─────────────────────────────────────────────┘
```

---

## Sample Data Generation

### Products (10 types):
| Product | Price Range (Rs) |
|---------|-----------------|
| Laptop | 1299 - 2199 |
| Desktop | 749 - 1249 |
| Monitor | 299 - 549 |
| Keyboard | 129 - 199 |
| Mouse | 59 - 109 |
| Headphones | 199 - 399 |
| Webcam | 119 - 229 |
| Tablet | 549 - 849 |
| Smartphone | 899 - 1499 |
| Router | 89 - 199 |

### Regions (4):
- North
- South
- East
- West

### Customer Types (3):
- Regular (standard consumers)
- Business (B2B customers)
- Premium (high-value customers)

---

## Output Example

```
================================================================================
  NL2SQL Voice Assistant - Database Setup
================================================================================

Connecting to database nl2sql_db...
[OK] Connected to database: nl2sql_db

Dropping existing sales table...
Creating sales table...
Creating indexes...
Inserting sample data...
[OK] Inserted 60 sales records

================================================================================
  DATABASE SUMMARY
================================================================================
Total Records: 60
Total Revenue: Rs 54,289.43
Average Sale: Rs 904.82

By Product:
  Laptop: 6 sales, Rs 10,099.93
  Smartphone: 6 sales, Rs 6,899.94
  Desktop: 6 sales, Rs 5,849.94
  ...

By Region:
  East: 15 sales, Rs 14,249.85
  North: 15 sales, Rs 13,549.86
  South: 15 sales, Rs 13,249.86
  West: 15 sales, Rs 13,239.86

[OK] Database setup complete!
```

---

## Alternative: schema.sql

This script is functionally equivalent to running:
```bash
psql -U postgres -d nl2sql_db -f src/database/schema.sql
```

Use populate_db.py when:
- You prefer Python over command line
- You want progress output
- You want to customize data programmatically

Use schema.sql when:
- You prefer SQL scripts
- You're using pgAdmin
- You want minimal dependencies

---

## File Relationships

```
populate_db.py
    │
    ├──> Uses: src/database/db_controller.py
    │
    ├──> Creates: PostgreSQL 'sales' table
    │
    ├──> Alternative to: src/database/schema.sql
    │
    └──> Imports from: config.py (DB credentials)
```
