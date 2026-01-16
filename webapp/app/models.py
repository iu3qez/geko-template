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
        order_by="Article.ordine"
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
        return f"/images/{self.filename}"

    @property
    def is_published(self):
        """True se l'immagine è in un articolo pubblicato."""
        if not self.article:
            return False
        return any(
            mag.stato == MagazineStatus.PUBBLICATO
            for mag in self.article.magazines
        )
