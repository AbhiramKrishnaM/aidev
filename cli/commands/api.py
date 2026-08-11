"""API request testing and formatting."""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import typer
from rich import print

from cli.utils.api import api_request, list_available_models
from cli.utils.formatting import print_error, print_info, print_json, print_success

app = typer.Typer(help="Send ad-hoc prompts to the configured AI model")

# Directory to store saved requests
REQUESTS_DIR = os.path.expanduser("~/.aidev/requests")


@app.command()
def request(
    prompt: str = typer.Argument(..., help="Text prompt to send to the model"),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use (defaults to the configured default)"
    ),
    temperature: float = typer.Option(
        0.7, "--temperature", "-t", help="Temperature for generation (0.0-1.0)"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming for local models"
    ),
) -> None:
    """Make a direct request to the configured AI model."""
    if not list_available_models():
        print_error("No AI provider configured.")
        print_info("Export ANTHROPIC_API_KEY or OPENAI_API_KEY to get started.")
        return

    print(
        f"Generating text with model {model or '(default)'} (Temperature: {temperature})"
    )

    # Make the request
    response = api_request(
        endpoint="/text/generate",
        method="POST",
        data={
            "prompt": prompt,
            "temperature": temperature,
            "stream": not no_stream,
        },
        model_name=model,
    )

    # Display the response
    if "error" in response:
        print_error("Request failed")
        print_error(response.get("message", "Unknown error"))
    else:
        print_success("Request successful")
        if no_stream:
            print_json(response, "Response")


@app.command()
def list_saved() -> None:
    """List all saved API requests."""
    _ensure_requests_dir()

    saved_requests = []
    for filename in os.listdir(REQUESTS_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(REQUESTS_DIR, filename), "r") as f:
                    request_data = json.load(f)
                name = filename[:-5]  # Remove .json extension
                saved_requests.append(
                    (
                        name,
                        request_data.get("method", ""),
                        request_data.get("url", ""),
                        request_data.get("timestamp", ""),
                    )
                )
            except (json.JSONDecodeError, IOError):
                pass

    if not saved_requests:
        typer.echo("No saved requests found.")
        return

    typer.echo("Saved API Requests:")
    for name, method, url, timestamp in sorted(saved_requests):
        typer.echo(f"  - {name}: [{method}] {url} ({timestamp})")


@app.command()
def load(
    name: str = typer.Argument(..., help="Name of the saved request to load"),
    execute: bool = typer.Option(
        False, "--execute", "-e", help="Execute the request after loading"
    ),
) -> None:
    """Load a saved API request."""
    _ensure_requests_dir()

    file_path = os.path.join(REQUESTS_DIR, f"{name}.json")
    if not os.path.exists(file_path):
        typer.echo(f"Error: Request '{name}' not found.", err=True)
        return

    try:
        with open(file_path, "r") as f:
            request_data = json.load(f)

        typer.echo(f"Loaded request: {name}")
        typer.echo(f"Method: {request_data.get('method', 'GET')}")
        typer.echo(f"URL: {request_data.get('url', '')}")

        headers = request_data.get("headers", {})
        if headers:
            typer.echo("\nHeaders:")
            for key, value in headers.items():
                typer.echo(f"  {key}: {value}")

        data = request_data.get("data")
        if data:
            typer.echo("\nData:")
            typer.echo(json.dumps(data, indent=2))

        if execute:
            typer.echo("\nExecuting request...")
            request(
                prompt=data.get("prompt", ""),
                model=data.get("model"),
                temperature=data.get("temperature", 0.7),
                no_stream=data.get("stream", False),
            )

    except (json.JSONDecodeError, IOError) as e:
        typer.echo(f"Error loading request: {str(e)}", err=True)


def _ensure_requests_dir() -> None:
    """Ensure the requests directory exists."""
    if not os.path.exists(REQUESTS_DIR):
        os.makedirs(REQUESTS_DIR, exist_ok=True)


def _save_request(
    name: str,
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Dict[str, Any],
    response: Any,
) -> None:
    """Save a request for future use."""
    _ensure_requests_dir()

    file_path = os.path.join(REQUESTS_DIR, f"{name}.json")

    request_data = {
        "method": method,
        "url": url,
        "headers": headers,
        "data": data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
        },
    }

    try:
        with open(file_path, "w") as f:
            json.dump(request_data, f, indent=2)
        typer.echo(f"\nRequest saved as '{name}'")
    except IOError as e:
        typer.echo(f"Error saving request: {str(e)}", err=True)
