"""Documentation search and summarization."""

import os
from typing import List, Optional, Tuple

import typer
from rich import print
from rich.panel import Panel

from cli.utils.api import api_request, list_available_models
from cli.utils.formatting import print_error, print_info, print_success, print_warning

app = typer.Typer(help="Search and summarize documentation")

# Mock documentation database (would be replaced with embeddings search)
MOCK_DOCS = {
    "python": {
        "list": "Lists are used to store multiple items in a single variable. Lists are created using square brackets.",
        "dict": "Dictionaries are used to store data values in key: value pairs. A dictionary is a collection which is ordered, changeable and do not allow duplicates.",
        "function": "A function is a block of code which only runs when it is called. You can pass data, known as parameters, into a function.",
    },
    "javascript": {
        "array": "JavaScript arrays are used to store multiple values in a single variable. Arrays use numbered indexes.",
        "object": "JavaScript objects are containers for named values called properties or methods.",
        "function": "JavaScript functions are blocks of code designed to perform a particular task and executed when 'called'.",
    },
    "git": {
        "commit": "The git commit command captures a snapshot of the project's currently staged changes.",
        "push": "The git push command is used to upload local repository content to a remote repository.",
        "pull": "The git pull command is used to fetch and download content from a remote repository and immediately update the local repository to match that content.",
    },
}


@app.command()
def search(
    query: List[str] = typer.Argument(..., help="Search terms"),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Limit search to specific language/tool"
    ),
    max_results: int = typer.Option(
        5, "--max", "-m", help="Maximum number of results to display"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model to use (defaults to the configured default)"
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
    """Search documentation for specific terms."""
    search_terms = " ".join(query).lower()
    print(f"Searching docs for: {search_terms}")

    available_models = list_available_models()
    use_ai = bool(available_models)
    if use_ai and model and model not in available_models:
        print_warning(
            f"Model '{model}' not found. Available models: {', '.join(available_models)}"
        )
        model = available_models[0]
        print_info(f"Using {model} instead.")

    if use_ai:
        # Prepare documentation search prompt
        language_filter = f" for {language}" if language else ""
        search_prompt = f"""You are a documentation search engine.

Search for information about "{search_terms}"{language_filter} and provide up to {max_results} results.

Each result should include:
1. The programming language or tool
2. The specific topic or function name
3. A brief description of how it works
4. A short example of its usage

Format the results in a clean, numbered list with clear headings for each item.
"""

        # Request documentation search from the configured model
        response = api_request(
            endpoint="/text/generate",
            method="POST",
            data={
                "prompt": search_prompt,
                "temperature": 0.3,
                "max_length": 1024,
                "stream": not no_stream,
                "show_thinking": show_thinking,
            },
            model_name=model,
        )

        if "error" in response:
            print_error("Failed to search documentation.")
            # Fall back to simple search
            use_ai = False
        else:
            # For streaming mode, we need to handle the final output differently
            if not no_stream:
                print("\n")  # Add extra newline for separation
                print_success(
                    f"Documentation search completed with {response.get('model_used', model)}."
                )

                # If there are thinking sections in non-streaming mode, show them
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
                return
            else:
                # For non-streaming mode, display the search results
                search_results = response.get("text", "").strip()
                print("\n[bold green]Search Results: [/bold green]")
                print(search_results)

                # Display thinking sections for non-streaming mode if available
                if "thinking" in response and response["thinking"] and show_thinking:
                    print_info("Model reasoning (click to expand):")
                    for i, thinking in enumerate(response["thinking"], 1):
                        panel = Panel(
                            thinking.strip(),
                            title=f"[bold]Thinking Process #{i}[/bold]",
                            subtitle="[dim][click to collapse][/dim]",
                            border_style="blue",
                        )
                        print(panel)
                return

    # Fallback to simple search if no AI provider is configured or the call failed
    if not use_ai:
        results: List[Tuple[str, str, str]] = []

        # Filter by language if provided
        doc_sources = list(MOCK_DOCS.items())
        if language:
            if language in MOCK_DOCS:
                doc_sources = [(language, MOCK_DOCS[language])]
            else:
                print_warning(f"No documentation found for {language}")
                return

        # Search through docs
        for lang, topics in doc_sources:
            for topic, content in topics.items():
                if search_terms in topic.lower() or search_terms in content.lower():
                    results.append((lang, topic, content))

        # Display results
        if not results:
            print_info("No results found. Try different search terms.")
            return

        print(f"\n[bold green]Found {len(results)} results: [/bold green]")
        for i, (lang, topic, content) in enumerate(results[:max_results], 1):
            print(f"\n{i}. [{lang}] {topic}")
            print(f"   {content[: 150]}{'...' if len(content) > 150 else ''}")

        if len(results) > max_results:
            print(f"\n...and {len(results) - max_results} more results.")


@app.command()
def summarize(
    file_path: str = typer.Argument(..., help="Documentation file to summarize"),
    length: str = typer.Option("medium", help="Summary length (short, medium, long)"),
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
    """Summarize a documentation file."""
    if not os.path.exists(file_path):
        print_error(f"File {file_path} not found.")
        return

    try:
        with open(file_path, "r") as f:
            content = f.read()

        available_models = list_available_models()
        use_ai = bool(available_models)
        if use_ai and model and model not in available_models:
            print_warning(
                f"Model '{model}' not found. Available models: {', '.join(available_models)}"
            )
            model = available_models[0]
            print_info(f"Using {model} instead.")

        if use_ai:
            # Determine the target length
            if length == "short":
                length_instruction = "Create a concise summary in about 2-3 sentences."
            elif length == "long":
                length_instruction = "Create a comprehensive summary with multiple paragraphs covering all main points."
            else:  # medium
                length_instruction = (
                    "Create a medium-length summary in about 1-2 paragraphs."
                )

            # Prepare the summarization prompt
            # If file is very large, truncate it
            if len(content) > 10000:
                first_part = content[:5000]
                last_part = content[-5000:]
                content_to_summarize = f"{first_part}\n\n[... content truncated for brevity ...]\n\n{last_part}"
                truncation_warning = "\nNote: The file was truncated due to its size. This summary covers the beginning and end of the document."
            else:
                content_to_summarize = content
                truncation_warning = ""

            summarize_prompt = f"""Summarize the following documentation file: {os.path.basename(file_path)}

{length_instruction}

The summary should:
1. Identify the main topic
2. Highlight key concepts, functions, or features
3. Note any important usage patterns or warnings
4. Be clear and informative

Here's the content to summarize:

{content_to_summarize}
{truncation_warning}
"""

            # Request summarization from the configured model
            response = api_request(
                endpoint="/text/generate",
                method="POST",
                data={
                    "prompt": summarize_prompt,
                    "temperature": 0.3,
                    "max_length": 1024,
                    "stream": not no_stream,
                    "show_thinking": show_thinking,
                },
                model_name=model,
            )

            if "error" in response:
                print_error("Failed to summarize.")
                # Fall back to simple summarization
                use_ai = False
            else:
                print(f"\n[bold green]Summary of {file_path} ({length}): [/bold green]")

                # For streaming mode, we need to handle the final output differently
                if not no_stream:
                    print("\n")  # Add extra newline for separation
                    print_success(
                        f"Summarization completed with {response.get('model_used', model)}."
                    )

                    # If there are thinking sections in non-streaming mode, show them
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
                    return
                else:
                    # For non-streaming mode, display the summary
                    summary = response.get("text", "").strip()
                    print(summary)

                    # Display thinking sections for non-streaming mode if available
                    if (
                        "thinking" in response
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
                    return

        # Fallback to simple summarization if no AI provider is configured or the call failed
        if not use_ai:
            # Calculate summary length
            content_length = len(content)
            if length == "short":
                summary_size = min(content_length, 200)
            elif length == "long":
                summary_size = min(content_length, 1000)
            else:  # medium
                summary_size = min(content_length, 500)

            print(f"\n[bold green]Summary of {file_path} ({length}): [/bold green]\n")

            # Mock summary - would be replaced with AI-generated summary
            summary = f"This document is about {os.path.basename(file_path)}. It contains information that would be useful for developers. The summary would be generated by an AI model."

            if content_length > 100:
                # Add a bit of context from the beginning
                intro = content[:100].replace("\n", " ")
                summary += f'\n\nIt begins with: "{intro}..."'

            print(summary)

    except Exception as e:
        print_error(f"{str(e)}")
