"""Git operations assistance."""

import os
from typing import Dict, List, Optional

import typer
from rich import print
from rich.panel import Panel

from cli.utils.api import api_request, list_available_models
from cli.utils.formatting import print_error, print_info, print_success, print_warning
from cli.utils.git import run_git_command

app = typer.Typer(help="Git operations assistance")


@app.command()
def generate_commit(
    message_type: str = typer.Option(
        "conventional", help="Commit message type (conventional or descriptive)"
    ),
    files: Optional[bool] = typer.Option(
        False, "--files", "-f", help="Show changed files in the message"
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
    """Generate a commit message for the current changes."""
    # Get changed files
    status_output = run_git_command(["git", "status", "--porcelain"])

    if not status_output or status_output.startswith("Error"):
        if "Error" in status_output:
            print_error(status_output)
        else:
            print_error("No changes to commit.")
        return

    # Process changed files
    changes = []
    for line in status_output.splitlines():
        if line:
            status = line[:2].strip()
            file_path = line[3:]
            changes.append((status, file_path))

    available_models = list_available_models()
    use_ai = bool(available_models)
    if use_ai and model and model not in available_models:
        print_warning(
            f"Model '{model}' not found. Available models: {', '.join(available_models)}"
        )
        model = available_models[0]
        print_info(f"Using {model} instead.")

    if use_ai:
        # Get the diff for context
        diff_output = run_git_command(["git", "diff", "--cached", "--stat"])
        if not diff_output or diff_output.startswith("Error"):
            diff_output = run_git_command(["git", "diff", "--stat"])

        # Get the full diff for better context
        full_diff = run_git_command(["git", "diff", "--cached"])
        if not full_diff or full_diff.startswith("Error"):
            full_diff = run_git_command(["git", "diff"])

        # If the diff is too large, truncate it
        if len(full_diff) > 4000:
            full_diff = full_diff[:4000] + "\n... (diff truncated for brevity)"

        # Build the prompt
        changes_summary = "\n".join(
            [f"{status}: {file_path}" for status, file_path in changes]
        )

        # Get the repository name
        repo_name = "unknown"
        try:
            remote_url = run_git_command(["git", "remote", "get-url", "origin"]).strip()
            if remote_url:
                # Extract repository name from URL
                if "github.com" in remote_url:
                    repo_name = remote_url.split("github.com/")[-1].replace(".git", "")
                elif "gitlab" in remote_url:
                    repo_name = remote_url.split("gitlab")[-1].replace(".git", "")
                else:
                    # Just use the last part of the path
                    repo_name = os.path.basename(
                        os.path.normpath(remote_url.replace(".git", ""))
                    )
        except Exception:
            # Fallback to directory name
            repo_name = os.path.basename(os.getcwd())

        # Create the prompt for the LLM
        commit_prompt = f"""Generate a {message_type} commit message for the following changes in the repository '{repo_name}'.

Changed files:
{changes_summary}

Diff summary:
{diff_output}

Full diff:
{full_diff}

Guidelines:
- For conventional commit messages, use: type(scope): description
- Common types: feat, fix, docs, style, refactor, test, chore
- Keep the commit message concise and descriptive
- Focus on WHAT and WHY, not HOW
- Use imperative mood ("Add feature" not "Added feature")

Format your response as a complete commit message.
"""

        # Request commit message from the configured model
        response = api_request(
            endpoint="/text/generate",
            method="POST",
            data={
                "prompt": commit_prompt,
                "temperature": 0.3,
                "max_length": 512,
                "stream": not no_stream,
                "show_thinking": show_thinking,
            },
            model_name=model,
        )

        if "error" in response:
            print_error("Failed to generate commit message.")
            # Fall back to simple generation
            use_ai = False
        else:
            # Extract the commit message from the response
            commit_msg = response.get("text", "").strip()

            # For streaming mode, we need to handle the final output differently
            if not no_stream:
                print("\n")  # Add extra newline for separation
                print_success(
                    f"Commit message generated with {response.get('model_used', model)}."
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

                # Ask to use the message
                if typer.confirm("Use this commit message?"):
                    result = run_git_command(["git", "commit", "-m", commit_msg])
                    print(result)
                return
            else:
                # For non-streaming mode, display the message
                print("\n[bold green]Generated commit message: [/bold green]")
                print(commit_msg)

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

                # Ask to use the message
                if typer.confirm("Use this commit message?"):
                    result = run_git_command(["git", "commit", "-m", commit_msg])
                    print(result)
                return

    # Fallback to simple generation if no AI provider is configured or the call failed
    if not use_ai:
        # Generate the commit message
        if message_type == "conventional":
            # Mock conventional commit message
            commit_type = "feat"
            if any(file_path.endswith((".md", ".txt")) for _, file_path in changes):
                commit_type = "docs"
            elif any(
                file_path == "package.json" or file_path.endswith(".lock")
                for _, file_path in changes
            ):
                commit_type = "chore"
            elif any("test" in file_path for _, file_path in changes):
                commit_type = "test"

            msg = f"{commit_type}: update "
            if len(changes) == 1:
                _, file_path = changes[0]
                msg += os.path.basename(file_path)
            else:
                most_common_dir = (
                    os.path.dirname(changes[0][1]) if "/" in changes[0][1] else ""
                )
                msg += most_common_dir if most_common_dir else "multiple files"
        else:
            # Descriptive message
            actions = []
            if any(status == "M" for status, _ in changes):
                actions.append("Update")
            if any(status == "A" for status, _ in changes):
                actions.append("Add")
            if any(status == "D" for status, _ in changes):
                actions.append("Remove")

            msg = " & ".join(actions)
            file_count = len(changes)
            msg += f" {file_count} " + ("file" if file_count == 1 else "files")

        # Add files to the message if requested
        if files and changes:
            files_list = "\n\n- " + "\n- ".join(
                f"{status}: {file_path}" for status, file_path in changes
            )
            msg += files_list

        print("\n[bold green]Generated commit message: [/bold green]")
        print(msg)

        # Ask to use the message
        if typer.confirm("Use this commit message?"):
            result = run_git_command(["git", "commit", "-m", msg])
            print(result)


@app.command()
def pr_description(
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
    """Generate a pull request description based on commits."""
    # Get commits that would be included in a PR
    try:
        main_branch = "main"
        if not run_git_command(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{main_branch}"]
        ):
            main_branch = "master"

        commits = run_git_command(
            ["git", "log", f"{main_branch}..HEAD", "--pretty=format: %s"]
        )

        if not commits:
            print_error("No commits found between current branch and main/master.")
            return

        available_models = list_available_models()
        use_ai = bool(available_models)
        if use_ai and model and model not in available_models:
            print_warning(
                f"Model '{model}' not found. Available models: {', '.join(available_models)}"
            )
            model = available_models[0]
            print_info(f"Using {model} instead.")

        if use_ai:
            # Get more detailed information for better PR descriptions
            # Get the branch name
            branch = run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"]
            ).strip()

            # Get more detailed commit info
            detailed_commits = run_git_command(
                ["git", "log", f"{main_branch}..HEAD", "--pretty=format: %h %s%n%b"]
            )

            # Get a summary of changes
            summary = run_git_command(["git", "diff", f"{main_branch}..HEAD", "--stat"])

            # Create a prompt for the PR description
            pr_prompt = f"""Generate a comprehensive pull request description for the following changes in branch '{branch}'.

Commits between {main_branch} and this branch:
{detailed_commits}

Summary of changes:
{summary}

Guidelines for a good PR description:
1. Include a clear title that summarizes the changes
2. Group related changes by category (Features, Fixes, etc.)
3. Explain WHY the changes were made, not just WHAT was changed
4. Include testing instructions if applicable
5. Add any relevant screenshots or examples placeholder sections
6. Mention any dependency changes or deployment considerations

Format the PR description in Markdown with appropriate headings, bullet points, and sections.
"""

            # Request PR description from the configured model
            response = api_request(
                endpoint="/text/generate",
                method="POST",
                data={
                    "prompt": pr_prompt,
                    "temperature": 0.3,
                    "max_length": 1024,
                    "stream": not no_stream,
                    "show_thinking": show_thinking,
                },
                model_name=model,
            )

            if "error" in response:
                print_error("Failed to generate PR description.")
                # Fall back to simple generation
                use_ai = False
            else:
                # Extract the PR description from the response
                pr_desc = response.get("text", "").strip()

                # For streaming mode, we need to handle the final output differently
                if not no_stream:
                    print("\n")  # Add extra newline for separation
                    print_success(
                        f"PR description generated with {response.get('model_used', model)}."
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
                    # For non-streaming mode, display the description
                    print("\n[bold green]Generated PR Description: [/bold green]")
                    print(pr_desc)

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

        # Fallback to simple generation if no AI provider is configured or the call failed
        if not use_ai:
            print("Based on your commits, here's a suggested PR description: \n")

            # Generate title from branch name
            branch = run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"]
            ).strip()
            title = branch.replace("-", " ").replace("_", " ").title()
            if title.startswith("Feature "):
                title = title[8:]  # Remove "Feature " prefix

            # Generate PR description
            description = f"# {title}\n\n## Changes\n\n"

            # Group commits by type for conventional commits
            commit_groups: Dict[str, List[str]] = {}
            for line in commits.splitlines():
                if ":" in line:
                    commit_type, message = line.split(":", 1)
                    if commit_type not in commit_groups:
                        commit_groups[commit_type] = []
                    commit_groups[commit_type].append(message.strip())
                else:
                    if "Other" not in commit_groups:
                        commit_groups["Other"] = []
                    commit_groups["Other"].append(line.strip())

            for group, messages in commit_groups.items():
                description += f"### {group.capitalize()}\n"
                for msg in messages:
                    description += f"- {msg}\n"
                description += "\n"

            description += "## Testing\n\n- [ ] Tests added for new functionality\n- [ ] All tests passing\n\n"
            description += "## Screenshots (if applicable)\n\n_Add screenshots here_\n"

            print(description)
    except Exception as e:
        print_error(f"Error generating PR description: {str(e)}")
