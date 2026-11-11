-- 0002 · Audio de cada sesión de voz · Postgres / Supabase
--
-- Una fila por sesión: el audio de la llamada (descargado de ElevenLabs al acabar) y los tiempos reales
-- de cada turno, para que cada dato del perfil suene con el fragmento que lo justifica.
-- Espejo de backend/app/perfil/persistencia/tablas.py (tabla session_audio).
-- Se aplica con:  python -m app.perfil.persistencia.migrar --aplicar   (desde backend/)
-- Mientras no se aplique, el backend arranca igual y solo desactiva el audio de las pruebas.

create table session_audio (
    session_id       text primary key references sessions (session_id),
    conversation_id  text not null,
    content_type     text not null,
    size_bytes       integer not null,
    duration_s       double precision,
    timings          jsonb not null,
    transcript       jsonb not null,
    audio            bytea not null,
    created_at       timestamptz not null default now(),
    constraint session_audio_size_check check (size_bytes > 0)
);

-- Forma parte del expediente, como la transcripción: de solo añadir.
create trigger session_audio_solo_anadir
    before update or delete on session_audio
    for each row execute function perfil_bloquear_cambio();

create trigger session_audio_sin_truncate
    before truncate on session_audio
    for each statement execute function perfil_bloquear_cambio();

-- Row Level Security sin políticas y sin permisos para la Data API de Supabase (igual que en 0001).
alter table session_audio enable row level security;

do $$
declare
    rol text;
begin
    foreach rol in array array['anon', 'authenticated'] loop
        if exists (select 1 from pg_roles where rolname = rol) then
            execute format('revoke all on session_audio from %I', rol);
        end if;
    end loop;
end
$$;
