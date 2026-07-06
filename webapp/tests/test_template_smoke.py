# webapp/tests/test_template_smoke.py
import uuid
from pathlib import Path
import typst

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"
# typst richiede che il file di ingresso sia contenuto in `root`: usiamo
# typst/generated/ (già gitignorato, vedi webapp/.gitignore) invece del
# tmp_path di pytest, che vive fuori dal repo e farebbe fallire il compile.
GENERATED_DIR = WEBAPP_DIR / "typst" / "generated"


def test_box_evidenza_tipi_e_scope():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    doc = GENERATED_DIR / f"test_smoke_{uuid.uuid4().hex}.typ"
    try:
        doc.write_text(
            # Path assoluto rispetto a `root` (REPO_DIR): typst risolve "/x" come
            # root-relative, non come path filesystem assoluto.
            '#import "/template.typ": *\n'
            '#set page(width: 12cm, height: auto)\n'
            '#box-evidenza(titolo: "T", tipo: "warning")[corpo]\n'
            '#box-evidenza(titolo: "Vecchia")[retro-compatibile]\n'
            '#assert(type(geko-md-scope) == dictionary)\n',
            encoding="utf-8",
        )
        pdf = typst.compile(str(doc), root=str(REPO_DIR), package_path=str(PKG_PATH))
        assert len(pdf) > 1000
    finally:
        doc.unlink(missing_ok=True)
