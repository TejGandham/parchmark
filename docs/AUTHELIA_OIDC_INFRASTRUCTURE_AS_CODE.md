# Authelia OIDC Infrastructure-as-Code Guide

Complete Terraform configurations for deploying ParchMark with Authelia OIDC authentication on Docker Swarm or Kubernetes.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Docker Swarm Deployment](#docker-swarm-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [AWS ECS Deployment](#aws-ecs-deployment)
6. [Network Configuration](#network-configuration)
7. [Storage & Persistence](#storage--persistence)
8. [Monitoring Stack Integration](#monitoring-stack-integration)
9. [SSL/TLS Certificates](#ssltls-certificates)
10. [State Management](#state-management)

---

## Overview

### Architecture

```
┌──────────────────────────────────────────────────────┐
│ Load Balancer / Ingress Controller                   │
│ (Nginx / Traefik)                                    │
└──────────────────┬───────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼──┐   ┌───▼──┐   ┌──▼────┐
    │Auth  │   │Note  │   │Asset  │
    │      │   │sApp  │   │API    │
    │9091  │   │5173  │   │8000   │
    └───┬──┘   └───┬──┘   └──┬────┘
        │          │         │
        │   ┌──────┼─────────┤
        │   │      │         │
    ┌───▼───▼──┐ ┌─▼────┐ ┌──▼────┐
    │PostgreSQL│ │Redis │ │Volumes│
    │          │ │Cache │ │Persist│
    └──────────┘ └──────┘ └───────┘
```

### Deployment Targets

- **Docker Swarm**: Single-server or cluster deployments
- **Kubernetes**: Managed services (EKS, GKE, AKS) or self-hosted
- **AWS ECS**: AWS-native containerization
- **Docker Compose**: Local development (pre-existing)

---

## Prerequisites

**Tools Required**:
- Terraform >= 1.0
- Docker / Kubernetes CLI
- AWS CLI (for AWS deployments)

**Infrastructure**:
- Domain names configured (auth.engen.tech, notes.engen.tech, assets-api.engen.tech)
- SSL/TLS certificates or Let's Encrypt access
- PostgreSQL 13+ database
- Persistent storage (local, NFS, or cloud storage)

---

## Docker Swarm Deployment

### Terraform Configuration

**File: `terraform/docker-swarm/main.tf`**:

```hcl
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = var.docker_host
}

variable "docker_host" {
  default = "unix:///var/run/docker.sock"
}

# Docker networks
resource "docker_network" "parchmark" {
  name   = "parchmark-network"
  driver = "overlay"

  labels {
    key   = "environment"
    value = "production"
  }
}

# PostgreSQL service
resource "docker_service" "postgres" {
  name = "parchmark-db"

  task_spec {
    container_spec {
      image = "postgres:15-alpine"

      env = [
        "POSTGRES_USER=parchmark_user",
        "POSTGRES_PASSWORD=${var.db_password}",
        "POSTGRES_DB=parchmark_db"
      ]

      mounts {
        type  = "volume"
        source = docker_volume.postgres_data.name
        target = "/var/lib/postgresql/data"
      }

      healthcheck {
        test     = ["CMD-SHELL", "pg_isready -U parchmark_user"]
        interval = "10s"
        timeout  = "5s"
        retries  = 5
      }
    }

    resources {
      limits {
        nano_cpus    = 1000000000  # 1 CPU
        memory_bytes = 2147483648 # 2 GB
      }

      reservation {
        nano_cpus    = 500000000
        memory_bytes = 1073741824 # 1 GB
      }
    }

    placement {
      constraints = ["node.role == manager"]
    }
  }

  networks_advanced {
    name = docker_network.parchmark.name
  }

  depends_on = [docker_volume.postgres_data]
}

# Redis cache service
resource "docker_service" "redis" {
  name = "parchmark-cache"

  task_spec {
    container_spec {
      image = "redis:7-alpine"

      healthcheck {
        test     = ["CMD", "redis-cli", "ping"]
        interval = "10s"
        timeout  = "5s"
        retries  = 5
      }
    }

    resources {
      limits {
        nano_cpus    = 500000000  # 0.5 CPU
        memory_bytes = 536870912  # 512 MB
      }
    }

    placement {
      constraints = ["node.role == manager"]
    }
  }

  networks_advanced {
    name = docker_network.parchmark.name
  }
}

# Authelia service
resource "docker_service" "authelia" {
  name = "parchmark-auth"

  task_spec {
    container_spec {
      image = "authelia/authelia:latest"

      env = [
        "AUTHELIA_JWT_SECRET=${var.authelia_jwt_secret}",
        "AUTHELIA_SESSION_SECRET=${var.authelia_session_secret}",
        "AUTHELIA_STORAGE_MYSQL_PASSWORD=${var.db_password}",
        "AUTHELIA_IDENTITY_PROVIDERS_OIDC_CLIENTS_0_CLIENT_ID=parchmark-web",
        "AUTHELIA_IDENTITY_PROVIDERS_OIDC_CLIENTS_0_CLIENT_SECRET=${var.oidc_client_secret}",
      ]

      mounts {
        type   = "bind"
        source = "/etc/authelia"
        target = "/etc/authelia"
      }

      ports {
        target_port = 9091
        host_port   = 9091
        publish_mode = "host"
      }

      healthcheck {
        test     = ["CMD", "wget", "--spider", "-q", "http://localhost:9091/api/health"]
        interval = "30s"
        timeout  = "10s"
        retries  = 3
      }
    }

    resources {
      limits {
        nano_cpus    = 1000000000
        memory_bytes = 1073741824 # 1 GB
      }
    }

    restart_policy {
      condition   = "on-failure"
      delay       = "5s"
      max_attempts = 3
      window      = "10s"
    }

    placement {
      constraints = ["node.role == manager"]
    }
  }

  networks_advanced {
    name = docker_network.parchmark.name
  }

  depends_on = [docker_service.postgres]
}

# Backend API service
resource "docker_service" "backend" {
  name = "parchmark-backend"

  task_spec {
    container_spec {
      image = "${var.docker_registry}/parchmark-backend:${var.backend_version}"

      env = [
        "DATABASE_URL=postgresql://parchmark_user:${var.db_password}@postgres:5432/parchmark_db",
        "SECRET_KEY=${var.secret_key}",
        "AUTH_MODE=hybrid",
        "OIDC_ISSUER_URL=${var.oidc_issuer_url}",
        "OIDC_AUDIENCE=parchmark-web",
        "OIDC_USERNAME_CLAIM=preferred_username",
        "ALLOWED_ORIGINS=${var.allowed_origins}",
        "ENVIRONMENT=production"
      ]

      ports {
        target_port = 8000
        host_port   = 8000
        publish_mode = "host"
      }

      healthcheck {
        test     = ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
        interval = "30s"
        timeout  = "10s"
        retries  = 3
      }
    }

    resources {
      limits {
        nano_cpus    = 2000000000  # 2 CPU
        memory_bytes = 2147483648  # 2 GB
      }

      reservation {
        nano_cpus    = 1000000000
        memory_bytes = 1073741824
      }
    }

    restart_policy {
      condition   = "on-failure"
      delay       = "5s"
      max_attempts = 5
      window      = "60s"
    }

    update_config {
      parallelism   = 1
      delay         = "10s"
      failure_action = "pause"
      monitor       = "5s"
    }

    placement {
      constraints = ["node.role == worker || node.role == manager"]
    }
  }

  networks_advanced {
    name = docker_network.parchmark.name
  }

  depends_on = [docker_service.postgres, docker_service.authelia]
}

# Frontend service
resource "docker_service" "frontend" {
  name = "parchmark-frontend"

  task_spec {
    container_spec {
      image = "${var.docker_registry}/parchmark-frontend:${var.frontend_version}"

      env = [
        "VITE_API_URL=${var.api_url}",
        "VITE_OIDC_ISSUER_URL=${var.oidc_issuer_url}",
        "VITE_OIDC_CLIENT_ID=parchmark-web",
        "VITE_OIDC_REDIRECT_URI=${var.frontend_url}/oidc/callback",
        "VITE_OIDC_LOGOUT_REDIRECT_URI=${var.frontend_url}/login",
      ]

      ports {
        target_port = 8080
        host_port   = 80
        publish_mode = "host"
      }

      healthcheck {
        test     = ["CMD", "wget", "--spider", "-q", "http://localhost:8080/"]
        interval = "30s"
        timeout  = "10s"
        retries  = 3
      }
    }

    resources {
      limits {
        nano_cpus    = 1000000000  # 1 CPU
        memory_bytes = 512000000   # 512 MB
      }
    }

    restart_policy {
      condition = "on-failure"
    }

    placement {
      constraints = ["node.role == worker || node.role == manager"]
    }
  }

  networks_advanced {
    name = docker_network.parchmark.name
  }
}

# Persistent volumes
resource "docker_volume" "postgres_data" {
  name = "parchmark-postgres-data"

  labels {
    key   = "backup"
    value = "daily"
  }
}

# Outputs
output "postgres_address" {
  value = "postgres:5432"
}

output "authelia_address" {
  value = "parchmark-auth:9091"
}

output "backend_address" {
  value = "parchmark-backend:8000"
}

output "frontend_address" {
  value = "parchmark-frontend:8080"
}
```

**File: `terraform/docker-swarm/variables.tf`**:

```hcl
variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
  default     = "ghcr.io/your-org"
}

variable "backend_version" {
  description = "Backend image version/tag"
  type        = string
}

variable "frontend_version" {
  description = "Frontend image version/tag"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "authelia_jwt_secret" {
  description = "Authelia JWT secret"
  type        = string
  sensitive   = true
}

variable "authelia_session_secret" {
  description = "Authelia session secret"
  type        = string
  sensitive   = true
}

variable "oidc_client_secret" {
  description = "OIDC client secret"
  type        = string
  sensitive   = true
}

variable "oidc_issuer_url" {
  description = "OIDC issuer URL (Authelia)"
  type        = string
}

variable "frontend_url" {
  description = "Frontend public URL"
  type        = string
}

variable "api_url" {
  description = "API public URL"
  type        = string
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = string
}
```

### Deployment

```bash
# Set variables
export TF_VAR_backend_version="sha-abc123"
export TF_VAR_frontend_version="sha-abc123"
export TF_VAR_db_password="$(openssl rand -base64 32)"
export TF_VAR_secret_key="$(openssl rand -base64 32)"
export TF_VAR_authelia_jwt_secret="$(openssl rand -base64 32)"
export TF_VAR_authelia_session_secret="$(openssl rand -base64 32)"
export TF_VAR_oidc_client_secret="$(openssl rand -base64 32)"
export TF_VAR_oidc_issuer_url="https://auth.engen.tech"
export TF_VAR_frontend_url="https://notes.engen.tech"
export TF_VAR_api_url="https://assets-api.engen.tech"
export TF_VAR_allowed_origins="https://notes.engen.tech"

# Initialize Terraform
terraform -chdir=terraform/docker-swarm init

# Plan deployment
terraform -chdir=terraform/docker-swarm plan -out=tfplan

# Apply
terraform -chdir=terraform/docker-swarm apply tfplan

# View outputs
terraform -chdir=terraform/docker-swarm output
```

---

## Kubernetes Deployment

### Helm Chart Structure

**File: `helm/parchmark-oidc/Chart.yaml`**:

```yaml
apiVersion: v2
name: parchmark-oidc
description: ParchMark with Authelia OIDC authentication
type: application
version: 1.0.0
appVersion: "1.0.0"

dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled

  - name: redis
    version: "17.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled

keywords:
  - parchmark
  - oidc
  - authelia
  - notes

maintainers:
  - name: ParchMark Team
    email: team@example.com
```

**File: `helm/parchmark-oidc/values.yaml`**:

```yaml
# PostgreSQL
postgresql:
  enabled: true
  auth:
    username: parchmark_user
    password: changeme
    database: parchmark_db
  primary:
    persistence:
      enabled: true
      size: 20Gi
  replica:
    replicaCount: 1

# Redis
redis:
  enabled: true
  auth:
    enabled: true
    password: changeme
  master:
    persistence:
      enabled: true
      size: 5Gi
  replica:
    replicaCount: 1

# Authelia
authelia:
  enabled: true
  replicaCount: 2
  image:
    repository: authelia/authelia
    tag: latest
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

# ParchMark Backend
backend:
  replicaCount: 2
  image:
    repository: ghcr.io/your-org/parchmark-backend
    tag: latest
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchExpressions:
                - key: app
                  operator: In
                  values:
                    - parchmark-backend
            topologyKey: kubernetes.io/hostname

# ParchMark Frontend
frontend:
  replicaCount: 2
  image:
    repository: ghcr.io/your-org/parchmark-frontend
    tag: latest
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"

# Ingress
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: auth.engen.tech
      paths:
        - path: /
          pathType: Prefix
    - host: notes.engen.tech
      paths:
        - path: /
          pathType: Prefix
    - host: assets-api.engen.tech
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: parchmark-tls
      hosts:
        - auth.engen.tech
        - notes.engen.tech
        - assets-api.engen.tech

# Monitoring
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

**File: `helm/parchmark-oidc/templates/backend-deployment.yaml`**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "parchmark-oidc.fullname" . }}-backend
  labels:
    {{- include "parchmark-oidc.labels" . | nindent 4 }}
    component: backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      {{- include "parchmark-oidc.selectorLabels" . | nindent 6 }}
      component: backend
  template:
    metadata:
      labels:
        {{- include "parchmark-oidc.selectorLabels" . | nindent 8 }}
        component: backend
    spec:
      containers:
        - name: backend
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: DATABASE_URL
              value: "postgresql://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ .Release.Name }}-postgresql:5432/{{ .Values.postgresql.auth.database }}"
            - name: AUTH_MODE
              value: "hybrid"
            - name: OIDC_ISSUER_URL
              value: "{{ .Values.oidcIssuerUrl }}"
            - name: OIDC_AUDIENCE
              value: "parchmark-web"
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "parchmark-oidc.fullname" . }}-secrets
                  key: secret-key
            - name: ALLOWED_ORIGINS
              value: "https://notes.engen.tech"
          livenessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
      affinity:
        {{- toYaml .Values.backend.affinity | nindent 8 }}
```

### Deployment

```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install
helm install parchmark ./helm/parchmark-oidc \
  --namespace parchmark \
  --create-namespace \
  --values custom-values.yaml

# Check status
helm status parchmark -n parchmark
kubectl get pods -n parchmark

# Upgrade
helm upgrade parchmark ./helm/parchmark-oidc \
  --namespace parchmark \
  --values custom-values.yaml
```

---

## AWS ECS Deployment

### Terraform Configuration

**File: `terraform/aws-ecs/main.tf`**:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ECS Cluster
resource "aws_ecs_cluster" "parchmark" {
  name = "parchmark-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = "production"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "parchmark" {
  name              = "/ecs/parchmark"
  retention_in_days = 7

  tags = {
    Environment = "production"
  }
}

# Task Definition
resource "aws_ecs_task_definition" "parchmark_backend" {
  family                   = "parchmark-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([{
    name      = "parchmark-backend"
    image     = "${var.docker_registry}/parchmark-backend:${var.backend_version}"
    essential = true

    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "DATABASE_URL"
        value = "postgresql://${var.db_user}:${var.db_password}@${aws_rds_cluster_instance.parchmark.endpoint}:5432/${var.db_name}"
      },
      {
        name  = "AUTH_MODE"
        value = "hybrid"
      },
      {
        name  = "OIDC_ISSUER_URL"
        value = var.oidc_issuer_url
      },
      {
        name  = "OIDC_AUDIENCE"
        value = "parchmark-web"
      }
    ]

    secrets = [
      {
        name      = "SECRET_KEY"
        valueFrom = "${aws_secretsmanager_secret.parchmark_secret_key.arn}:secret-key::"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.parchmark.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])

  tags = {
    Environment = "production"
  }
}

# ECS Service
resource "aws_ecs_service" "parchmark_backend" {
  name            = "parchmark-backend"
  cluster         = aws_ecs_cluster.parchmark.id
  task_definition = aws_ecs_task_definition.parchmark_backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.parchmark_backend.arn
    container_name   = "parchmark-backend"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.parchmark_backend,
    aws_iam_role_policy.ecs_task_execution_role_policy
  ]

  tags = {
    Environment = "production"
  }
}

# Auto Scaling
resource "aws_appautoscaling_target" "backend_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.parchmark.name}/${aws_ecs_service.parchmark_backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_policy_cpu" {
  policy_name            = "cpu-autoscaling"
  policy_type            = "TargetTrackingScaling"
  resource_id            = aws_appautoscaling_target.backend_target.resource_id
  scalable_dimension     = aws_appautoscaling_target.backend_target.scalable_dimension
  service_namespace      = aws_appautoscaling_target.backend_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# RDS Database
resource "aws_rds_cluster" "parchmark" {
  cluster_identifier     = "parchmark-cluster"
  engine                 = "aurora-postgresql"
  engine_version         = "15.2"
  database_name          = var.db_name
  master_username        = var.db_user
  master_password        = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.parchmark.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  skip_final_snapshot       = false
  final_snapshot_identifier = "parchmark-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Environment = "production"
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "parchmark_secret_key" {
  name                    = "parchmark/secret-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "parchmark_secret_key" {
  secret_id      = aws_secretsmanager_secret.parchmark_secret_key.id
  secret_string  = jsonencode({ "secret-key" = var.secret_key })
}

# Outputs
output "backend_service_name" {
  value = aws_ecs_service.parchmark_backend.name
}

output "database_endpoint" {
  value = aws_rds_cluster.parchmark.endpoint
}
```

---

## Network Configuration

### DNS Setup

```hcl
# Route53 records
resource "aws_route53_record" "auth" {
  zone_id = var.route53_zone_id
  name    = "auth.engen.tech"
  type    = "A"
  alias {
    name                   = aws_lb.parchmark.dns_name
    zone_id                = aws_lb.parchmark.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "frontend" {
  zone_id = var.route53_zone_id
  name    = "notes.engen.tech"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.parchmark.domain_name
    zone_id                = aws_cloudfront_distribution.parchmark.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api" {
  zone_id = var.route53_zone_id
  name    = "assets-api.engen.tech"
  type    = "A"
  alias {
    name                   = aws_lb.parchmark.dns_name
    zone_id                = aws_lb.parchmark.zone_id
    evaluate_target_health = true
  }
}
```

### Security Groups

```hcl
resource "aws_security_group" "alb" {
  name = "parchmark-alb"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks" {
  name = "parchmark-ecs-tasks"

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name = "parchmark-rds"

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
}
```

---

## Storage & Persistence

### Persistent Volumes (Kubernetes)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 50Gi

---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
allowVolumeExpansion: true
```

---

## Monitoring Stack Integration

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: parchmark-backend
spec:
  selector:
    matchLabels:
      app: parchmark-backend
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

---

## SSL/TLS Certificates

### Let's Encrypt with Cert-Manager

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

---

## State Management

### Terraform Backend (S3)

```hcl
terraform {
  backend "s3" {
    bucket         = "parchmark-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}
```

---

## Deployment Checklist

- [ ] Secrets created in Secrets Manager / Vault
- [ ] Database backups configured
- [ ] SSL/TLS certificates provisioned
- [ ] DNS records propagated
- [ ] Monitoring dashboards created
- [ ] Alerting rules configured
- [ ] Backup and recovery procedures tested
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security audit performed

---

## See Also

- **AUTHELIA_OIDC_OPERATIONS_RUNBOOK.md** - Operational procedures
- **AUTHELIA_OIDC_MONITORING_OBSERVABILITY.md** - Monitoring setup
- **AUTHELIA_OIDC_DEPLOYMENT.md** - Traditional deployment
