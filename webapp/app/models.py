"""Database models for GEKO Magazine Web App."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


# Tabella associazione many-to-many: Articoli <-> Numeri GEKO
article_magazines = Table(
    'article_magazines',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('magazine_id', Integer, ForeignKey('magazines.id'), primary_key=True),
    Column('ordine', Integer, default=0),  # posizione dell'articolo nel numero
)


class MagazineStatus(str, enum.Enum):
    BOZZA = "bozza"
    PUBBLICATO = "pubblicato"


class Magazine(Base):
    """Un numero della rivista."""
    __tablename__ = "magazines"

    id = Column(Integer, primary_key=True)
    numero = Column(String(10), nullable=False)  # "67", "68"
    mese = Column(String(20), nullable=False)
    anno = Column(String(4), nullable=False)
    stato = Column(Enum(MagazineStatus), default=MagazineStatus.BOZZA)
    editoriale = Column(Text, default="")
    editoriale_autore = Column(String(100), default="")
    copertina_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazione many-to-many con articoli
    articles = relationship(
        "Article",
        secondary=article_magazines,
        back_populates="magazines",
        order_by=article_magazines.c.ordine
    )
    copertina = relationship("Image", foreign_keys=[copertina_id])


class Article(Base):
    """Un articolo della rivista."""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    titolo = Column(String(200), nullable=False)
    sottotitolo = Column(String(300), default="")
    autore = Column(String(50), default="")  # nominativo radio
    nome_autore = Column(String(100), default="")  # nome reale
    contenuto_md = Column(Text, default="")  # markdown originale
    contenuto_typ = Column(Text, default="")  # typst generato
    sommario_llm = Column(Text, default="")  # generato da Claude
    ordine = Column(Integer, default=0)  # posizione di default
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazione many-to-many con numeri GEKO
    magazines = relationship(
        "Magazine",
        secondary=article_magazines,
        back_populates="articles"
    )
    images = relationship("Image", back_populates="article")


class Image(Base):
    """Un'immagine caricata."""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    alt_text = Column(String(300), default="")  # testo alternativo/descrizione
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="images")

    @property
    def url(self):
        """URL pubblico dell'immagine."""
        return f"/uploads/{self.filename}"

    @property
    def is_published(self):
        """True se l'immagine è in un articolo pubblicato."""
        if not self.article:
            return False
        return any(
            mag.stato == MagazineStatus.PUBBLICATO
            for mag in self.article.magazines
        )


class Config(Base):
    """
    Configurazione globale dell'applicazione.

    Memorizza parametri chiave-valore per configurazioni
    che valgono per tutti i numeri della rivista.

    Parametri predefiniti:
    - ultimo_numero: numero dell'ultimo GEKO pubblicato (es. "67")
    - titolo_rivista: nome della rivista
    - sottotitolo_rivista: descrizione/sottotitolo
    - sito_web: URL del sito
    - template_typst: template Typst personalizzato (futuro)
    """
    __tablename__ = "config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")
    description = Column(String(500), default="")  # descrizione per UI
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Valori di default per le configurazioni
    DEFAULTS = {
        "ultimo_numero": ("67", "Numero dell'ultimo GEKO pubblicato"),
        "titolo_rivista": ("GEKO Radio Magazine", "Titolo della rivista"),
        "sottotitolo_rivista": ("Rivista aperiodica del Mountain QRP Club", "Sottotitolo/descrizione"),
        "sito_web": ("https://www.mqc.it", "Sito web del club"),
        "email_redazione": ("redazione@mqc.it", "Email della redazione"),
        "claude_model": ("claude-3-5-haiku-20241022", "Modello Claude per generazione sommari AI"),
    }

    @classmethod
    async def get(cls, db, key: str, default: str = "") -> str:
        """Ottiene un valore di configurazione."""
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.key == key))
        config = result.scalar_one_or_none()
        if config:
            return config.value
        # Ritorna default dal DEFAULTS o quello passato
        if key in cls.DEFAULTS:
            return cls.DEFAULTS[key][0]
        return default

    @classmethod
    async def set(cls, db, key: str, value: str, description: str = None):
        """Imposta un valore di configurazione."""
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.key == key))
        config = result.scalar_one_or_none()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            desc = description or (cls.DEFAULTS.get(key, ("", ""))[1])
            config = cls(key=key, value=value, description=desc)
            db.add(config)
        await db.commit()

    @classmethod
    async def get_all(cls, db) -> dict:
        """Ottiene tutte le configurazioni come dizionario."""
        from sqlalchemy import select
        result = await db.execute(select(cls))
        configs = {c.key: c for c in result.scalars().all()}

        # Unisci con i default (per mostrare anche quelli non ancora salvati)
        all_configs = {}
        for key, (default_value, desc) in cls.DEFAULTS.items():
            if key in configs:
                all_configs[key] = {
                    "value": configs[key].value,
                    "description": configs[key].description or desc,
                    "updated_at": configs[key].updated_at
                }
            else:
                all_configs[key] = {
                    "value": default_value,
                    "description": desc,
                    "updated_at": None
                }
        return all_configs
