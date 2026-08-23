# DPWH Verify database ERD

The existing `VerificationReport` model is the implementation of the logical
`InspectionReport` entity. Its original name is retained so existing routes,
templates, migrations, and database records continue to work.

```mermaid
erDiagram
    USER ||--o| INSPECTOR : "has profile"
    USER ||--o{ VERIFICATION_REPORT : reviews
    USER ||--o{ AUDIT_LOG : performs
    INSPECTOR ||--o{ PROJECT_ASSIGNMENT : receives
    PROJECT ||--o{ PROJECT_ASSIGNMENT : has
    INSPECTOR ||--o{ VERIFICATION_REPORT : submits
    PROJECT ||--o{ VERIFICATION_REPORT : contains
    VERIFICATION_REPORT ||--o{ INSPECTION_IMAGE : includes
    INSPECTION_IMAGE ||--o| BLOCKCHAIN_RECORD : anchors

    USER {
        bigint id PK
        string username
        string email
        boolean is_staff
    }
    INSPECTOR {
        bigint id PK
        bigint user_id FK
        string employee_id
        string district
        boolean is_active
        datetime date_registered
    }
    PROJECT {
        bigint id PK
        string project_name
        decimal latitude
        decimal longitude
        decimal geofence_radius
        decimal progress_percentage
        string status
    }
    PROJECT_ASSIGNMENT {
        bigint id PK
        bigint project_id FK
        bigint inspector_id FK
        datetime assigned_date
    }
    VERIFICATION_REPORT {
        bigint id PK
        bigint project_id FK
        bigint inspector_id FK
        decimal progress_percentage
        text accomplishment_description
        string status
        datetime submitted_at
        bigint reviewed_by_id FK
        datetime reviewed_at
        text review_notes
    }
    INSPECTION_IMAGE {
        bigint id PK
        bigint report_id FK
        string image_file
        string sha256_hash
        string perceptual_hash
        decimal latitude
        decimal longitude
        decimal altitude
        decimal gps_accuracy
        datetime captured_at
        decimal geofence_distance
        string geofence_status
        bigint file_size
        string mime_type
    }
    BLOCKCHAIN_RECORD {
        bigint id PK
        bigint inspection_image_id FK
        string transaction_id
        bigint block_number
        string chaincode_name
        string commit_status
        datetime committed_at
        json metadata_json
        text error_message
    }
    AUDIT_LOG {
        bigint id PK
        bigint user_id FK
        string action_type
        string target_entity
        bigint target_id
        string ip_address
        string device_info
        datetime timestamp
    }
```

## Storage boundary

- PostgreSQL stores users, projects, reports, image metadata, audit events, and a
  local copy of each Fabric transaction receipt.
- Uploaded image files are stored off-chain under `MEDIA_ROOT` (or a future
  object-storage service).
- Hyperledger Fabric will store lightweight verification metadata. A
  `BlockchainRecord` row is a searchable local receipt; it is not the ledger.
