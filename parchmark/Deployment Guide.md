
## Current State Analysis

  

### Current Architecture

- **Module Location**: `/Users/tej/src/axomic/AXO373/modules/aws/services/AXO484/`

- **Environment File**: `/Users/tej/src/axomic/AXO373/env/shredai/aws/oa_integration/main.tf`

- **Service Type**: ECS Fargate (not Lambda like AXO431)

- **Current Setup**: Single ECS service exposed via public ALB

  

### Files in AXO484 Module

1. `main.tf` - Module locals and database module

2. `ecs.tf` - Single ECS service definition

3. `variables.tf` - Input variables

4. `iam.tf` - IAM roles and policies

5. `security_groups.tf` - Security group rules for RDS access

  

## Implementation Strategy

  

### Core Principle

- **ONE module call** from environment file

- Module internally creates **BOTH** internal and external services

- Keep existing `ecs.tf` file and modify it

- Minimal changes to achieve the goal

  

## Detailed Implementation Steps

  

### Step 1: Add ALB Configuration Variables to variables.tf

  

**File**: `/Users/tej/src/axomic/AXO373/modules/aws/services/AXO484/variables.tf`

  

**Current State** (lines 116-125):

```hcl

variable "alb_config" {

description = "Configuration for the ALB"

type = object({

listener_arn = string

security_group_id = string

dns_name = string

zone_id = string

})

}

```

  

**Action**: Modify existing `alb_config` variable and add new variables after line 125

  

**Exact Changes**:

1. **Modify existing `alb_config` variable** (lines 116-125):

- Add `default = null` to make it optional

- Update description to indicate deprecation

2. **Add new variables** after line 125:

```hcl

# ALB configurations for internal and external services

variable "internal_alb_config" {

description = "ALB configuration for internal service"

type = object({

listener_arn = string

security_group_id = string

dns_name = string

zone_id = string

})

nullable = false

}

variable "external_alb_config" {

description = "ALB configuration for external service"

type = object({

listener_arn = string

security_group_id = string

dns_name = string

zone_id = string

})

nullable = false

}

# Optional: Add a flag to control which services to create

variable "create_internal_service" {

description = "Whether to create the internal service"

type = bool

default = true

}

variable "create_external_service" {

description = "Whether to create the external service"

type = bool

default = true

}

```

  

**Why These Variables**:

- `internal_alb_config`: Configuration for private ALB (VPN/internal access only)

- `external_alb_config`: Configuration for public ALB (internet-facing)

- `create_internal_service`: Optional flag to enable/disable internal service

- `create_external_service`: Optional flag to enable/disable external service

  

### Step 2: Modify ecs.tf to Add Internal Service

  

**File**: `/Users/tej/src/axomic/AXO373/modules/aws/services/AXO484/ecs.tf`

  

**Current State**: Single module block `api_service` (lines 1-60)

  

**Action**: Add internal service module BEFORE existing module, then modify existing module

  

#### Part A: Add Internal Service Module at Beginning of File

  

**Insert at line 1** (pushing existing content down):

```hcl

# Internal API Service

module "api_internal_service" {

count = var.create_internal_service ? 1 : 0

source = "../../../../submodules/ecs_fargate_service"

  

providers = {

aws.main = aws.main

aws.master = aws.master

}

  

name = "${var.name}-internal"

ecr_name = var.ecr_repository_name

tags = local.tags

container_cpu = var.service_container_config.cpu

container_memory = var.service_container_config.memory

container_desired_count = var.service_container_config.desired_count

  

# Use internal ALB configuration

alb_config = var.internal_alb_config

alb_ingress_security_group_ids = var.ingress_security_group_ids

  

# Internal domain

domain = "${var.name}-internal.${var.parent_domain_name}"

zone_id = var.zone_id

  

cpu_architecture = "ARM64"

container_image = var.ecr_image.image_uri

ecs_port = var.service_container_config.container_port

  

# Same environment variables as external

environment = [

{ name = "RELEASE_VERSION", value = var.release },

{ name = "ENVIRONMENT", value = var.environment },

{ name = "LOG_TO_CONSOLE", value = false },

{ name = "LOG_LEVEL", value = var.debug ? "DEBUG" : "INFO" },

{ name = "DEBUG", value = var.debug },

{ name = "DISABLE_CORS", value = true }, # Internal doesn't need CORS

{ name = "DEV_MODE", value = var.use_dev_settings },

{ name = "REQUIRED_OA_JWT_CLAIMS", value = join(",", var.required_oa_jwt_claims) },

{ name = "CLIENT_REGISTRY_SERVICE_URL", value = var.axo395_api_uri },

{ name = "SHRED_DOCUMENT_SERVICE_URL", value = var.axo473_api_uri },

{ name = "DB_HOST", value = var.rds_config.cluster_endpoint },

{ name = "DB_PORT", value = var.rds_config.cluster_port },

{ name = "DB_NAME", value = module.db.db_name_ssm.value },

{ name = "DB_USERNAME", value = module.db.db_user_ssm.value },

{ name = "DB_PASSWORD", value = module.db.db_password_ssm.value },

{ name = "SERVICE_TYPE", value = "internal" }, # Add identifier

]

  

healthcheck_config = {

path = var.service_container_config.health_check_path,

interval = 20,

retries = 10,

}

  

vpc_id = var.vpc_id

ecs_subnet_ids = var.services_subnet_ids

}

  

# External API Service (existing module with modifications)

```

  

#### Part B: Modify Existing Module `api_service`

  

**Changes to existing module** (now starts around line 62):

  

1. **Add count parameter** (after line 1 of module):

```hcl

module "api_service" {

count = var.create_external_service ? 1 : 0 # ADD THIS LINE

source = "../../../../submodules/ecs_fargate_service"

```

  

2. **Change name** (line 9):

```hcl

# FROM:

name = var.name

# TO:

name = "${var.name}-external"

```

  

3. **Change ALB config** (line 16):

```hcl

# FROM:

alb_config = var.alb_config

# TO:

alb_config = var.external_alb_config

```

  

4. **Change ingress security groups** (line 17):

```hcl

# FROM:

alb_ingress_security_group_ids = var.ingress_security_group_ids

# TO:

alb_ingress_security_group_ids = [] # External is open to internet

```

  

5. **Add SERVICE_TYPE to environment array** (after line 47):

```hcl

{ name = "DB_PASSWORD", value = module.db.db_password_ssm.value },

{ name = "SERVICE_TYPE", value = "external" }, # ADD THIS LINE

```

  

**Key Differences Between Services**:

- **Names**: `axo484-internal` vs `axo484-external`

- **Domains**: `axo484-internal.shredapp.ai` vs `axo484.shredapp.ai`

- **ALB**: Private ALB vs Public ALB

- **Security Groups**: VPN access only vs Internet access

- **CORS**: Disabled for internal, enabled for external

- **SERVICE_TYPE**: Environment variable to identify service type

  

### Step 3: Update security_groups.tf

  

**File**: `/Users/tej/src/axomic/AXO373/modules/aws/services/AXO484/security_groups.tf`

  

**Current State** (entire file):

```hcl

# For API service

resource "aws_vpc_security_group_ingress_rule" "rds_from_api" {

provider = aws.main

  

security_group_id = var.rds_config.security_group_id

description = local.description

ip_protocol = "tcp"

from_port = var.rds_config.cluster_port

to_port = var.rds_config.cluster_port

referenced_security_group_id = module.api_service.ecs_security_group.id

}

```

  

**Action**: Replace entire file content

  

**New Content**:

```hcl

# For Internal API service

resource "aws_vpc_security_group_ingress_rule" "rds_from_api_internal" {

count = var.create_internal_service ? 1 : 0

provider = aws.main

  

security_group_id = var.rds_config.security_group_id

description = "${local.description} - Internal API"

ip_protocol = "tcp"

from_port = var.rds_config.cluster_port

to_port = var.rds_config.cluster_port

referenced_security_group_id = module.api_internal_service[0].ecs_security_group.id

}

  

# For External API service

resource "aws_vpc_security_group_ingress_rule" "rds_from_api_external" {

count = var.create_external_service ? 1 : 0

provider = aws.main

  

security_group_id = var.rds_config.security_group_id

description = "${local.description} - External API"

ip_protocol = "tcp"

from_port = var.rds_config.cluster_port

to_port = var.rds_config.cluster_port

referenced_security_group_id = module.api_service[0].ecs_security_group.id

}

```

  

**Why These Changes**:

- Creates separate security group rules for each service

- Uses count to conditionally create rules

- Uses array index `[0]` because modules now have count

- Both services can access the same RDS database

  

### Step 4: Update iam.tf

  

**File**: `/Users/tej/src/axomic/AXO373/modules/aws/services/AXO484/iam.tf`

  

**Current State**: References `module.api_service` directly

  

**Changes Required**:

  

#### Change 1: Update Task Execution Role Attachment (line 29)

```hcl

# FROM:

role = module.api_service.ecs_task_execution_role_name

# TO:

role = var.create_internal_service ? module.api_internal_service[0].ecs_task_execution_role_name : module.api_service[0].ecs_task_execution_role_name

```

  

#### Change 2: Update Task Role Attachment (line 61)

```hcl

# FROM:

role = module.api_service.ecs_task_role_name

# TO:

role = var.create_internal_service ? module.api_internal_service[0].ecs_task_role_name : module.api_service[0].ecs_task_role_name

```

  

#### Change 3: Add Additional Attachments (after line 63)

```hcl

# If both services exist, attach policies to both

resource "aws_iam_role_policy_attachment" "api_task_execution_both" {

count = var.create_internal_service && var.create_external_service ? 1 : 0

provider = aws.main

role = module.api_service[0].ecs_task_execution_role_name

policy_arn = aws_iam_policy.api_task_execution.arn

}

  

resource "aws_iam_role_policy_attachment" "api_task_both" {

count = var.create_internal_service && var.create_external_service ? 1 : 0

provider = aws.main

role = module.api_service[0].ecs_task_role_name

policy_arn = aws_iam_policy.api_task.arn

}

```

  

**Why These Changes**:

- Handles conditional module creation with count

- Ensures IAM policies are attached to whichever service exists

- When both services exist, attaches policies to both

  

### Step 5: Create outputs.tf (Optional but Recommended)

  

**File**: `/Users/tej/src/axomic/AXO373/modules/aws/services/AXO484/outputs.tf` (NEW FILE)

  

**Content**:

```hcl

output "internal_service_endpoint" {

description = "Internal service endpoint"

value = var.create_internal_service ? "${var.name}-internal.${var.parent_domain_name}" : null

}

  

output "external_service_endpoint" {

description = "External service endpoint"

value = var.create_external_service ? "${var.name}.${var.parent_domain_name}" : null

}

  

output "internal_service_name" {

description = "Internal ECS service name"

value = var.create_internal_service ? module.api_internal_service[0].service_name : null

}

  

output "external_service_name" {

description = "External ECS service name"

value = var.create_external_service ? module.api_service[0].service_name : null

}

  

output "database_name" {

description = "Database name"

value = module.db.db_name_ssm.value

}

```

  

### Step 6: Update Environment File - THE KEY CHANGE

  

**File**: `/Users/tej/src/axomic/AXO373/env/shredai/aws/oa_integration/main.tf`

  

**Current State**: Two separate module calls (lines 7-107)

- `module "axo484"` (lines 7-56)

- `module "axo484_private"` (lines 58-107)

  

**Action**: Delete BOTH module blocks and replace with ONE module call

  

**New Content** (replace lines 7-107):

```hcl

# Single module call creates both internal and external services

module "axo484" {

for_each = !local.in_production ? { this = "this" } : {}

  

source = "../../../../modules/aws/services/AXO484"

  

providers = {

aws.main = aws.use1

aws.master = aws.main_tf

postgresql = postgresql.use1

}

  

# Basic configuration

name = "axo484"

environment = local.stage

release = var.axo484_version

use_dev_settings = !local.in_production

  

# Container configuration

ecr_image = data.aws_ecr_image.this["axo484"]

ecr_repository_name = data.aws_ecr_repository.this["axo484"].name

  

# Domain configuration

parent_domain_name = local.zone_name

zone_id = local.zone_id

  

# Network configuration

vpc_id = data.aws_vpc.this.id

services_subnet_ids = [

data.aws_subnet.this["private_a"].id,

data.aws_subnet.this["private_b"].id,

data.aws_subnet.this["private_c"].id,

]

  

# Service dependencies

axo395_api_uri = "https://axo395.${local.zone_name}/api/v1/clients"

axo473_api_uri = "https://axo473.${local.zone_name}/api/v1/clients"

  

# RDS configuration (shared by both services)

rds_config = {

security_group_id = data.aws_security_group.rds.id

cluster_name = local.shredai_name

cluster_port = local.db_creds.port

cluster_endpoint = local.db_creds.endpoint

}

  

# ALB configurations - THIS IS THE KEY CHANGE

internal_alb_config = {

listener_arn = data.aws_lb_listener.private_443.arn

security_group_id = data.aws_security_group.alb_private.id

dns_name = data.aws_lb.private.dns_name

zone_id = data.aws_lb.private.zone_id

}

  

external_alb_config = {

listener_arn = data.aws_lb_listener.public_443.arn

security_group_id = data.aws_security_group.alb_public.id

dns_name = data.aws_lb.public.dns_name

zone_id = data.aws_lb.public.zone_id

}

  

# Security configuration

required_oa_jwt_claims = ["client_key"]

disable_cors = !local.in_production

debug = !local.in_production

# Ingress only needed for internal service (VPN access)

ingress_security_group_ids = [data.aws_security_group.vpn.id]

  

# Control which services to create (both by default)

create_internal_service = true

create_external_service = true

}

```

  

**Key Points**:

- ONE module call instead of two

- Passes BOTH `internal_alb_config` and `external_alb_config`

- Module internally decides what to create

- `ingress_security_group_ids` applies only to internal service

- Both services share the same database configuration

  

## What Gets Created

  

### Internal Service

- **ECS Service Name**: `axo484-internal`

- **DNS Endpoint**: `axo484-internal.shredapp.ai`

- **ALB**: Private ALB (internal-facing)

- **Access**: VPN and specified security groups only

- **Target Group**: New target group on private ALB listener

- **Container**: Same image as external service

- **Database**: Shared `axo484_db`

- **Environment Variable**: `SERVICE_TYPE=internal`

  

### External Service

- **ECS Service Name**: `axo484-external`

- **DNS Endpoint**: `axo484.shredapp.ai`

- **ALB**: Public ALB (internet-facing)

- **Access**: Internet accessible

- **Target Group**: New target group on public ALB listener

- **Container**: Same image as internal service

- **Database**: Shared `axo484_db`

- **Environment Variable**: `SERVICE_TYPE=external`

  

### Shared Resources

- **Database**: Single PostgreSQL database `axo484_db`

- **Database User**: Same user for both services

- **Database Password**: Same SSM parameter

- **ECR Repository**: Both services use same container image

- **VPC/Subnets**: Both run in same private subnets

- **IAM Policies**: Shared policies for database access

  

## Testing and Verification

  

### Pre-deployment Checklist

1. Backup current Terraform state

2. Review all changes in a separate branch

3. Run `terraform fmt` to ensure proper formatting

4. Run `terraform validate` to check syntax

  

### Terraform Plan

```bash

cd env/shredai/aws/oa_integration

terraform plan -target=module.axo484 -out=axo484.plan

```

  

### Expected Plan Output

- **To be created**:

- `module.axo484.module.api_internal_service[0]`

- `module.axo484.module.api_service[0]` (modified from existing)

- New security group rules

- New IAM role attachments

- New Route53 records

  

### Apply Changes

```bash

terraform apply axo484.plan

```

  

### Post-deployment Verification

```bash

# 1. Check ECS services

aws ecs list-services --cluster your-cluster-name --region us-east-1

  

# 2. Check Route53 records

aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID | grep axo484

  

# 3. Test internal endpoint (from VPN or bastion)

curl -X GET https://axo484-internal.shredapp.ai/healthz

  

# 4. Test external endpoint (from internet)

curl -X GET https://axo484.shredapp.ai/healthz

  

# 5. Verify database connectivity

# Check CloudWatch logs for both services

```

  

## Rollback Procedure

  

If issues occur:

  

### Option 1: Disable Services

```hcl

# In environment file, set:

create_internal_service = false

create_external_service = false

  

# Apply to remove services

terraform apply

```

  

### Option 2: Full Rollback

1. Restore original files from git

2. Run terraform apply to restore previous state

3. Verify services are working

  

## Summary Metrics

  

### Files Modified: 6

1. `variables.tf` - Add 4 new variables

2. `ecs.tf` - Add internal service, modify external

3. `security_groups.tf` - Handle both services

4. `iam.tf` - Handle conditional modules

5. `outputs.tf` - New file for outputs

6. `env/.../main.tf` - Single module call

  

### Lines of Code

- **Added**: ~120 lines

- **Modified**: ~20 lines

- **Deleted**: ~100 lines (duplicate module in env file)

- **Net Change**: +40 lines

  

### Complexity

- **Low**: Following established pattern

- **Risk**: Minimal with proper testing

- **Rollback**: Easy with feature flags

  

## Success Criteria

1. ✓ ONE module invocation in environment file

2. ✓ Module creates BOTH services internally

3. ✓ Minimal code changes

4. ✓ Follows AXO431 pattern

5. ✓ Both services share same database

6. ✓ Services can be toggled on/off

7. ✓ No breaking changes to existing infrastructure

  

## Notes and Considerations

  

### Database Sharing

- Both services naturally share the same database

- No special configuration needed

- Database module creates one database used by both

  

### Security Considerations

- Internal service: VPN access only

- External service: Internet accessible

- Both have separate security groups

- Database allows connections from both

  

### Future Enhancements

- Add service mesh for internal communication

- Implement rate limiting on external service

- Add monitoring dashboards for both services

- Consider adding a third "admin" service

  

This plan provides a complete, detailed implementation guide that follows the established patterns while keeping changes minimal and focused.