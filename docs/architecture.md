# Architecture

System-level view of the pivot described in [`docs/adr/`](adr/README.md): a CLI that detects
which cloud AI provider the user already has credentials for, and uses it to power an
incident/debugging co-pilot grounded in the local repo's code and git history.

## Component diagram

Command groups all funnel through the same shared layer down to a provider adapter, so every
command benefits from provider detection and model selection without reimplementing it.
`incident` and `git` additionally share git plumbing.

```mermaid
flowchart TD
    subgraph CLI["cli/main.py (Typer app)"]
        CODE["code"]
        TERM["terminal"]
        GIT["git"]
        DOCS["docs"]
        API["api"]
        MODELS["models"]
        INCIDENT["incident"]
    end

    subgraph SHARED["Shared layer"]
        UTILAPI["cli/utils/api.py
generate_text / generate_code / explain_code"]
        UTILGIT["cli/utils/git.py
run_git_command"]
        UTILCFG["cli/utils/config.py
get/set_config_value"]
    end

    subgraph FACTORY["cli/ai_agent_models/"]
        FACTORYPY["model_factory.py
get_model / get_available_providers"]
        BASE["base_model.py
BaseAIModel"]
        ANTH["anthropic_model.py
AnthropicModel"]
        OPENAIM["openai_model.py
OpenAIModel"]
    end

    subgraph EXTERNAL["External APIs"]
        ANTHAPI[("Anthropic API")]
        OPENAIAPI[("OpenAI API")]
    end

    CONFIGFILE[("~/.aidev/config.json")]

    CODE --> UTILAPI
    TERM --> UTILAPI
    DOCS --> UTILAPI
    GIT --> UTILAPI
    GIT --> UTILGIT
    API --> UTILAPI
    MODELS --> FACTORYPY
    INCIDENT --> UTILAPI
    INCIDENT --> UTILGIT

    UTILAPI --> FACTORYPY
    FACTORYPY --> BASE
    BASE --> ANTH
    BASE --> OPENAIM
    ANTH --> ANTHAPI
    OPENAIM --> OPENAIAPI

    FACTORYPY --> UTILCFG
    MODELS --> UTILCFG
    UTILCFG <--> CONFIGFILE
```

## Sequence diagram: `aidev incident analyze`

The flagship flow. The key property is that steps 3-5 run entirely locally, before anything is
sent to the model — the AI call in step 7 is grounded in real repo state, not just the raw error
text.

```mermaid
sequenceDiagram
    participant User
    participant Incident as incident.py
    participant Git as utils/git.py
    participant Factory as model_factory
    participant Provider as Provider adapter
    participant API as Anthropic / OpenAI

    User->>Incident: aidev incident analyze (arg / --file / stdin)
    Incident->>Incident: 1. Read raw error/traceback
    Incident->>Incident: 2. Regex-extract (file, line) references
    loop for each matched file (max 5)
        Incident->>Incident: 3. Read code context (+/- N lines)
        Incident->>Git: 4. git blame -L start,end <file>
        Git-->>Incident: blame output
        Incident->>Git: 5. git log -n 5 -- <file>
        Git-->>Incident: recent commits
    end
    Incident->>Incident: 6. Assemble prompt (error + code + blame + log)
    Incident->>Factory: get_model(model_name)
    Factory-->>Incident: provider adapter instance
    Incident->>Provider: generate_text(prompt, system_prompt, stream=True)
    Provider->>API: streaming completion request
    API-->>Provider: token stream
    Provider-->>Incident: token stream
    Incident-->>User: 7. Live-streamed root-cause analysis
```

## Credential and config flow

Provider detection is a pure environment check (no network call); model selection is
explicit and persisted, with a safe auto-pick fallback so the tool is still usable before the
user has ever run `aidev models select`.

```mermaid
flowchart LR
    ENV["Environment variables
ANTHROPIC_API_KEY
OPENAI_API_KEY"] --> ISAVAIL["BaseAIModel.is_available()
per provider"]
    ISAVAIL --> LIST["aidev models list
shows detected providers + models"]
    LIST --> SELECT["aidev models select
interactive provider -> model picker"]
    SELECT --> WRITE["set_config_value(ai.default_model,
'provider:model_id')"]
    WRITE --> CFGFILE[("~/.aidev/config.json")]

    CFGFILE --> RESOLVE["get_default_model_name()"]
    ISAVAIL --> RESOLVE
    RESOLVE -->|"config value set"| USECFG["Use configured default"]
    RESOLVE -->|"unset, provider(s) detected"| AUTOPICK["Auto-pick first available
provider's first model"]
    RESOLVE -->|"unset, none detected"| ERR["Error: export ANTHROPIC_API_KEY
or OPENAI_API_KEY, or run
aidev models select"]
```

## Notes

- Every component in these diagrams is backed by a decision in an ADR — see
  [`docs/adr/README.md`](adr/README.md) for the rationale behind each one.
- This document describes the target architecture agreed in planning; it does not imply any of
  it has been implemented yet. Check `cli/` for current state.
