# Milestone 12 Summary — AI Provider SDK

**Status:** Complete  
**Version:** 0.1.0  
**Type:** Provider-neutral AI platform

Milestone 12 delivers the AI Provider SDK — a capability-based abstraction where Vedaws requests `chat`, `plan`, `implement`, etc., not Gemini or OpenAI. Providers are plugins; the runtime never imports vendor SDKs.

---

## 1. Repository Tree

```
vedaws/
├── design/
│   ├── 012_CONFIGURATION.md      # [ai] routing config
│   ├── 017_AI_PROVIDERS.md         # AI platform (active)
│   ├── 010_PLUGINS.md              # contribute_ai_provider
│   └── README.md
│
├── docs/
│   └── MILESTONE_12_SUMMARY.md
│
├── plugins/mock-ai/
│   ├── vedaws.plugin.toml
│   └── mock_ai_plugin/
│       ├── __init__.py
│       └── provider.py             # MockAIProvider
│
├── runtime/vedaws/
│   ├── ai/
│   │   ├── capabilities.py         # chat, plan, implement, …
│   │   ├── model.py                # requests/responses
│   │   ├── provider.py             # AIProvider ABC
│   │   ├── registry.py
│   │   ├── router.py               # capability routing
│   │   ├── service.py              # AIService facade
│   │   ├── config.py
│   │   ├── integration.py
│   │   ├── validator.py
│   │   ├── reporter.py
│   │   └── sdk.py                  # public plugin exports
│   ├── cli/ai_commands.py
│   ├── config/schema.py            # AIConfig on VedawsConfig
│   ├── doctor/checks.py            # check_ai_platform
│   ├── plugins/sdk.py              # contribute_ai_provider
│   └── runtime/bootstrap.py        # build_ai_service
│
└── tests/
    └── test_ai_providers.py
```

---

## 2. Architecture Summary

```
Worker / CLI / Automation
        ↓
    AIService (capability request)
        ↓
AIProviderRouter (config → preferred → fallback → default → priority)
        ↓
AIProviderRegistry
        ↓
Plugin AIProvider (mock-ai, future: gemini, …)
```

**Domain neutrality:** Workflows and runtime code never name vendors. Only capability strings and provider ids in configuration.

---

## 3. SDK Interfaces

```python
class AIProvider(ABC):
    id: str
    name: str
    capabilities: tuple[str, ...]
    priority: int

    def health() -> AIProviderHealth
    def chat(request: ChatRequest) -> ChatResponse
    def generate(request: GenerateRequest) -> GenerateResponse
    def stream(request) -> Iterator[str]      # stub ok
    def embeddings(request) -> EmbeddingsResponse  # stub ok
```

Plugin registration:

```python
context.contribute_ai_provider(MockAIProvider())
```

---

## 4. Provider Lifecycle

```
Plugin discovered → activated → contribute_ai_provider()
        ↓
build_ai_service() merges into AIProviderRegistry
        ↓
AIProviderRouter applies project [ai] config
        ↓
AIService available on RuntimeContext
        ↓
Plugin unload → registry rebuilt on next bootstrap
```

`unregister()` supported on registry API; bootstrap rebuilds each session.

---

## 5. Capability Routing

| Step | Source |
|------|--------|
| 1 | `[ai.capabilities.<cap>.preferred]` |
| 2 | `[ai.capabilities.<cap>.fallback]` |
| 3 | `[ai].default_provider` |
| 4 | Highest `priority` among providers supporting capability |

```toml
[ai]
default_provider = "mock-ai"

[ai.capabilities.implement]
preferred = "mock-ai"
fallback = ["mock-ai"]
```

---

## 6. Mock Provider

`plugins/mock-ai/` implements all standard capabilities plus `embeddings`:

- Deterministic `[mock-ai:capability]` responses
- `stream()` yields full response (stub)
- `health()` reports credentials available (no keys required)
- Enabled by default in new projects (`plugins.toml`)

---

## Example Usage

```bash
vedaws ai providers
vedaws ai capabilities
vedaws ai status
vedaws doctor
```

Programmatic (runtime):

```python
context = bootstrap(workspace)
response = context.ai_service.chat(
    ChatRequest(messages=(ChatMessage("user", "hello"),), capability="chat")
)
```

---

## Future Integration Points

| Integration point | Hook | Notes |
|-------------------|------|-------|
| Gemini / OpenAI / Claude | `AIProvider` plugin | Vendor code stays in plugin only |
| AI workers | `AIService` in worker execute | Workers request capabilities |
| Skills | capability + skill metadata | Prompt binding in provider plugin |
| Automation | future `invoke_ai` action | Route through `AIService` |
| Credentials | `health().credentials_available` | Vault plugins set availability |

**Explicitly not implemented:** Real vendors, MCP, prompt engineering, agent orchestration, streaming UI.

---

## Tests

```bash
python -m pytest tests/ -q
# 107 passed
```
