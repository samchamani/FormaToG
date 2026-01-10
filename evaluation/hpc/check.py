import argparse
import time
import requests
import sys


def check_service(url, target_code, timeout, interval):
    start_time = time.time()
    print(f"Checking {url} for status {target_code} (Timeout: {timeout}s)...")
    while (time.time() - start_time) < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == target_code:
                print(f"Status is {response.status_code}!")
                sys.exit(0)
            else:
                print(f"Got status {response.status_code}, expected {target_code}")
        except requests.exceptions.ConnectionError:
            print("Connection refused (Service not ready)")
        except requests.exceptions.ReadTimeout:
            print("Connection timed out")
        except Exception as e:
            print(f"Warning: Unexpected error: {e}")
        print("Waiting...")
        time.sleep(interval)
    print(f"ERROR: Timed out after {timeout} seconds. Service {url} is not ready.")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wait for a URL to return a specific status code."
    )
    parser.add_argument(
        "--url", required=True, help="The URL to check (e.g., http://localhost:7474)"
    )
    parser.add_argument(
        "--code", type=int, default=200, help="The expected status code (default: 200)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Max wait time in seconds (default: 300)",
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="Check interval in seconds (default: 5)"
    )

    args = parser.parse_args()
    check_service(args.url, args.code, args.timeout, args.interval)
