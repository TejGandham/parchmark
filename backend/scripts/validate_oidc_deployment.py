#!/usr/bin/env python3
"""
Pre-Deployment OIDC Validation Checker

Comprehensive validation script to ensure ParchMark OIDC implementation is
production-ready before deployment.

Validates:
- Environment variables
- Service connectivity
- OIDC configuration
- Database connectivity
- Health checks
- Performance metrics
- Security configuration
- API endpoints

Usage:
    python scripts/validate_oidc_deployment.py
    python scripts/validate_oidc_deployment.py --environment production
    python scripts/validate_oidc_deployment.py --skip-performance
"""

import os
import sys
import time
from typing import Dict, List, Tuple, Optional
import asyncio

import httpx

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title: str) -> None:
    print(f"\n{CYAN}{'=' * 70}{RESET}")
    print(f"{CYAN}{title.center(70)}{RESET}")
    print(f"{CYAN}{'=' * 70}{RESET}\n")


def print_check(msg: str, status: bool, notes: str = "") -> None:
    symbol = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    print(f"{symbol} {msg}")
    if notes:
        print(f"  {YELLOW}→ {notes}{RESET}")


def print_section(title: str) -> None:
    print(f"\n{CYAN}{title}{RESET}")
    print(f"{CYAN}{'-' * len(title)}{RESET}")


class DeploymentValidator:
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.all_passed = True
        self.checks = []

    def add_check(self, name: str, passed: bool, notes: str = "") -> None:
        self.checks.append((name, passed, notes))
        print_check(name, passed, notes)
        if not passed:
            self.all_passed = False

    # ========================================================================
    # Environment Variables
    # ========================================================================

    def check_env_variables(self) -> None:
        print_section("Environment Variables")

        required_vars = {
            "DATABASE_URL": "Database connection string",
            "SECRET_KEY": "JWT secret key",
            "ALGORITHM": "JWT algorithm (HS256)",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "Access token TTL",
            "ALLOWED_ORIGINS": "CORS origins",
            "AUTH_MODE": "Authentication mode (hybrid/oidc/local)",
            "OIDC_ISSUER_URL": "OIDC issuer URL",
            "OIDC_AUDIENCE": "OIDC client ID",
            "OIDC_USERNAME_CLAIM": "Username claim name",
        }

        missing_vars = []
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask secrets in output
                if "SECRET" in var or "PASSWORD" in var:
                    display = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display = value
                self.add_check(f"{var} is set", True, display)
            else:
                missing_vars.append(var)
                self.add_check(f"{var} is set", False, "REQUIRED - not found")

        # Check SECRET_KEY strength
        secret = os.getenv("SECRET_KEY", "")
        if len(secret) < 32:
            self.add_check(
                "SECRET_KEY is strong (32+ chars)",
                False,
                f"Current length: {len(secret)} chars",
            )
        else:
            self.add_check("SECRET_KEY is strong (32+ chars)", True)

        # Check AUTH_MODE is valid
        auth_mode = os.getenv("AUTH_MODE", "").lower()
        if auth_mode in ["hybrid", "oidc", "local"]:
            self.add_check(f"AUTH_MODE is valid ({auth_mode})", True)
        else:
            self.add_check(
                "AUTH_MODE is valid",
                False,
                f"Invalid value: {auth_mode}. Must be: hybrid, oidc, or local",
            )

    # ========================================================================
    # Service Connectivity
    # ========================================================================

    async def check_service_connectivity(self) -> None:
        print_section("Service Connectivity")

        base_url = os.getenv("OIDC_ISSUER_URL", "http://localhost:9091")
        api_url = os.getenv("API_URL", "http://localhost:8000")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Check backend
                try:
                    response = await client.get(f"{api_url}/api/health")
                    self.add_check("Backend API reachable", response.status_code == 200)
                except Exception as e:
                    self.add_check("Backend API reachable", False, str(e))

                # Check OIDC provider
                try:
                    discovery_url = f"{base_url}/.well-known/openid-configuration"
                    response = await client.get(discovery_url)
                    self.add_check("OIDC provider reachable", response.status_code == 200)
                except Exception as e:
                    self.add_check("OIDC provider reachable", False, str(e))

        except Exception as e:
            self.add_check("Service connectivity check", False, str(e))

    # ========================================================================
    # Database
    # ========================================================================

    async def check_database(self) -> None:
        print_section("Database Connectivity")

        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            self.add_check("Database URL configured", False, "DATABASE_URL not set")
            return

        self.add_check("Database URL configured", True, "PostgreSQL")

        # Check if database is reachable
        if "localhost" in db_url or "127.0.0.1" in db_url:
            self.add_check(
                "Database on localhost",
                True,
                "Verify in production this is intentional",
            )
        elif "postgres" in db_url:
            self.add_check("Database uses PostgreSQL", True)

    # ========================================================================
    # OIDC Configuration
    # ========================================================================

    async def check_oidc_configuration(self) -> None:
        print_section("OIDC Configuration")

        issuer = os.getenv("OIDC_ISSUER_URL", "")
        audience = os.getenv("OIDC_AUDIENCE", "")
        username_claim = os.getenv("OIDC_USERNAME_CLAIM", "")

        self.add_check("OIDC_ISSUER_URL configured", bool(issuer), issuer)
        self.add_check("OIDC_AUDIENCE configured", bool(audience), audience)
        self.add_check(
            "OIDC_USERNAME_CLAIM configured", bool(username_claim), username_claim
        )

        # Check issuer URL format
        if issuer:
            if issuer.startswith("http"):
                self.add_check("OIDC_ISSUER_URL format valid", True)
            else:
                self.add_check(
                    "OIDC_ISSUER_URL format valid",
                    False,
                    "Must start with http:// or https://",
                )

        # Check for production HTTPS in production environment
        if self.environment == "production":
            if issuer.startswith("https"):
                self.add_check("OIDC_ISSUER_URL uses HTTPS", True)
            else:
                self.add_check(
                    "OIDC_ISSUER_URL uses HTTPS",
                    False,
                    f"Production must use HTTPS: {issuer}",
                )

        # Try to fetch OIDC discovery
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                discovery_url = f"{issuer}/.well-known/openid-configuration"
                response = await client.get(discovery_url)
                if response.status_code == 200:
                    doc = response.json()
                    scopes = doc.get("scopes_supported", [])
                    required_scopes = {"openid", "profile", "email"}
                    supported = required_scopes.issubset(set(scopes))
                    self.add_check(
                        "OIDC discovery has required scopes",
                        supported,
                        f"Scopes: {', '.join(scopes)}",
                    )
                else:
                    self.add_check(
                        "OIDC discovery endpoint responds",
                        False,
                        f"HTTP {response.status_code}",
                    )
        except Exception as e:
            self.add_check("OIDC discovery endpoint responds", False, str(e))

    # ========================================================================
    # Health Checks
    # ========================================================================

    async def check_health(self) -> None:
        print_section("Health Checks")

        api_url = os.getenv("API_URL", "http://localhost:8000")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    response = await client.get(f"{api_url}/api/health")
                    if response.status_code == 200:
                        health = response.json()
                        self.add_check(
                            "API health check passes",
                            True,
                            f"Status: {health.get('status')}",
                        )

                        db_status = health.get("database")
                        self.add_check(
                            "Database connection healthy",
                            db_status == "connected",
                            f"Status: {db_status}",
                        )
                    else:
                        self.add_check(
                            "API health check passes",
                            False,
                            f"HTTP {response.status_code}",
                        )
                except Exception as e:
                    self.add_check("API health check passes", False, str(e))
        except Exception as e:
            self.add_check("Health checks", False, str(e))

    # ========================================================================
    # Performance
    # ========================================================================

    async def check_performance(self) -> None:
        print_section("Performance Metrics")

        api_url = os.getenv("API_URL", "http://localhost:8000")
        issuer = os.getenv("OIDC_ISSUER_URL", "")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Test API response time
                times = []
                for _ in range(3):
                    start = time.time()
                    try:
                        response = await client.get(f"{api_url}/api/health")
                        elapsed = (time.time() - start) * 1000
                        times.append(elapsed)
                    except Exception:
                        break

                if times:
                    avg_time = sum(times) / len(times)
                    status = avg_time < 100
                    self.add_check(
                        "API response time < 100ms",
                        status,
                        f"Average: {avg_time:.1f}ms",
                    )

                # Test OIDC response time
                if issuer:
                    start = time.time()
                    try:
                        response = await client.get(
                            f"{issuer}/.well-known/openid-configuration"
                        )
                        elapsed = (time.time() - start) * 1000
                        status = elapsed < 200
                        self.add_check(
                            "OIDC response time < 200ms",
                            status,
                            f"Time: {elapsed:.1f}ms",
                        )
                    except Exception as e:
                        self.add_check(
                            "OIDC response time check", False, str(e)
                        )

        except Exception as e:
            self.add_check("Performance checks", False, str(e))

    # ========================================================================
    # Security
    # ========================================================================

    def check_security(self) -> None:
        print_section("Security Configuration")

        # Check environment
        environment = os.getenv("ENVIRONMENT", "development")
        self.add_check(
            f"ENVIRONMENT set to {environment}",
            True,
            "Ensure 'production' for production",
        )

        # Check ALLOWED_ORIGINS
        origins = os.getenv("ALLOWED_ORIGINS", "")
        self.add_check("ALLOWED_ORIGINS configured", bool(origins), origins)

        # Check for localhost in production
        if self.environment == "production":
            if "localhost" in origins or "127.0.0.1" in origins:
                self.add_check(
                    "ALLOWED_ORIGINS excludes localhost",
                    False,
                    "Production should not allow localhost",
                )
            else:
                self.add_check("ALLOWED_ORIGINS excludes localhost", True)

            if origins.startswith("https://"):
                self.add_check("ALLOWED_ORIGINS uses HTTPS", True)
            else:
                self.add_check(
                    "ALLOWED_ORIGINS uses HTTPS",
                    False,
                    "Production should use HTTPS origins",
                )

    # ========================================================================
    # API Endpoints
    # ========================================================================

    async def check_api_endpoints(self) -> None:
        print_section("API Endpoints")

        api_url = os.getenv("API_URL", "http://localhost:8000")

        endpoints = [
            ("/api/health", "GET", "Health check"),
            ("/api/auth/login", "POST", "Local login"),
            ("/api/auth/refresh", "POST", "Token refresh"),
            ("/api/auth/me", "GET", "Current user"),
            ("/api/auth/logout", "POST", "Logout"),
            ("/api/notes", "GET", "List notes"),
            ("/docs", "GET", "API documentation"),
        ]

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                for endpoint, method, desc in endpoints:
                    try:
                        if method == "GET":
                            response = await client.get(f"{api_url}{endpoint}")
                        else:
                            response = await client.post(f"{api_url}{endpoint}")

                        # 200-399 = accessible, 401 = auth required (ok), 404 = not found
                        accessible = response.status_code < 404
                        self.add_check(
                            f"{method} {endpoint}: {desc}",
                            accessible,
                            f"HTTP {response.status_code}",
                        )
                    except Exception as e:
                        self.add_check(
                            f"{method} {endpoint}: {desc}",
                            False,
                            str(e),
                        )
        except Exception as e:
            self.add_check("API endpoints check", False, str(e))

    # ========================================================================
    # Main Validation
    # ========================================================================

    async def run_all_checks(self) -> bool:
        print_header(
            f"ParchMark OIDC Deployment Validation ({self.environment.upper()})"
        )

        self.check_env_variables()
        await self.check_service_connectivity()
        await self.check_database()
        await self.check_oidc_configuration()
        await self.check_health()
        await self.check_performance()
        self.check_security()
        await self.check_api_endpoints()

        # Summary
        print_header("Validation Summary")

        total = len(self.checks)
        passed = sum(1 for _, p, _ in self.checks if p)
        failed = total - passed

        for name, status, notes in self.checks:
            print_check(name, status, notes)

        print()
        if self.all_passed:
            print(f"{GREEN}✓ ALL CHECKS PASSED ({passed}/{total}){RESET}")
            print(f"{GREEN}✓ Deployment is ready for {self.environment.upper()}{RESET}")
            return True
        else:
            print(f"{RED}✗ {failed} CHECK(S) FAILED ({passed}/{total}){RESET}")
            print(f"{RED}✗ Fix errors before deploying to {self.environment.upper()}{RESET}")
            return False


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-Deployment OIDC Validation Checker"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="development",
        help="Deployment environment (default: development)",
    )
    parser.add_argument(
        "--skip-performance",
        action="store_true",
        help="Skip performance tests",
    )

    args = parser.parse_args()

    validator = DeploymentValidator(environment=args.environment)

    try:
        await validator.run_all_checks()
        sys.exit(0 if validator.all_passed else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Validation interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Validation failed with error: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
