# Backend Migration Research

> **Document Created**: January 2026
> **Decision**: Stay with Python/FastAPI (performance is not a bottleneck)
> **Next Review**: When triggers in "When to Revisit" section are met

---

## Executive Summary

ParchMark's current Python/FastAPI backend was evaluated for potential migration to a compiled tech stack. After thorough analysis, the decision was made to **stay with Python** because:

1. Current performance is more than adequate for the application's scale
2. Compiled alternatives would provide 10-100x more throughput than needed
3. Migration effort (~2-4 weeks) is not justified without actual bottlenecks
4. FastAPI provides excellent developer experience and maintainability

This document preserves the research for future reference when revisiting this decision.

---

## Current Backend Analysis

### Overview

| Metric | Value |
|--------|-------|
| **Framework** | FastAPI 0.104.1 |
| **Runtime** | Python 3.13 |
| **ORM** | SQLAlchemy 2.0+ |
| **Database** | PostgreSQL |
| **Codebase Size** | ~2,300 lines |
| **Test Coverage** | 90%+ |

### API Surface

| Router | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| auth | `/api/auth` | 5 | Login, logout, refresh, me, health |
| notes | `/api/notes` | 6 | CRUD operations for notes |
| settings | `/api/settings` | 4 | User account management |
| health | `/api` | 1 | Health check with DB connectivity |

**Total**: 18 endpoints (mostly CRUD)

### Database Schema

```
users (1) ─────< (N) notes

users:
  - id, username, password_hash, email
  - oidc_sub, auth_provider (for OIDC support)
  - created_at

notes:
  - id (format: "note-{timestamp}")
  - user_id (FK), title, content
  - created_at, updated_at
```

### Authentication System

**Dual authentication** supporting both local and OIDC:

1. **Local JWT Authentication**
   - Access tokens: 30-minute expiration
   - Refresh tokens: 7-day expiration
   - Bcrypt password hashing

2. **OIDC/Authelia Integration**
   - RS256 token validation
   - JWKS caching (1-hour TTL)
   - Auto-creates users on first login

### Special Features Requiring Migration

| Feature | Implementation | Migration Complexity |
|---------|----------------|---------------------|
| Markdown title extraction | Regex: `^#\s+(.+)$` | Low |
| ZIP export | In-memory ZIP with metadata JSON | Medium |
| JWKS caching | Async double-checked locking | Medium |
| Database seeding | Idempotent user/note creation | Low |

---

## Compiled Stack Options Evaluated

### Tier 1: Recommended Options

#### 1. Go (Golang)

**Recommendation**: Best balance of performance, simplicity, and ecosystem

| Aspect | Details |
|--------|---------|
| **Framework** | Gin or Echo |
| **ORM** | GORM or sqlc (type-safe SQL) |
| **Auth** | golang-jwt/jwt + x/crypto/bcrypt |
| **Learning Curve** | Low-Medium |
| **Migration Effort** | ~2-3 weeks |

**Pros**:
- Single binary deployment
- Tiny Docker images (~10-20MB)
- Excellent concurrency (goroutines)
- Fast compilation
- Large ecosystem and hiring pool

**Cons**:
- More verbose than Python
- No generics until recently (Go 1.18+)
- Explicit error handling (`if err != nil`)

**Code Example** (Creating a note):
```go
func CreateNote(c *gin.Context) {
    user := c.MustGet("user").(*models.User)

    var input CreateNoteInput
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }

    title := markdown.ExtractTitle(input.Content)
    note, err := notes.Create(user.ID, title, input.Content)
    if err != nil {
        c.JSON(500, gin.H{"error": "Failed to create note"})
        return
    }

    c.JSON(201, note)
}
```

---

#### 2. Elixir/Phoenix

**Recommendation**: Best reliability and developer experience

| Aspect | Details |
|--------|---------|
| **Framework** | Phoenix |
| **ORM** | Ecto (excellent, similar to SQLAlchemy) |
| **Auth** | Guardian (JWT) + bcrypt_elixir |
| **OIDC** | Ueberauth with OIDC strategy |
| **Learning Curve** | Medium (functional paradigm) |
| **Migration Effort** | ~3-4 weeks |

**Pros**:
- Exceptional fault tolerance (supervision trees)
- "Let it crash" philosophy - isolated process crashes
- Beautiful, Ruby-inspired syntax
- Pattern matching reduces conditionals
- Phoenix LiveView for real-time features
- Hot code upgrades possible

**Cons**:
- Not native compilation (BEAM bytecode)
- Slower cold start (~1-2s vs ~50ms for Go)
- Smaller ecosystem and hiring pool
- Functional paradigm requires mindset shift

**Code Example** (Creating a note):
```elixir
def create(conn, %{"content" => content}) do
  user = conn.assigns.current_user
  title = MarkdownService.extract_title(content)

  case Notes.create_note(user, %{content: content, title: title}) do
    {:ok, note} ->
      conn |> put_status(:created) |> render(:show, note: note)
    {:error, changeset} ->
      conn |> put_status(:unprocessable_entity) |> render(:error, changeset: changeset)
  end
end
```

**Feature Mapping**:

| ParchMark Feature | Elixir Equivalent |
|-------------------|-------------------|
| FastAPI routes | Phoenix Controllers + Router |
| Pydantic schemas | Ecto Changesets |
| SQLAlchemy models | Ecto Schemas |
| JWT (python-jose) | Guardian + JOSE |
| Alembic migrations | Ecto Migrations (built-in) |
| Bcrypt hashing | bcrypt_elixir |
| ZIP export | `:zip` Erlang module (built-in) |

---

#### 3. Rust

**Recommendation**: Maximum performance, steepest learning curve

| Aspect | Details |
|--------|---------|
| **Framework** | Axum (modern) or Actix-web (fastest) |
| **ORM** | SQLx (compile-time checked) or Diesel |
| **Auth** | jsonwebtoken + argon2/bcrypt |
| **Learning Curve** | High (ownership, lifetimes) |
| **Migration Effort** | ~4-6 weeks |

**Pros**:
- Best-in-class performance
- Memory safety without garbage collection
- Excellent type system
- Zero-cost abstractions

**Cons**:
- Steeper learning curve (ownership model)
- Longer compile times
- More verbose code
- Smaller web ecosystem than Go

---

### Tier 2: Viable Alternatives

#### 4. .NET 8 / C#

| Aspect | Details |
|--------|---------|
| **Framework** | ASP.NET Core Minimal APIs |
| **ORM** | Entity Framework Core |
| **Auth** | Built-in JWT Bearer authentication |
| **Learning Curve** | Low-Medium |
| **Migration Effort** | ~2-3 weeks |

**Pros**: Mature, enterprise-grade, excellent tooling, familiar patterns
**Cons**: Larger memory footprint, Microsoft ecosystem dependency

---

#### 5. Kotlin/JVM

| Aspect | Details |
|--------|---------|
| **Framework** | Ktor (lightweight) or Spring Boot |
| **ORM** | Exposed (Kotlin DSL) |
| **Auth** | java-jwt / Spring Security |
| **Learning Curve** | Medium |
| **Migration Effort** | ~3-4 weeks |

**Pros**: Modern syntax, excellent coroutines, full Java interop
**Cons**: JVM startup overhead, larger memory footprint

---

#### 6. Gleam (Emerging)

| Aspect | Details |
|--------|---------|
| **Framework** | Wisp |
| **ORM** | Ecto via Elixir interop |
| **Runtime** | BEAM (same as Elixir) |
| **Learning Curve** | Medium |
| **Migration Effort** | ~4-5 weeks |

**Pros**: Static types + BEAM reliability, Rust-inspired syntax
**Cons**: Very new (1.0 in 2024), smaller ecosystem

---

## Performance Comparison

### Benchmark Data (JSON API, typical hardware)

| Stack | Requests/sec | Latency (p99) | Memory Baseline | Docker Image |
|-------|-------------|---------------|-----------------|--------------|
| **Python/FastAPI** | 5,000-15,000 | 5-15ms | 50-100MB | ~200MB |
| **Go/Gin** | 100,000-150,000 | 1-2ms | 10-20MB | 10-20MB |
| **Elixir/Phoenix** | 50,000-80,000 | 2-5ms | 50-100MB | 40-50MB |
| **Rust/Axum** | 150,000-200,000 | <1ms | 5-15MB | 5-15MB |
| **.NET 8** | 80,000-120,000 | 1-3ms | 80-150MB | 80-100MB |
| **Kotlin/Ktor** | 60,000-100,000 | 2-4ms | 100-200MB | 150-200MB |

### Cold Start Times

| Stack | Startup Time |
|-------|-------------|
| Go | ~50ms |
| Rust | ~50ms |
| .NET 8 | ~200-500ms |
| Elixir | ~1-2s |
| Kotlin/JVM | ~2-5s |
| Python | ~500ms-1s |

**Note**: For ParchMark's scale, Python's 5,000-15,000 req/sec is massive overkill. All compiled options would provide 10-100x more capacity than needed.

---

## Reliability Comparison

| Aspect | Python | Go | Elixir | Rust |
|--------|--------|-----|--------|------|
| **Type Safety** | Runtime (mypy helps) | Compile-time | Runtime (dialyzer) | Compile-time |
| **Process Isolation** | None | None (shared memory) | Excellent | None |
| **Supervision Trees** | Manual | Manual | Built-in | Manual |
| **Memory Safety** | GC | GC | GC | Ownership system |
| **Error Handling** | Exceptions | Explicit returns | Pattern matching | Result types |

---

## Decision Matrix

| Priority | Best Choice | Runner-up |
|----------|-------------|-----------|
| **Performance** | Rust | Go |
| **Reliability** | Elixir | Rust |
| **Developer Experience** | Elixir | Python (current) |
| **Deployment Simplicity** | Go | Rust |
| **Type Safety** | Rust | Go |
| **Ecosystem Size** | Go | .NET |
| **Real-time Features** | Elixir (LiveView) | Go + WebSockets |
| **Hiring Pool** | Go | .NET |

---

## When to Revisit This Decision

Consider migration when any of these triggers occur:

### Performance Triggers
- [ ] API latency exceeds 100ms at p95
- [ ] Request throughput exceeds 5,000 req/sec sustained
- [ ] Database queries become the bottleneck (optimize DB first)
- [ ] Memory usage exceeds available resources

### Architectural Triggers
- [ ] Real-time collaboration features needed (consider Elixir/Phoenix LiveView)
- [ ] Serverless deployment required (cold start times matter)
- [ ] Team grows significantly (hiring pool becomes important)
- [ ] Microservices architecture adopted

### Reliability Triggers
- [ ] Runtime type errors causing production incidents
- [ ] Process crashes affecting other users
- [ ] Need for hot code deployments without downtime

### Business Triggers
- [ ] Compliance requirements mandate specific languages
- [ ] Client/customer requirements specify tech stack
- [ ] Cost optimization needed (smaller containers = lower cloud costs)

---

## Migration Checklist (For Future Reference)

When migration is decided, follow this checklist:

### Phase 1: Setup (Week 1)
- [ ] Set up new project structure
- [ ] Configure database connections
- [ ] Implement basic health check endpoint
- [ ] Set up CI/CD pipeline for new stack
- [ ] Configure Docker builds

### Phase 2: Core Features (Week 2)
- [ ] Implement User model and schema
- [ ] Implement Note model and schema
- [ ] Port markdown utilities (title extraction, formatting)
- [ ] Implement local JWT authentication
- [ ] Port all CRUD endpoints

### Phase 3: Advanced Features (Week 3)
- [ ] Implement OIDC/Authelia integration
- [ ] Implement JWKS caching
- [ ] Implement ZIP export functionality
- [ ] Port database seeding scripts
- [ ] Implement user management CLI

### Phase 4: Testing & Deployment (Week 4)
- [ ] Port all unit tests
- [ ] Port all integration tests
- [ ] Achieve 90% test coverage
- [ ] Update Docker Compose configurations
- [ ] Update deployment scripts
- [ ] Parallel deployment testing
- [ ] Gradual traffic migration
- [ ] Decommission Python backend

---

## Resources & Links

### Go
- [Gin Framework](https://github.com/gin-gonic/gin)
- [Echo Framework](https://echo.labstack.com/)
- [GORM ORM](https://gorm.io/)
- [sqlc (Type-safe SQL)](https://sqlc.dev/)
- [golang-jwt](https://github.com/golang-jwt/jwt)

### Elixir
- [Phoenix Framework](https://www.phoenixframework.org/)
- [Ecto ORM](https://hexdocs.pm/ecto/Ecto.html)
- [Guardian (JWT)](https://github.com/ueberauth/guardian)
- [Ueberauth (OAuth/OIDC)](https://github.com/ueberauth/ueberauth)

### Rust
- [Axum Framework](https://github.com/tokio-rs/axum)
- [Actix-web](https://actix.rs/)
- [SQLx](https://github.com/launchbadge/sqlx)
- [Diesel ORM](https://diesel.rs/)

### .NET
- [ASP.NET Core](https://docs.microsoft.com/en-us/aspnet/core/)
- [Entity Framework Core](https://docs.microsoft.com/en-us/ef/core/)

### Kotlin
- [Ktor Framework](https://ktor.io/)
- [Exposed ORM](https://github.com/JetBrains/Exposed)

### Gleam
- [Gleam Language](https://gleam.run/)
- [Wisp Framework](https://github.com/lpil/wisp)

---

## Document History

| Date | Change |
|------|--------|
| January 2026 | Initial research and decision to stay with Python |

---

*This document should be reviewed when any triggers in the "When to Revisit" section are met.*
