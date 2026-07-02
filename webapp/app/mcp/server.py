"""Server MCP GEKO: tool per creare/gestire articoli conformi al template."""

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
async def crea_numero(numero: str, mese: str, anno: str, stato: str = "bozza") -> dict:
    """Crea un nuovo numero della rivista.

    `mese` in italiano (es. "Luglio"), `anno` a 4 cifre, `stato` = bozza|pubblicato
    (default bozza). Ritorna il record creato (id, numero, mese, anno, stato).
    """
    async with async_session() as db:
        return await article_ops.create_magazine(
            db, numero=numero, mese=mese, anno=anno, stato=stato
        )


@mcp.tool
async def modifica_numero(
    id: int,
    numero: Optional[str] = None,
    mese: Optional[str] = None,
    anno: Optional[str] = None,
    stato: Optional[str] = None,
) -> dict:
    """Aggiorna i campi indicati di un numero esistente (id, numero, mese, anno, stato)."""
    fields = {k: v for k, v in {
        "numero": numero, "mese": mese, "anno": anno, "stato": stato,
    }.items() if v is not None}
    async with async_session() as db:
        mag = await article_ops.update_magazine(db, id, **fields)
        if mag is None:
            raise ValueError(f"Numero {id} non trovato")
        return mag


@mcp.tool
async def elimina_numero(id: int, forza: bool = False) -> dict:
    """Elimina un numero. Fallisce se ha articoli associati (usa forza=True).

    Non elimina gli articoli, solo le associazioni al numero.
    """
    async with async_session() as db:
        ok = await article_ops.delete_magazine(db, id, forza=forza)
        if ok is None:
            raise ValueError(f"Numero {id} non trovato")
        return {"eliminato": id}


@mcp.tool
async def genera_sommario(id: int) -> dict:
    """Genera il sommario AI dell'articolo (richiede ANTHROPIC_API_KEY)."""
    async with async_session() as db:
        art = await article_ops.generate_summary(db, id)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def anteprima_typst(contenuto_md: str) -> str:
    """Converte il Markdown in Typst e lo restituisce, senza salvare nulla."""
    return markdown_preview(contenuto_md)


@mcp.resource("guida://convenzioni")
def guida_convenzioni() -> str:
    """Guida alle convenzioni Markdown del template GEKO."""
    return CONVENZIONI
