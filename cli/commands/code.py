"""Code generation commands."""

from typing import Optional

import typer
from rich import print
from rich.panel import Panel
from rich.syntax import Syntax

from cli.utils.api import api_request, list_available_models
from cli.utils.formatting import print_error, print_info, print_success, print_warning

app = typer.Typer(help="Generate and manage code snippets")


@app.command()
def generate(
    description: str = typer.Argument(..., help="Description of the code to generate"),
    language: str = typer.Option("python", help="Programming language"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
    temperature: float = typer.Option(
        0.7, "--temperature", "-t", help="Temperature for generation (0.0-1.0)"
    ),
    max_length: Optional[int] = typer.Option(
        None, "--max-length", "-l", help="Maximum length of generated code"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use (defaults to the configured default)"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming for local models"
    ),
    show_thinking: bool = typer.Option(
        True,
        "--show-thinking/--no-thinking",
        help="Show or hide model's thinking process",
    ),
) -> None:
    """Generate code based on a natural language description."""
    print(f"Generating {language} code for: {description}")

    # Check for available models
    available_models = list_available_models()
    if not available_models:
        print_error("No AI provider configured.")
        print_info("Export ANTHROPIC_API_KEY or OPENAI_API_KEY to get started.")
        return

    if model and model not in available_models:
        print_warning(
            f"Model '{model}' not found. Available models: {', '.join(available_models)}"
        )
        model = available_models[0]
        print_info(f"Using {model} instead.")

    # Request code generation
    response = api_request(
        endpoint="/code/generate",
        method="POST",
        data={
            "description": description,
            "language": language,
            "temperature": temperature,
            "max_length": max_length or 1024,
            "stream": not no_stream,
            "show_thinking": show_thinking,
        },
        model_name=model,
    )

    # Extract the code from response
    if "error" in response:
        print_error("Failed to generate code.")
        print_error(response.get("message", "Unknown error"))
        return

    code = response.get(
        "code", response.get("text", "# Error: No code was generated")
    ).strip()

    # For streaming mode, we need to handle the final output and thinking differently
    if not no_stream:
        print("\n")  # Add extra newline for separation
        print_success(
            f"Code generation completed with {response.get('model_used', model)}."
        )

        # If there are thinking sections in non-streaming mode
        if (
            no_stream
            and "thinking" in response
            and response["thinking"]
            and show_thinking
        ):
            print_info("Model reasoning (click to expand):")
            for i, thinking in enumerate(response["thinking"], 1):
                panel = Panel(
                    thinking.strip(),
                    title=f"[bold]Thinking Process #{i}[/bold]",
                    subtitle="[dim][click to collapse][/dim]",
                    border_style="blue",
                )
                print(panel)

    # Output handling
    if output:
        with open(output, "w") as f:
            f.write(code)
        print(f"Code written to [bold]{output}[/bold]")
    else:
        # Only print the syntax-highlighted code if we're not in streaming mode
        # (for streaming, the code is already printed in real-time)
        if not (not no_stream):
            print("\n[bold green]Generated Code: [/bold green]")
            # Use the rich Syntax class for syntax highlighting
            try:
                syntax = Syntax(code, language, theme="monokai", line_numbers=True)
                print(syntax)
            except Exception:
                # Fallback to simple printing if syntax highlighting fails
                print(code)


@app.command()
def explain(
    file_path: str = typer.Argument(..., help="Path to the code file to explain"),
    line_range: Optional[str] = typer.Option(
        None, "--lines", "-l", help="Line range (e.g., '10-20')"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", help="Programming language"
    ),
    detail_level: str = typer.Option(
        "medium",
        "--detail",
        "-d",
        help="Explanation detail level (brief, medium, detailed)",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use (defaults to the configured default)"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming for local models"
    ),
    show_thinking: bool = typer.Option(
        True,
        "--show-thinking/--no-thinking",
        help="Show or hide model's thinking process",
    ),
) -> None:
    """Explain the provided code."""
    try:
        with open(file_path, "r") as f:
            code = f.read()

        if line_range:
            start, end = map(int, line_range.split("-"))
            lines = code.splitlines()[start - 1 : end]
            code = "\n".join(lines)

        print(f"Explaining code from {file_path}:")

        # Check for available models
        available_models = list_available_models()
        if not available_models:
            print_error("No AI provider configured.")
            print_info("Export ANTHROPIC_API_KEY or OPENAI_API_KEY to get started.")
            return

        if model and model not in available_models:
            print_warning(
                f"Model '{model}' not found. Available models: {', '.join(available_models)}"
            )
            model = available_models[0]
            print_info(f"Using {model} instead.")

        # Infer language if not specified
        if not language:
            if file_path.endswith(".py"):
                language = "python"
            elif file_path.endswith(".js"):
                language = "javascript"
            elif file_path.endswith(".ts"):
                language = "typescript"
            elif file_path.endswith(".java"):
                language = "java"
            elif file_path.endswith(".go"):
                language = "go"
            elif file_path.endswith(".rs"):
                language = "rust"
            elif (
                file_path.endswith(".c")
                or file_path.endswith(".cpp")
                or file_path.endswith(".cc")
            ):
                language = "c++"
            elif file_path.endswith(".rb"):
                language = "ruby"
            else:
                language = "unknown"

        # Create a prompt for code explanation based on detail level
        detail_text = ""
        if detail_level == "brief":
            detail_text = (
                "Give a brief explanation highlighting only the most important aspects."
            )
        elif detail_level == "medium":
            detail_text = "Give a medium-length explanation with moderate detail."
        elif detail_level == "detailed":
            detail_text = (
                "Give a detailed explanation covering all aspects of the code."
            )

        # Request code explanation
        response = api_request(
            endpoint="/code/explain",
            method="POST",
            data={
                "code": code,
                "language": language,
                "detail_level": detail_level,
                "stream": not no_stream,
                "show_thinking": show_thinking,
            },
            model_name=model,
        )

        if "error" in response:
            print_error("Failed to explain code.")
            print_error(response.get("message", "Unknown error"))
            return

        # Print the explanation
        explanation = response.get("text", "Error: No explanation generated").strip()

        if no_stream:
            print("\n[bold green]Explanation: [/bold green]")
            print(explanation)

        print("\n")  # Add extra newline for separation
        print_success(f"Code explanation completed with {model}.")

    except FileNotFoundError:
        print_error(f"File not found: {file_path}")
    except Exception as e:
        print_error(f"Error explaining code: {str(e)}")
