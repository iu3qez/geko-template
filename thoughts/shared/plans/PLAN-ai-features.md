# Plan: AI Features Enhancement

## Summary
Add two AI-related features:
1. **Regenerate AI summary button** - Allow regenerating summaries for articles that already have one
2. **AI model selection** - Allow choosing between Haiku and Sonnet in settings

## Task 1: Regenerate AI Summary Button

### Current State
- Button "🤖 Genera sommario" only shows when `article.sommario_llm` is empty
- Location: `webapp/app/templates/standard/articles/list_item.html:71-83`
- Endpoint: `POST /articles/{id}/summary` already works for generating/regenerating

### Changes Required

**File: `webapp/app/templates/standard/articles/list_item.html`**
- Modify the conditional block (lines 71-83)
- Show "Genera sommario" when NO summary exists
- Show "🔄 Rigenera sommario" when summary ALREADY exists
- Both buttons call the same endpoint

```html
<!-- Current: only shows when no summary -->
{% if not article.sommario_llm %}
<button ...>🤖 Genera sommario</button>
{% endif %}

<!-- New: show different button based on state -->
{% if article.sommario_llm %}
<button ... title="Rigenera sommario AI">🔄 Rigenera</button>
{% else %}
<button ... title="Genera sommario con AI">🤖 Genera sommario</button>
{% endif %}
```

## Task 2: AI Model Selection in Settings

### Current State
- Model hardcoded: `webapp/app/services/llm.py:62` → `"claude-3-5-haiku-20241022"`
- Config stored in key-value table: `webapp/app/models.py:106-134`
- Config panel: `webapp/app/templates/standard/config/panel.html`
- Service is singleton: `get_summary_service()` creates one instance

### Changes Required

**File: `webapp/app/models.py`**
- Add `claude_model` to `Config.DEFAULTS`:
```python
DEFAULTS = {
    # ... existing ...
    "claude_model": ("claude-3-5-haiku-20241022", "Modello Claude per generazione sommari"),
}
```

**File: `webapp/app/templates/standard/config/panel.html`**
- Add new fieldset "Impostazioni AI" before "Template Typst"
- Add dropdown for model selection with options:
  - `claude-3-5-haiku-20241022` (Haiku - economico, veloce)
  - `claude-sonnet-4-20250514` (Sonnet - più capace, più costoso)

**File: `webapp/app/services/llm.py`**
- Modify `ClaudeSummaryService.__init__()` to accept `model` parameter
- Modify `get_summary_service()` to NOT be a singleton (or accept model param)
- Add new function `get_summary_service_with_model(model: str)` for flexibility
- OR: read model from env/config at service creation time

**File: `webapp/app/routes/articles.py`**
- Update `generate_summary()` to fetch model from Config
- Pass model to service

**File: `webapp/app/routes/config.py`**
- Update `save_config()` to handle new `claude_model` key (already automatic via DEFAULTS loop)

## Implementation Order
1. Add `claude_model` to Config.DEFAULTS
2. Update config panel template with dropdown
3. Modify llm.py service to accept model parameter
4. Update articles.py to fetch and use config model
5. Add regenerate button to list_item.html

## Risk Assessment
- **Low risk**: Changes are additive, existing functionality preserved
- **Breaking change**: None - default model stays Haiku
- **Testing**: Manual test via UI after each change

## Files Modified
1. `webapp/app/models.py` - Add claude_model to DEFAULTS
2. `webapp/app/templates/standard/config/panel.html` - Add AI model dropdown
3. `webapp/app/services/llm.py` - Accept model parameter
4. `webapp/app/routes/articles.py` - Fetch model from config
5. `webapp/app/templates/standard/articles/list_item.html` - Add regenerate button
