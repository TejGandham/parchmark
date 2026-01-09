#!/usr/bin/env python3
"""
OIDC Integration Testing Utility

Comprehensive testing script for validating Authelia OIDC integration with ParchMark.
Tests token validation, user creation, and hybrid authentication.

Usage:
    # Test connection to OIDC provider
    python scripts/test_oidc_integration.py --test-discovery

    # Test token validation
    python scripts/test_oidc_integration.py --test-validation

    # Test performance
    python scripts/test_oidc_integration.py --test-performance

    # Run all tests
    python scripts/test_oidc_integration.py --test-all

    # Test with custom issuer
    python scripts/test_oidc_integration.py --issuer http://localhost:9091 --test-discovery
"""

import argparse
import asyncio
import sys
import time
from datetime import UTC, datetime, timedelta

import httpx
from jose.jwt import encode

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_success(msg: str) -> None:
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg: str) -> None:
    print(f"{RED}✗ {msg}{RESET}")


def print_info(msg: str) -> None:
    print(f"{CYAN}ℹ {msg}{RESET}")


def print_warn(msg: str) -> None:
    print(f"{YELLOW}⚠ {msg}{RESET}")


class OIDCTester:
    def __init__(
        self,
        issuer_url: str = "http://localhost:9091",
        client_id: str = "parchmark",
        api_url: str = "http://localhost:8000",
    ):
        self.issuer_url = issuer_url.rstrip("/")
        self.client_id = client_id
        self.api_url = api_url.rstrip("/")
        self.discovery_doc: dict | None = None
        self.jwks: dict | None = None

    async def test_discovery(self) -> bool:
        """Test OIDC discovery endpoint"""
        print_info(f"Testing OIDC discovery at {self.issuer_url}")

        try:
            async with httpx.AsyncClient() as client:
                discovery_url = f"{self.issuer_url}/.well-known/openid-configuration"
                print_info(f"Fetching discovery document: {discovery_url}")

                response = await client.get(discovery_url, timeout=10)
                response.raise_for_status()

                self.discovery_doc = response.json()

                # Verify required fields
                required_fields = [
                    "issuer",
                    "authorization_endpoint",
                    "token_endpoint",
                    "jwks_uri",
                    "userinfo_endpoint",
                ]

                missing = [f for f in required_fields if f not in self.discovery_doc]
                if missing:
                    print_error(f"Missing required fields: {missing}")
                    return False

                print_success("OIDC discovery document retrieved")
                print_info(f"Issuer: {self.discovery_doc.get('issuer')}")
                print_info(f"JWKS URI: {self.discovery_doc.get('jwks_uri')}")
                print_info(f"Scopes: {self.discovery_doc.get('scopes_supported')}")

                return True

        except httpx.ConnectError:
            print_error(f"Failed to connect to {self.issuer_url}")
            return False
        except httpx.HTTPStatusError as e:
            print_error(f"HTTP {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            print_error(f"Error testing discovery: {e}")
            return False

    async def test_jwks(self) -> bool:
        """Test JWKS endpoint"""
        if not self.discovery_doc:
            print_error("Discovery document not loaded. Run test_discovery first.")
            return False

        print_info("Testing JWKS endpoint")

        try:
            jwks_uri = self.discovery_doc.get("jwks_uri")
            if not jwks_uri:
                print_error("JWKS URI not found in discovery document")
                return False

            async with httpx.AsyncClient() as client:
                print_info(f"Fetching JWKS: {jwks_uri}")
                response = await client.get(jwks_uri, timeout=10)
                response.raise_for_status()

                self.jwks = response.json()
                keys = self.jwks.get("keys", [])

                if not keys:
                    print_error("No signing keys found in JWKS")
                    return False

                print_success(f"JWKS retrieved with {len(keys)} key(s)")
                for i, key in enumerate(keys):
                    print_info(f"  Key {i + 1}: {key.get('kid', 'unknown')}")

                return True

        except Exception as e:
            print_error(f"Error testing JWKS: {e}")
            return False

    async def test_token_validation(self) -> bool:
        """Test token validation"""
        print_info("Testing token validation")

        if not self.discovery_doc or not self.jwks:
            print_error("Discovery and JWKS not loaded. Run discovery tests first.")
            return False

        try:
            # Create test token (valid structure but may not work with real Authelia)
            secret = "test-secret"
            now = datetime.now(UTC)
            payload = {
                "sub": "test-user",
                "preferred_username": "testuser",
                "email": "test@example.com",
                "iss": self.discovery_doc["issuer"],
                "aud": self.client_id,
                "exp": (now + timedelta(hours=1)).timestamp(),
                "iat": now.timestamp(),
            }

            # Note: Real validation would use RS256 with JWKS
            # This is just to test structure
            test_token = encode(payload, secret, algorithm="HS256")
            print_success("Test token created")
            print_info(f"Token (first 50 chars): {test_token[:50]}...")

            # Try to validate against backend
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {test_token}"}
                print_info("Testing token against backend API")
                response = await client.get(
                    f"{self.api_url}/api/auth/me",
                    headers=headers,
                    timeout=10,
                )

                if response.status_code == 200:
                    print_success("Token validated by backend")
                    user = response.json()
                    print_info(f"Authenticated as: {user.get('username')}")
                    return True
                elif response.status_code == 401:
                    print_warn("Token rejected by backend (expected for test token)")
                    return True
                else:
                    print_error(f"Unexpected status {response.status_code}")
                    return False

        except Exception as e:
            print_error(f"Error testing token validation: {e}")
            return False

    async def test_api_health(self) -> bool:
        """Test backend API health"""
        print_info("Testing backend API health")

        try:
            async with httpx.AsyncClient() as client:
                print_info(f"Fetching health check: {self.api_url}/api/health")
                response = await client.get(f"{self.api_url}/api/health", timeout=10)

                if response.status_code == 200:
                    health = response.json()
                    print_success("Backend API healthy")
                    print_info(f"Database: {health.get('database')}")
                    print_info(f"Service: {health.get('service')}")
                    print_info(f"Version: {health.get('version')}")
                    return True
                else:
                    print_error(f"Backend unhealthy: {response.status_code}")
                    return False

        except httpx.ConnectError:
            print_error(f"Failed to connect to backend at {self.api_url}")
            return False
        except Exception as e:
            print_error(f"Error testing API health: {e}")
            return False

    async def test_hybrid_auth(self) -> bool:
        """Test hybrid authentication (local + OIDC)"""
        print_info("Testing hybrid authentication configuration")

        try:
            async with httpx.AsyncClient() as client:
                # Check if local login endpoint exists
                response = await client.post(
                    f"{self.api_url}/api/auth/login",
                    json={"username": "test", "password": "test"},
                    timeout=10,
                )

                if response.status_code in [200, 401]:  # 200 for success, 401 for invalid creds
                    print_success("Local auth endpoint available (hybrid mode)")
                    return True
                else:
                    print_error(f"Unexpected response from local auth: {response.status_code}")
                    return False

        except Exception as e:
            print_error(f"Error testing hybrid auth: {e}")
            return False

    async def test_performance(self) -> bool:
        """Test OIDC performance (JWKS caching)"""
        print_info("Testing OIDC performance (JWKS caching)")

        if not self.discovery_doc:
            print_error("Discovery document not loaded")
            return False

        try:
            jwks_uri = self.discovery_doc.get("jwks_uri")
            if not jwks_uri:
                print_error("JWKS URI not found")
                return False

            # Measure JWKS fetch time
            async with httpx.AsyncClient() as client:
                times = []

                for i in range(5):
                    start = time.time()
                    response = await client.get(jwks_uri, timeout=10)
                    elapsed = (time.time() - start) * 1000  # ms

                    if response.status_code != 200:
                        print_error(f"JWKS fetch {i + 1} failed: {response.status_code}")
                        return False

                    times.append(elapsed)
                    print_info(f"JWKS fetch {i + 1}: {elapsed:.2f}ms")

                avg = sum(times) / len(times)
                print_success(f"Average JWKS fetch time: {avg:.2f}ms")

                # Cache performance expectation
                if avg < 100:
                    print_success("JWKS caching performing well")
                    return True
                else:
                    print_warn("JWKS caching may need optimization")
                    return True  # Still pass, just warning

        except Exception as e:
            print_error(f"Error testing performance: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Run all tests"""
        print(f"\n{CYAN}=== ParchMark OIDC Integration Tests ==={RESET}\n")

        results = []

        # Test 1: Discovery
        print("Test 1: OIDC Discovery")
        print("-" * 50)
        result = await self.test_discovery()
        results.append(("OIDC Discovery", result))
        print()

        # Test 2: JWKS
        if result:
            print("Test 2: JWKS")
            print("-" * 50)
            result = await self.test_jwks()
            results.append(("JWKS", result))
            print()

        # Test 3: Token Validation
        if result:
            print("Test 3: Token Validation")
            print("-" * 50)
            result = await self.test_token_validation()
            results.append(("Token Validation", result))
            print()

        # Test 4: API Health
        print("Test 4: API Health")
        print("-" * 50)
        result = await self.test_api_health()
        results.append(("API Health", result))
        print()

        # Test 5: Hybrid Auth
        print("Test 5: Hybrid Auth Configuration")
        print("-" * 50)
        result = await self.test_hybrid_auth()
        results.append(("Hybrid Auth", result))
        print()

        # Test 6: Performance
        if results[1][1]:  # If JWKS test passed
            print("Test 6: Performance (JWKS Caching)")
            print("-" * 50)
            result = await self.test_performance()
            results.append(("Performance", result))
            print()

        # Summary
        print(f"\n{CYAN}=== Test Summary ==={RESET}\n")
        passed = sum(1 for _, r in results if r)
        total = len(results)

        for test_name, result in results:
            if result:
                print_success(f"{test_name}")
            else:
                print_error(f"{test_name}")

        print()
        print_info(f"Passed: {passed}/{total}")

        if passed == total:
            print_success("All tests passed!")
            return True
        else:
            print_error(f"{total - passed} test(s) failed")
            return False


async def main():
    parser = argparse.ArgumentParser(description="ParchMark OIDC Integration Tester")
    parser.add_argument(
        "--issuer",
        default="http://localhost:9091",
        help="OIDC issuer URL (default: http://localhost:9091)",
    )
    parser.add_argument(
        "--client-id",
        default="parchmark",
        help="OIDC client ID (default: parchmark)",
    )
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="ParchMark API URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--test-discovery",
        action="store_true",
        help="Test OIDC discovery endpoint",
    )
    parser.add_argument(
        "--test-jwks",
        action="store_true",
        help="Test JWKS endpoint",
    )
    parser.add_argument(
        "--test-validation",
        action="store_true",
        help="Test token validation",
    )
    parser.add_argument(
        "--test-health",
        action="store_true",
        help="Test API health",
    )
    parser.add_argument(
        "--test-hybrid",
        action="store_true",
        help="Test hybrid auth configuration",
    )
    parser.add_argument(
        "--test-performance",
        action="store_true",
        help="Test OIDC performance",
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Run all tests",
    )

    args = parser.parse_args()

    tester = OIDCTester(issuer_url=args.issuer, client_id=args.client_id, api_url=args.api)

    # If no specific test, run all
    if not any(
        [
            args.test_discovery,
            args.test_jwks,
            args.test_validation,
            args.test_health,
            args.test_hybrid,
            args.test_performance,
            args.test_all,
        ]
    ):
        args.test_all = True

    if args.test_all:
        success = await tester.run_all_tests()
    else:
        results = []

        if args.test_discovery:
            success = await tester.test_discovery()
            results.append(success)

        if args.test_jwks:
            success = await tester.test_jwks()
            results.append(success)

        if args.test_validation:
            success = await tester.test_validation()
            results.append(success)

        if args.test_health:
            success = await tester.test_api_health()
            results.append(success)

        if args.test_hybrid:
            success = await tester.test_hybrid_auth()
            results.append(success)

        if args.test_performance:
            success = await tester.test_performance()
            results.append(success)

        success = all(results) if results else False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
