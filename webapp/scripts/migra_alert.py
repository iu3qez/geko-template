"""Converte i box '!!!' del vecchio formato in GitHub-alert '> [!NOTE]'.
Idempotente: se non trova '!!!' non tocca nulla.

Supporta sia la forma con titolo (`!!! "Titolo"` / `!!! tipo "Titolo"`) sia
la forma nuda `!!!` senza tipo né titolo (quest'ultima è quella usata
dall'unico articolo reale in produzione, id 13)."""
import re
import sqlite3

BLOCK = re.compile(
    r'^!!![ \t]*(?:(?:\w+[ \t]*)?"([^"]*)")?[ \t]*\n(.*?)^!!![ \t]*$',
    re.MULTILINE | re.DOTALL,
)


def convert(md: str) -> str:
    def repl(m):
        titolo = m.group(1) or ""
        corpo = m.group(2).rstrip('\n')
        righe = '\n'.join('> ' + l if l.strip() else '>'
                          for l in corpo.split('\n'))
        header = f'> [!NOTE] {titolo}' if titolo else '> [!NOTE]'
        return f'{header}\n{righe}\n'
    return BLOCK.sub(repl, md)


def main():
    con = sqlite3.connect("data/geko.db")
    rows = con.execute(
        "SELECT id, contenuto_md FROM articles WHERE contenuto_md LIKE '%!!!%'"
    ).fetchall()
    for aid, md in rows:
        new = convert(md)
        if new != md:
            con.execute("UPDATE articles SET contenuto_md=? WHERE id=?", (new, aid))
            print("migrato articolo", aid)
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
