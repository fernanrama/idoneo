"""Tablas del perfil. Espejo de backend/migraciones/*.sql (Postgres).

En SQLite (local y tests) se crean desde aquí; en Postgres/Supabase, solo con las migraciones.
`tests/test_migraciones.py` comprueba que ambas definiciones no se separan.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    LargeBinary,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()
JSON_ = JSON().with_variant(JSONB(), "postgresql")
FECHA = DateTime(timezone=True)

ESTADOS = "('draft','pending_validation','active','review_due')"

clients = Table(
    "clients", metadata,
    Column("client_id", Text, primary_key=True),
    Column("created_at", FECHA, nullable=False),
)

# Registro de solo añadir: cada fila es una versión completa del perfil (capa MiFID).
profile_versions = Table(
    "profile_versions", metadata,
    Column("client_id", Text, ForeignKey("clients.client_id"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("author", Text, nullable=False),
    Column("snapshot", JSON_, nullable=False),
    Column("created_at", FECHA, nullable=False),
    PrimaryKeyConstraint("client_id", "version"),
    CheckConstraint("version >= 1", name="profile_versions_version_check"),
    CheckConstraint(f"status in {ESTADOS}", name="profile_versions_status_check"),
)

# Capa personal: separada para poder borrarla (RGPD) sin tocar el registro MiFID.
personal_versions = Table(
    "personal_versions", metadata,
    Column("client_id", Text, ForeignKey("clients.client_id"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("consent_given", Boolean, nullable=False),
    Column("consent_at", FECHA),
    Column("data", JSON_, nullable=False),
    Column("author", Text, nullable=False),
    Column("created_at", FECHA, nullable=False),
    PrimaryKeyConstraint("client_id", "version"),
    CheckConstraint("version >= 1", name="personal_versions_version_check"),
)

sessions = Table(
    "sessions", metadata,
    Column("session_id", Text, primary_key=True),
    Column("client_id", Text, ForeignKey("clients.client_id"), nullable=False),
    Column("channel", Text, nullable=False),
    Column("started_at", FECHA, nullable=False),
    Column("ended_at", FECHA),
    Column("conversation_id", Text),  # id de la conversación en ElevenLabs
    CheckConstraint("channel in ('voice','text')", name="sessions_channel_check"),
)

# Transcripción: también de solo añadir (forma parte del expediente).
turns = Table(
    "turns", metadata,
    Column("session_id", Text, ForeignKey("sessions.session_id"), nullable=False),
    Column("turn_id", Text, nullable=False),
    Column("idx", Integer, nullable=False),
    Column("speaker", Text, nullable=False),
    Column("text", Text, nullable=False),
    Column("t_start", Float),
    Column("t_end", Float),
    Column("created_at", FECHA, nullable=False),
    PrimaryKeyConstraint("session_id", "turn_id"),
    UniqueConstraint("session_id", "idx", name="turns_session_id_idx_key"),
    CheckConstraint("idx >= 0", name="turns_idx_check"),
    CheckConstraint("speaker in ('agent','client')", name="turns_speaker_check"),
)

# Audio de cada sesión de voz (prueba de cada dato) y tiempos reales de cada turno según ElevenLabs.
# Una fila por sesión, de solo añadir como la transcripción: forma parte del expediente. Migración 0002.
session_audio = Table(
    "session_audio", metadata,
    Column("session_id", Text, ForeignKey("sessions.session_id"), primary_key=True),
    Column("conversation_id", Text, nullable=False),
    Column("content_type", Text, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("duration_s", Float),
    Column("timings", JSON_, nullable=False),     # {turn_id: [inicio, fin]} en segundos del audio
    Column("transcript", JSON_, nullable=False),  # transcripción oficial de ElevenLabs (rol, texto, segundo)
    Column("audio", LargeBinary, nullable=False),
    Column("created_at", FECHA, nullable=False),
    CheckConstraint("size_bytes > 0", name="session_audio_size_check"),
)

# Tablas protegidas contra UPDATE/DELETE (y en personal_versions, solo contra UPDATE).
SOLO_ANADIR = ("clients", "profile_versions", "turns", "session_audio")
SIN_UPDATE = ("personal_versions",)
# Tablas que un Postgres ya desplegado puede no tener todavía (migración posterior): si faltan, el backend
# arranca igual y esa función queda desactivada con un aviso, en vez de no arrancar.
OPCIONALES = ("session_audio",)
