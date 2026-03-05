#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx[socks]", "rich"]
# ///
"""Felo AI CLI - AI-powered conversational search with real-time web results."""

import argparse
import os
import sys
import json
import time
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()
stderr_console = Console(stderr=True)

# Configuration from environment variables
FELO_API_KEY = os.getenv("FELO_API_KEY", "").strip()
FELO_API_URL = "https://openapi.felo.ai/v2/chat"

# Proxy configuration - supports HTTP, HTTPS, and SOCKS5
# Only use proxy if FELO_PROXY environment variable is set (non-empty)
FELO_PROXY = os.getenv("FELO_PROXY", "").strip()
PROXY = FELO_PROXY if FELO_PROXY else None

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # Initial delay in seconds
RETRY_BACKOFF = 2  # Exponential backoff multiplier

# Query constants
QUERY_MAX_LENGTH = 2000

# HTTP constants
TIMEOUT_SECONDS = 60

# Display constants
URL_DISPLAY_MAX_LEN = 50
TITLE_DISPLAY_MAX_LEN = 50
SNIPPET_DISPLAY_MAX_LEN = 50


def _calculate_delay(attempt: int) -> float:
    """Calculate retry delay with exponential backoff."""
    return RETRY_DELAY * (RETRY_BACKOFF ** attempt)


def chat(query: str, output_format: str = "table", max_retries: int = MAX_RETRIES) -> dict:
    """
    Call Felo Chat API to get AI-powered answer with web sources.

    Args:
        query: Search query string (1-2000 characters)
        output_format: Output format (table, json)
        max_retries: Maximum number of retries for transient errors

    Returns:
        Dict with answer, resources, and query analysis
    """
    # Validate configuration
    if not FELO_API_KEY:
        stderr_console.print(
            "[red]Error:[/red] FELO_API_KEY environment variable is not set."
        )
        stderr_console.print(
            "[dim]Please set your Felo API Key:[/dim]"
        )
        stderr_console.print(
            "  export FELO_API_KEY=your_api_key_here"
        )
        stderr_console.print(
            "[dim]Get your API key from: https://felo.ai[/dim]"
        )
        return {"error": "FELO_API_KEY not configured"}

    # Validate query
    if not query or not query.strip():
        stderr_console.print(
            "[red]Error:[/red] Query cannot be empty."
        )
        return {"error": "Empty query"}

    query = query.strip()
    if len(query) > QUERY_MAX_LENGTH:
        stderr_console.print(
            f"[red]Error:[/red] Query exceeds {QUERY_MAX_LENGTH} characters limit."
        )
        return {"error": f"Query too long (max {QUERY_MAX_LENGTH} characters)"}

    headers = {
        "Authorization": f"Bearer {FELO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "query": query
    }

    # Retry logic with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            response = httpx.post(
                FELO_API_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT_SECONDS,
                verify=True,
                proxy=PROXY
            )

            # Handle specific error codes
            if response.status_code == 401:
                stderr_console.print(
                    "[red]Authentication failed:[/red] Invalid API Key."
                )
                stderr_console.print(
                    "[dim]Please check your FELO_API_KEY configuration.[/dim]"
                )
                return {"error": "Authentication failed (401)"}

            if response.status_code == 429:
                stderr_console.print(
                    "[red]Rate limit exceeded:[/red] Too many requests."
                )
                stderr_console.print(
                    "[dim]Felo AI allows 100 requests per minute. Please wait and try again.[/dim]"
                )
                return {"error": "Rate limit exceeded (429)"}

            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Invalid request parameters")
                stderr_console.print(
                    f"[red]Bad Request:[/red] {error_msg}"
                )
                return {"error": f"Bad request (400): {error_msg}"}

            # Retry on 5xx server errors
            if response.status_code >= 500:
                if attempt < max_retries:
                    delay = _calculate_delay(attempt)
                    stderr_console.print(
                        f"[yellow]Server error {response.status_code}, retrying in {delay}s...[/yellow]"
                    )
                    time.sleep(delay)
                    continue

            response.raise_for_status()

            result = response.json()

            # Check for Felo API error response structure
            if isinstance(result, dict) and result.get("status") == "error":
                error_code = result.get("code", "UNKNOWN_ERROR")
                error_msg = result.get("message", "Unknown error occurred")
                request_id = result.get("request_id", "")

                # Map error codes to user-friendly messages
                error_messages = {
                    "INVALID_API_KEY": "Invalid API Key. Please check your FELO_API_KEY.",
                    "EXPIRED_API_KEY": "API Key has expired. Please generate a new API Key from your account settings.",
                    "MISSING_AUTHORIZATION": "Authorization header is missing.",
                    "MALFORMED_AUTHORIZATION": "Authorization header format is incorrect. Use: Bearer YOUR_API_KEY",
                    "MISSING_PARAMETER": "Required parameter is missing.",
                    "INVALID_PARAMETER": "Invalid parameter value.",
                    "QUERY_TOO_LONG": f"Query exceeds {QUERY_MAX_LENGTH} characters limit.",
                    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please slow down your requests.",
                    "CHAT_FAILED": "Internal service error. Please retry.",
                    "SERVICE_UNAVAILABLE": "Service temporarily unavailable. Please wait and retry."
                }

                user_msg = error_messages.get(error_code, error_msg)
                stderr_console.print(f"[red]Error:[/red] {user_msg}")
                if request_id:
                    stderr_console.print(f"[dim]Request ID: {request_id}[/dim]")
                return {"error": f"{error_code}: {error_msg}", "request_id": request_id}

            # Felo API returns successful data in nested "data" field
            if isinstance(result, dict) and "data" in result:
                return result["data"]
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500 and attempt < max_retries:
                delay = _calculate_delay(attempt)
                stderr_console.print(
                    f"[yellow]Server error {e.response.status_code}, retrying in {delay}s...[/yellow]"
                )
                time.sleep(delay)
                continue
            stderr_console.print(
                f"[red]HTTP Error:[/red] {e.response.status_code} - {e.response.reason_phrase}"
            )
            return {"error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}"}
        except httpx.ConnectError as e:
            if attempt < max_retries:
                delay = _calculate_delay(attempt)
                stderr_console.print(
                    f"[yellow]Connection error, retrying in {delay}s...[/yellow]"
                )
                time.sleep(delay)
                continue
            stderr_console.print(
                f"[red]Connection Error:[/red] Unable to connect to Felo AI API"
            )
            stderr_console.print(
                "[dim]Please check your network connection.[/dim]"
            )
            return {"error": f"Connection error: {e}"}
        except httpx.TimeoutException as e:
            if attempt < max_retries:
                delay = _calculate_delay(attempt)
                stderr_console.print(
                    f"[yellow]Request timeout, retrying in {delay}s...[/yellow]"
                )
                time.sleep(delay)
                continue
            stderr_console.print(
                "[red]Timeout Error:[/red] Request timed out. Felo AI may be experiencing high load."
            )
            return {"error": "Request timeout"}
        except httpx.HTTPError as e:
            stderr_console.print(
                f"[red]HTTP Error:[/red] {e}"
            )
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            stderr_console.print(
                "[red]Error:[/red] Failed to parse API response."
            )
            return {"error": f"Invalid JSON response: {e}"}
        except Exception as e:
            stderr_console.print(
                f"[red]Unexpected error:[/red] {e}"
            )
            return {"error": str(e)}

    # If we've exhausted all retries
    return {"error": "Max retries exceeded"}


def display_result_table(data: dict, query: str):
    """Display Felo AI response in a rich formatted table."""
    if "error" in data:
        return

    answer = data.get("answer", "")
    resources = data.get("resources", [])
    query_analysis = data.get("query_analysis", {})
    message_id = data.get("message_id", data.get("id", ""))

    # Display query info
    if query_analysis:
        optimized_query = query_analysis.get("optimized_query", "")
        if optimized_query and optimized_query != query:
            rprint(f"[dim]Original query:[/dim] {query}")
            rprint(f"[dim]Optimized query:[/dim] [cyan]{optimized_query}[/cyan]")
            print()

    # Display answer in a panel
    if answer:
        rprint(Panel(
            answer,
            title="[bold green]Felo AI Answer[/bold green]",
            title_align="left",
            border_style="green"
        ))
    else:
        rprint("[yellow]No answer received from Felo AI.[/yellow]")

    # Display resources table
    if resources:
        print()
        table = Table(
            title="[bold blue]Sources[/bold blue]",
            show_lines=True,
            header_style="bold blue"
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="bold", width=40)
        table.add_column("URL", style="blue", width=50)
        table.add_column("Summary", style="dim", width=40)

        # Build table and details in single iteration
        for i, resource in enumerate(resources, 1):
            title = resource.get("title", "No title")
            url = resource.get("link", resource.get("url", ""))
            snippet = resource.get("snippet", resource.get("summary", ""))

            # Truncate for table display
            title_display = title[:TITLE_DISPLAY_MAX_LEN] + "..." if len(title) > TITLE_DISPLAY_MAX_LEN else title
            url_display = url[:URL_DISPLAY_MAX_LEN] + "..." if len(url) > URL_DISPLAY_MAX_LEN else url
            summary_display = snippet[:SNIPPET_DISPLAY_MAX_LEN] + "..." if len(snippet) > SNIPPET_DISPLAY_MAX_LEN else snippet

            table.add_row(str(i), title_display, url_display, summary_display)

        console.print(table)

        # Display full resource details
        rprint("\n[bold]Source Details:[/bold]")
        for i, resource in enumerate(resources, 1):
            title = resource.get("title", "No title")
            url = resource.get("link", resource.get("url", ""))
            snippet = resource.get("snippet", resource.get("summary", ""))

            rprint(f"\n[bold cyan]{i}. {title}[/bold cyan]")
            rprint(f"   [blue underline]{url}[/blue underline]")
            if snippet:
                rprint(f"   [dim]{snippet}[/dim]")

    # Display message ID if available
    if message_id:
        print()
        rprint(f"[dim]Message ID: {message_id}[/dim]")


def display_result_json(data: dict):
    """Display result in JSON format for programmatic use."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    api_key_status = "configured" if FELO_API_KEY else "[red]not configured[/red]"
    proxy_status = f"using {PROXY}" if PROXY else "not configured"

    parser = argparse.ArgumentParser(
        description="Felo AI CLI - AI-powered conversational search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s chat "What is the latest news about AI?"
  %(prog)s chat "Explain quantum computing in simple terms"
  %(prog)s chat "Best restaurants in Tokyo" --format json
  %(prog)s chat "Python vs JavaScript for beginners" --format table

Environment Variables:
  FELO_API_KEY: Felo AI API Key (current: {api_key_status})
  FELO_PROXY:   Proxy configuration (current: {proxy_status})

Rate Limits:
  100 requests per minute per API key
  Query length: 1-2000 characters

Retry Policy:
  Automatically retries on 5xx errors and network issues
  Max retries: {MAX_RETRIES} with exponential backoff

Documentation:
  https://felo.ai
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send a query to Felo AI")
    chat_parser.add_argument("query", nargs="+", help="Search query (1-2000 characters)")
    chat_parser.add_argument(
        "-f", "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )
    chat_parser.add_argument(
        "--retries",
        type=int,
        default=MAX_RETRIES,
        help=f"Maximum number of retries for transient errors (default: {MAX_RETRIES})"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "chat":
        query = " ".join(args.query)

        data = chat(query=query, output_format=args.format, max_retries=args.retries)

        if args.format == "json":
            display_result_json(data)
        else:
            display_result_table(data, query)


if __name__ == "__main__":
    main()
