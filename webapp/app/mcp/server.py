"""Server MCP GEKO: tool per creare/gestire articoli conformi al template."""

import base64
from typing import Optional

from fastmcp import FastMCP

from ..database import async_session
from ..services import article_ops
from .auth import build_auth
from .conventions import CONVENZIONI, markdown_preview

mcp = FastMCP(name="GEKO Articoli", auth=build_auth())


@mcp.tool
async def crea_articolo(
    titolo: str,
    contenuto_md: str,
    sottotitolo: str = "",
    autore: str = "",
    nome_autore: str = "",
    numero_id: Optional[int] = None,
) -> dict:
    """Crea un articolo GEKO da Markdown (vedi risorsa guida://convenzioni).

    `autore` è il nominativo radio (call), `nome_autore` il nome reale.
    Se `numero_id` è indicato, assegna l'articolo a quel numero.
    """
    async with async_session() as db:
        art = await article_ops.create_article(
            db, titolo=titolo, contenuto_md=contenuto_md,
            sottotitolo=sottotitolo, autore=autore, nome_autore=nome_autore,
        )
        if numero_id is not None:
            art = await article_ops.assign_article(db, art["id"], [numero_id])
        return art


@mcp.tool
async def lista_numeri() -> list[dict]:
    """Elenca i numeri della rivista (id, numero, mese, anno, stato)."""
    async with async_session() as db:
        return await article_ops.list_magazines(db)


@mcp.tool
async def lista_articoli(numero_id: Optional[int] = None, search: Optional[str] = None) -> list[dict]:
    """Elenca gli articoli, opzionalmente filtrati per numero o ricerca testo."""
    async with async_session() as db:
        return await article_ops.list_articles(db, magazine_id=numero_id, search=search)


@mcp.tool
async def leggi_articolo(id: int) -> dict:
    """Restituisce un articolo completo (Markdown + metadati)."""
    async with async_session() as db:
        art = await article_ops.get_article(db, id)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def modifica_articolo(
    id: int,
    titolo: Optional[str] = None,
    sottotitolo: Optional[str] = None,
    autore: Optional[str] = None,
    nome_autore: Optional[str] = None,
    contenuto_md: Optional[str] = None,
) -> dict:
    """Aggiorna i campi indicati di un articolo esistente."""
    fields = {k: v for k, v in {
        "titolo": titolo, "sottotitolo": sottotitolo, "autore": autore,
        "nome_autore": nome_autore, "contenuto_md": contenuto_md,
    }.items() if v is not None}
    async with async_session() as db:
        art = await article_ops.update_article(db, id, **fields)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def assegna_a_numero(id: int, numero_ids: list[int]) -> dict:
    """Assegna l'articolo a uno o più numeri (sostituisce le assegnazioni)."""
    async with async_session() as db:
        art = await article_ops.assign_article(db, id, numero_ids)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def genera_sommario(id: int) -> dict:
    """Genera il sommario AI dell'articolo (richiede ANTHROPIC_API_KEY)."""
    async with async_session() as db:
        art = await article_ops.generate_summary(db, id)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def anteprima_typst(contenuto_md: str, articolo_id: Optional[int] = None) -> str:
    """Converte il Markdown in Typst e lo restituisce, senza salvare nulla.

    Con `articolo_id`, i riferimenti a immagini con nome file nudo
    (es. `![](x.png)`) si risolvono nelle immagini caricate per quell'articolo.
    """
    return markdown_preview(contenuto_md, articolo_id=articolo_id)


def _decode_base64(contenuto_base64: str) -> bytes:
    """Decodifica base64, accettando anche un prefisso data URI."""
    data = contenuto_base64.strip()
    if data.startswith("data:") and "," in data:
        data = data.split(",", 1)[1]
    try:
        return base64.b64decode(data, validate=True)
    except Exception as exc:  # base64.binascii.Error e simili
        raise ValueError("contenuto_base64 non è una stringa base64 valida") from exc


@mcp.tool
async def carica_immagine(
    articolo_id: int,
    nome_file: str,
    contenuto_base64: str,
    mime: str = "",
    sovrascrivi: bool = True,
) -> dict:
    """Carica un'immagine legata a un articolo (max 10 MB).

    `nome_file` deve combaciare col riferimento nel Markdown
    (es. `![](x.png)` → serve `nome_file="x.png"`). Formati: PNG, JPG/JPEG,
    GIF, WEBP, SVG. `contenuto_base64` sono i byte del file in base64 (accetta
    anche un data URI). `mime` è dedotto dall'estensione se non fornito.
    Con `sovrascrivi=false` un nome già esistente dà errore. Ritorna
    {nome_file, url, bytes}.
    """
    content = _decode_base64(contenuto_base64)
    async with async_session() as db:
        return await article_ops.save_article_image(
            db, articolo_id, nome_file, content, mime=mime, sovrascrivi=sovrascrivi
        )


@mcp.tool
async def lista_immagini(articolo_id: int) -> list[dict]:
    """Elenca le immagini caricate per un articolo (nome_file, url, bytes, mime)."""
    async with async_session() as db:
        return await article_ops.list_article_images(db, articolo_id)


@mcp.tool
async def elimina_immagine(articolo_id: int, nome_file: str) -> dict:
    """Elimina un'immagine (file + record) caricata per un articolo."""
    async with async_session() as db:
        await article_ops.delete_article_image(db, articolo_id, nome_file)
        return {"ok": True}


@mcp.resource("guida://convenzioni")
def guida_convenzioni() -> str:
    """Guida alle convenzioni Markdown del template GEKO."""
    return CONVENZIONI
