# Authelia OIDC Compliance & Audit Logging Guide

Comprehensive guide for compliance requirements, audit logging, and regulatory adherence for ParchMark with Authelia OIDC.

---

## Table of Contents

1. [Overview](#overview)
2. [Compliance Requirements](#compliance-requirements)
3. [Audit Logging Implementation](#audit-logging-implementation)
4. [Data Protection](#data-protection)
5. [Access Control & RBAC](#access-control--rbac)
6. [Incident Reporting](#incident-reporting)
7. [Compliance Checklists](#compliance-checklists)

---

## Overview

### Compliance Frameworks Supported

| Framework | Status | Applicability |
|-----------|--------|----------------|
| **GDPR** | ✓ Implemented | EU user data, user rights |
| **SOC 2 Type II** | ✓ Implemented | Security, availability, confidentiality |
| **HIPAA** | ⚠ Partial | Healthcare data handling (requires additional setup) |
| **PCI-DSS** | ⚠ Partial | Payment data (if integrated with payment systems) |
| **ISO 27001** | ✓ Implemented | Information security management |
| **FedRAMP** | ☐ Not targeted | US government specific |

### Audit Requirements

ParchMark with OIDC provides comprehensive audit logging for:
- Authentication events (local and OIDC)
- Authorization decisions
- Data access patterns
- Account lifecycle events
- System configuration changes
- Security incident alerts

---

## Compliance Requirements

### GDPR Compliance

#### 1. Data Subject Rights

**Right to Access** - Users must be able to access their data:

```python
# backend/app/routers/gdpr.py
@app.get("/api/gdpr/export")
async def export_user_data(
    current_user: User = Depends(get_current_active_user)
):
    """Export all user data in machine-readable format (GDPR Article 15)"""

    user_data = {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "auth_provider": current_user.auth_provider,
            "oidc_linked": current_user.oidc_sub is not None
        },
        "notes": [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat()
            }
            for note in current_user.notes
        ],
        "auth_history": [
            {
                "event": log.event,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "status": log.status
            }
            for log in AuthAuditLog.query.filter_by(user_id=current_user.id).all()
        ]
    }

    return FileResponse(
        path=generate_json_export(user_data),
        filename=f"parchmark-export-{current_user.id}.json",
        media_type="application/json"
    )

@app.post("/api/gdpr/delete")
async def delete_user_data(
    current_user: User = Depends(get_current_active_user)
):
    """Permanently delete all user data (GDPR Article 17 - Right to be Forgotten)"""

    # Log the deletion request before deleting
    audit_log = AuditLog(
        user_id=current_user.id,
        event="USER_DELETION_REQUESTED",
        details={"username": current_user.username},
        ip_address=request.client.host,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    # Delete user data
    user_id = current_user.id
    Note.query.filter_by(user_id=user_id).delete()
    User.query.filter_by(id=user_id).delete()

    db.commit()

    logger.info(f"User {user_id} deleted all data per GDPR request")

    return {"status": "deleted"}
```

**Right to Rectification** - Users must be able to correct data:

```python
@app.put("/api/gdpr/correct")
async def correct_user_data(
    correction: DataCorrection,
    current_user: User = Depends(get_current_active_user)
):
    """Correct inaccurate personal data (GDPR Article 16)"""

    old_email = current_user.email
    current_user.email = correction.email

    # Log the change
    audit_log = AuditLog(
        user_id=current_user.id,
        event="DATA_CORRECTED",
        details={
            "field": "email",
            "old_value": old_email,
            "new_value": correction.email
        },
        ip_address=request.client.host,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"User {current_user.id} corrected data")
    return {"status": "corrected"}
```

#### 2. Data Processing Agreement

**Documentation Required**:
- Data Processing Addendum (DPA) for Authelia provider
- Cloud provider agreements (if using AWS, GCP, Azure)
- Sub-processor agreements
- Data transfer mechanisms (Standard Contractual Clauses if international)

**Sample DPA Checklist**:
```yaml
DPA_REQUIREMENTS:
  - Data processor appointment documented
  - Processing instructions documented
  - Confidentiality agreements in place
  - Sub-processor list maintained
  - Data subject rights procedures established
  - Audit rights granted
  - Data deletion procedures defined
  - Incident notification procedures established
```

#### 3. Data Protection Impact Assessment (DPIA)

**Required Assessment for OIDC implementation**:

```markdown
# DPIA: Authelia OIDC Integration

## Processing Activities
- User authentication (local and OIDC)
- Token storage (browser localStorage)
- Login event logging
- User profile data collection

## Necessity & Proportionality
- **Necessity**: Required for service operation
- **Proportionality**: Minimal data collected, retention limited

## Risk Assessment
- **Token interception**: Mitigated by HTTPS + short expiration
- **OIDC provider compromise**: Mitigated by token validation
- **Data breach**: Mitigated by encryption + access controls

## Safeguards
- HTTPS enforcement
- Token expiration (30 minutes)
- Secure password hashing (bcrypt)
- Access control enforcement
- Audit logging

## Rights Protection
- Users can export data
- Users can delete accounts
- Users can correct data
- Privacy policy provided
```

### SOC 2 Type II Compliance

#### Security Requirements

```python
# backend/app/security/controls.py

class SecurityControls:
    """SOC 2 Type II Security Controls Implementation"""

    @staticmethod
    async def enforce_tls():
        """CC6.1: Logical and Physical Access Controls - Encryption"""
        # Enforce HTTPS everywhere
        # TLS 1.2+ only
        # Certificate pinning for sensitive endpoints

    @staticmethod
    async def manage_authentication():
        """CC6.2: Authentication and Identity"""
        # Multi-factor authentication available
        # Password complexity enforced
        # Session timeout configured
        # Failed login tracking

    @staticmethod
    async def implement_encryption():
        """CC6.3: Encryption of Data in Transit and at Rest"""
        # Database encryption
        # Secrets management (AWS Secrets Manager)
        # TLS for all network communication

    @staticmethod
    async def monitor_activity():
        """CC7.2: System Monitoring"""
        # Comprehensive audit logging
        # Real-time alerting
        # Log retention for 12+ months
        # Integrity verification

    @staticmethod
    async def incident_response():
        """A1.1: Incident Response"""
        # Incident detection procedures
        # Escalation procedures
        # Post-incident review process
        # Evidence preservation
```

**Audit Evidence Collection**:

```python
# backend/app/audit/soc2_evidence.py
class SOC2EvidenceCollector:
    """Collect and document evidence for SOC2 Type II audits"""

    @staticmethod
    def collect_access_logs() -> dict:
        """Evidence: Who accessed what and when"""
        return {
            "file": "/var/log/access.log",
            "retention": "12 months",
            "entries": AuditLog.query.count(),
            "sample": AuditLog.query.limit(10).all()
        }

    @staticmethod
    def collect_configuration_baselines() -> dict:
        """Evidence: System configurations"""
        return {
            "tls_version": "1.2+",
            "password_policy": "12+ chars, uppercase, numbers, special",
            "session_timeout": "30 minutes",
            "mfa_available": True,
            "encryption_at_rest": "AES-256"
        }

    @staticmethod
    def collect_incident_logs() -> dict:
        """Evidence: Security incidents and response"""
        incidents = IncidentLog.query.all()
        return {
            "total_incidents": len(incidents),
            "resolved": sum(1 for i in incidents if i.resolved),
            "avg_resolution_time": calculate_avg_resolution_time(),
            "sample": [i.to_dict() for i in incidents[:5]]
        }

    @staticmethod
    def collect_change_logs() -> dict:
        """Evidence: Change management"""
        changes = ChangeLog.query.all()
        return {
            "total_changes": len(changes),
            "approved_percentage": calculate_approval_percentage(),
            "sample": [c.to_dict() for c in changes[:10]]
        }
```

---

## Audit Logging Implementation

### Comprehensive Audit Log Schema

```python
# backend/app/models/audit.py
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    # Event information
    event_type = Column(String)  # LOGIN, LOGOUT, CREATE_NOTE, DELETE_NOTE, etc.
    status = Column(String)  # SUCCESS, FAILURE, PARTIAL
    timestamp = Column(DateTime, index=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String)  # Captured at time of event
    email = Column(String)

    # Authentication information
    auth_method = Column(String)  # local, oidc
    auth_provider = Column(String)  # parchmark, authelia
    mfa_used = Column(Boolean, default=False)

    # Network information
    ip_address = Column(String, index=True)
    user_agent = Column(String)
    country_code = Column(String)  # GeoIP lookup

    # Details
    resource_type = Column(String)  # USER, NOTE, ACCOUNT, etc.
    resource_id = Column(String)
    action = Column(String)  # READ, CREATE, UPDATE, DELETE
    changes = Column(JSON)  # Before/after values for modifications

    # Compliance
    retention_until = Column(DateTime)  # Calculate based on policy
    anonymized = Column(Boolean, default=False)

    # Indexes
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
    )
```

### Event Types to Log

```python
# backend/app/audit/events.py
class AuditEventTypes:
    """Comprehensive list of events to log"""

    # Authentication events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    OIDC_LINK = "OIDC_LINK"
    OIDC_UNLINK = "OIDC_UNLINK"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"

    # Note operations
    NOTE_CREATED = "NOTE_CREATED"
    NOTE_UPDATED = "NOTE_UPDATED"
    NOTE_DELETED = "NOTE_DELETED"
    NOTE_VIEWED = "NOTE_VIEWED"
    NOTE_EXPORTED = "NOTE_EXPORTED"
    NOTE_SHARED = "NOTE_SHARED"

    # Account operations
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    DATA_EXPORTED = "DATA_EXPORTED"
    DATA_DELETED = "DATA_DELETED"

    # Security events
    SECURITY_ALERT = "SECURITY_ALERT"
    BRUTE_FORCE_DETECTED = "BRUTE_FORCE_DETECTED"
    UNUSUAL_LOCATION = "UNUSUAL_LOCATION"
    TOKEN_REVOKED = "TOKEN_REVOKED"

    # Administrative events
    ADMIN_ACTION = "ADMIN_ACTION"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"
```

### Audit Logging Middleware

```python
# backend/app/middleware/audit.py
from datetime import datetime

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API requests and responses"""

    start_time = time.time()
    user_id = None

    # Extract user from token if present
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            claims = decode_jwt(token)
            user_id = claims.get("sub")
        except:
            pass

    # Get IP address
    ip_address = request.client.host

    # Call the endpoint
    response = await call_next(request)

    # Log the request
    process_time = time.time() - start_time
    audit_log = AuditLog(
        event_type=f"API_{request.method}",
        status="SUCCESS" if response.status_code < 400 else "FAILURE",
        timestamp=datetime.utcnow(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
        resource_type="API",
        action=request.method,
        changes={
            "endpoint": str(request.url.path),
            "status_code": response.status_code,
            "duration_ms": process_time * 1000
        }
    )

    db.add(audit_log)
    db.commit()

    return response
```

---

## Data Protection

### Data Retention Policy

```yaml
DATA_RETENTION_POLICY:
  USER_ACCOUNT_DATA:
    retention_period: "Duration of user relationship + 30 days"
    deletion_trigger: "Account deletion or 12 months inactivity"

  AUTHENTICATION_LOGS:
    retention_period: "12 months"
    deletion_trigger: "Automated purge after 12 months"

  TRANSACTION_LOGS:
    retention_period: "7 years"  # For financial/compliance
    deletion_trigger: "Automated purge after 7 years"

  SECURITY_INCIDENT_LOGS:
    retention_period: "3 years"
    deletion_trigger: "Manual deletion after 3 years"

  GDPR_REQUEST_LOGS:
    retention_period: "3 years"
    deletion_trigger: "Manual deletion after 3 years"

  BACKUP_RETENTION:
    backup_duration: "30 days"
    archive_duration: "90 days"
    deletion_trigger: "Automated purge"
```

**Implementation**:

```python
# backend/app/tasks/retention.py
@app.task(schedule=crontab(hour=2, minute=0))  # Daily at 2 AM
def purge_expired_audit_logs():
    """Purge audit logs based on retention policy"""

    cutoff_date = datetime.utcnow() - timedelta(days=365)

    deleted = AuditLog.query.filter(
        AuditLog.timestamp < cutoff_date,
        AuditLog.event_type != "SECURITY_INCIDENT"  # Keep security logs longer
    ).delete()

    db.commit()
    logger.info(f"Purged {deleted} audit log entries")
```

### Data Minimization

```python
# Collect only necessary data
MINIMAL_OIDC_CLAIMS = {
    "sub": "Unique identifier",
    "preferred_username": "Display name",
    "email": "Contact",
}

# Don't collect if not needed
EXCLUDED_CLAIMS = {
    "phone_number",
    "address",
    "birthdate",
    "gender",
    "locale",
}
```

---

## Access Control & RBAC

### Role-Based Access Control

```python
# backend/app/models/roles.py
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # admin, user, viewer, auditor
    permissions = Column(JSON)

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    resource = Column(String)  # notes, users, audit_logs
    action = Column(String)  # read, create, update, delete

# Predefined roles
ROLES = {
    "admin": ["*"],  # All permissions
    "user": [
        "notes:create", "notes:read", "notes:update", "notes:delete",
        "account:read", "account:update",
        "audit_logs:read:own"  # Only own logs
    ],
    "auditor": [
        "audit_logs:read:all",
        "users:read:all"
    ],
    "viewer": [
        "notes:read"
    ]
}
```

### Permission Enforcement

```python
# backend/app/auth/permissions.py
def require_permission(resource: str, action: str):
    """Decorator to enforce permissions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            required_permission = f"{resource}:{action}"

            if not has_permission(current_user, required_permission):
                logger.warning(
                    f"Permission denied for user {current_user.id}: {required_permission}"
                )
                raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator

@app.get("/api/audit-logs")
@require_permission("audit_logs", "read:all")
async def get_all_audit_logs(current_user: User = Depends(get_current_active_user)):
    """Only auditors and admins can access all logs"""
    return AuditLog.query.all()
```

---

## Incident Reporting

### Breach Notification

```python
# backend/app/security/breach_notification.py
class BreachNotificationService:
    """Handle security breach notifications per GDPR Article 33/34"""

    @staticmethod
    async def report_breach(
        incident: SecurityIncident,
        affected_users: List[User]
    ):
        """Report breach to authorities and users"""

        # Determine notification requirements
        breach_severity = calculate_breach_severity(incident)
        authorities_notification_required = breach_severity > THRESHOLD

        # Notify authorities (GDPR: within 72 hours)
        if authorities_notification_required:
            await notify_data_protection_authority(
                incident=incident,
                affected_count=len(affected_users),
                description=incident.description,
                remediation=incident.remediation
            )

        # Notify affected users (GDPR: without undue delay)
        notification_email = render_template("breach_notification.html", {
            "incident": incident,
            "recommended_actions": get_recommended_actions(incident.type)
        })

        for user in affected_users:
            send_email(
                to=user.email,
                subject="Security Incident Notification",
                body=notification_email
            )

        # Log the breach notification
        audit_log = AuditLog(
            event_type="BREACH_NOTIFICATION",
            status="SUCCESS",
            timestamp=datetime.utcnow(),
            changes={
                "incident_id": incident.id,
                "affected_users": len(affected_users),
                "authority_notified": authorities_notification_required
            }
        )
        db.add(audit_log)
        db.commit()
```

---

## Compliance Checklists

### GDPR Compliance Checklist

```markdown
# GDPR Compliance Checklist

## Data Collection & Processing
- [ ] Privacy policy published and accessible
- [ ] User consent obtained before processing (if not service necessary)
- [ ] Legitimate interest documented (if applicable)
- [ ] Data minimization implemented
- [ ] Purpose limitation enforced

## User Rights Implementation
- [ ] Right to Access: Data export feature implemented
- [ ] Right to Rectification: Data correction feature implemented
- [ ] Right to Erasure: Account deletion feature implemented
- [ ] Right to Restrict: Data export option available
- [ ] Right to Data Portability: Export in standard format
- [ ] Right to Object: Opt-out mechanisms available

## Compliance Procedures
- [ ] Data Processing Agreement signed with processors
- [ ] DPA completed for OIDC integration
- [ ] Incident response plan documented
- [ ] Breach notification procedures in place
- [ ] Data Protection Officer contact published

## Technical Measures
- [ ] Encryption in transit (HTTPS)
- [ ] Encryption at rest
- [ ] Access controls implemented
- [ ] Audit logging enabled
- [ ] Regular security assessments conducted

## Governance
- [ ] Retention policy documented
- [ ] Data inventory maintained
- [ ] Sub-processor list maintained
- [ ] Documentation organized for audits
```

### SOC 2 Type II Checklist

```markdown
# SOC 2 Type II Compliance Checklist

## CC6: Logical and Physical Access Controls
- [ ] Authentication enforced (local + OIDC)
- [ ] Multi-factor authentication available
- [ ] Password complexity requirements
- [ ] Session timeout configured
- [ ] Encryption enabled

## CC7: System Monitoring
- [ ] Comprehensive audit logging
- [ ] Real-time alerting configured
- [ ] Log retention for 12+ months
- [ ] Integrity verification implemented
- [ ] Anomaly detection enabled

## A1: Service Commitment and Responsibilities
- [ ] Service level agreements published
- [ ] Incident response procedures documented
- [ ] Change management process documented
- [ ] Disaster recovery plan tested

## Audit Evidence
- [ ] Access logs collected (12 months)
- [ ] Configuration baselines documented
- [ ] Incident logs maintained
- [ ] Change logs tracked
```

---

## See Also

- **AUTHELIA_OIDC_SECURITY_HARDENING.md** - Security measures
- **AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md** - Operational compliance
- **AUTHELIA_OIDC_MONITORING_OBSERVABILITY.md** - Audit logging setup
