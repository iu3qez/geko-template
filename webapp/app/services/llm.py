"""
Claude API integration for generating article summaries.

Gestione API Key:
    La chiave API può essere fornita in 3 modi (in ordine di priorità):
    1. Parametro diretto: ClaudeSummaryService(api_key="sk-...")
    2. File secrets: ANTHROPIC_API_KEY_FILE=/path/to/file
    3. Variabile ambiente: ANTHROPIC_API_KEY=sk-...

    Per Docker, usare il file secrets è più sicuro:
    ```yaml
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key
    secrets:
      - anthropic_key
    ```
"""

import json
import os
from pathlib import Path
from typing import Optional
import httpx


def _load_api_key() -> Optional[str]:
    """
    Carica API key da file o variabile ambiente.

    Ordine di priorità:
    1. ANTHROPIC_API_KEY_FILE (path a file con la key)
    2. ANTHROPIC_API_KEY (variabile ambiente diretta)

    Returns:
        API key come stringa, o None se non trovata
    """
    # Prima prova a leggere da file (più sicuro per Docker)
    key_file = os.getenv("ANTHROPIC_API_KEY_FILE")
    if key_file:
        key_path = Path(key_file)
        if key_path.exists():
            return key_path.read_text().strip()

    # Fallback a variabile ambiente diretta
    return os.getenv("ANTHROPIC_API_KEY")


class ClaudeSummaryService:
    """
    Generate article summaries using Claude API.

    Attributes:
        api_key: Chiave API Anthropic
        base_url: Endpoint API
        model: Modello Claude da usare (default: claude-sonnet-4-20250514)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _load_api_key()
        self.base_url = "https://api.anthropic.com/v1/messages"
        # Haiku 3.5: economico ($0.25-1.25/1M token), veloce, qualità buona per sommari
        self.model = "claude-3-5-haiku-20241022"

    async def generate_summary(self, article_content: str, article_title: str) -> dict:
        """
        Generate a summary for an article.

        Args:
            article_content: The article content in markdown
            article_title: The article title

        Returns:
            dict with 'sommario' and 'keywords' keys
        """
        if not self.api_key:
            # Return placeholder if no API key
            return {
                "sommario": f"Articolo: {article_title}",
                "keywords": []
            }

        prompt = f"""Riassumi questo articolo per una rivista radioamatoriale in 2-3 frasi.
Il riassunto deve essere adatto per la sezione "In Evidenza" della copertina.
Tono: informale, tecnico ma accessibile.

Titolo: {article_title}

Contenuto:
{article_content[:3000]}

Rispondi SOLO con un JSON valido in questo formato:
{{"sommario": "Il riassunto qui...", "keywords": ["keyword1", "keyword2", "keyword3"]}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 500,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()

                # Extract text from response
                text = result["content"][0]["text"]

                # Parse JSON from response
                # Handle potential markdown code blocks
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]

                return json.loads(text.strip())

        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                "sommario": f"Articolo: {article_title}",
                "keywords": []
            }

    async def generate_summaries_batch(
        self,
        articles: list[dict]
    ) -> list[dict]:
        """
        Generate summaries for multiple articles.

        Args:
            articles: List of dicts with 'titolo' and 'contenuto' keys

        Returns:
            List of summary dicts
        """
        summaries = []
        for article in articles:
            summary = await self.generate_summary(
                article.get('contenuto', ''),
                article.get('titolo', 'Articolo')
            )
            summaries.append(summary)
        return summaries


# Global instance
_summary_service: Optional[ClaudeSummaryService] = None


def get_summary_service() -> ClaudeSummaryService:
    """Get or create the summary service instance."""
    global _summary_service
    if _summary_service is None:
        _summary_service = ClaudeSummaryService()
    return _summary_service


async def generate_article_summary(content: str, title: str) -> dict:
    """Convenience function for generating a single summary."""
    service = get_summary_service()
    return await service.generate_summary(content, title)
