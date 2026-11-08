-- 0001 · Esquema inicial del perfil (contrato 04, borrador) · Postgres / Supabase
--
-- Espejo de backend/app/perfil/persistencia/tablas.py. Si cambias una, cambia la otra:
-- tests/test_migraciones.py comprueba que tablas y columnas coinciden.
-- Se aplica con:  python -m app.perfil.persistencia.migrar --aplicar   (desde backend/)
-- No ejecutar contra Supabase sin autorización del responsable del backend.

create table clients (
    client_id   text primary key check (length(client_id) between 1 and 64),
    created_at  timestamptz not null default now()
);

-- Registro de solo añadir: cada fila es una versión completa de la capa MiFID del perfil.
create table profile_versions (
    client_id   text not null references clients (client_id),
    version     integer not null,
    status      text not null,
    reason      text not null,
    author      text not null,
    snapshot    jsonb not null,
    created_at  timestamptz not null default now(),
    primary key (client_id, version),
    constraint profile_versions_version_check check (version >= 1),
    constraint profile_versions_status_check
        check (status in ('draft', 'pending_validation', 'active', 'review_due'))
);

-- Capa personal: separada y con su propio consentimiento, para poder borrarla (RGPD)
-- sin tocar el registro MiFID.
create table personal_versions (
    client_id      text not null references clients (client_id),
    version        integer not null,
    consent_given  boolean not null,
    consent_at     timestamptz,
    data           jsonb not null,
    author         text not null,
    created_at     timestamptz not null default now(),
    primary key (client_id, version),
    constraint personal_versions_version_check check (version >= 1)
);

create table sessions (
    session_id       text primary key,
    client_id        text not null references clients (client_id),
    channel          text not null,
    started_at       timestamptz not null default now(),
    ended_at         timestamptz,
    conversation_id  text,
    constraint sessions_channel_check check (channel in ('voice', 'text'))
);

create index sessions_client_id_idx on sessions (client_id);

-- Transcripción: también de solo añadir, porque forma parte del expediente.
create table turns (
    session_id  text not null references sessions (session_id),
    turn_id     text not null,
    idx         integer not null,
    speaker     text not null,
    text        text not null,
    t_start     double precision,
    t_end       double precision,
    created_at  timestamptz not null default now(),
    primary key (session_id, turn_id),
    constraint turns_session_id_idx_key unique (session_id, idx),
    constraint turns_idx_check check (idx >= 0),
    constraint turns_speaker_check check (speaker in ('agent', 'client'))
);

-- Nada se sobrescribe: UPDATE y DELETE bloqueados en el registro (también para el rol postgres).
create function perfil_bloquear_cambio() returns trigger
language plpgsql as $$
begin
    raise exception 'La tabla % es de solo añadir: % no está permitido', tg_table_name, tg_op;
end
$$;

create trigger profile_versions_solo_anadir
    before update or delete on profile_versions
    for each row execute function perfil_bloquear_cambio();

create trigger turns_solo_anadir
    before update or delete on turns
    for each row execute function perfil_bloquear_cambio();

-- En la capa personal se permite DELETE (derecho de supresión), pero no UPDATE.
create trigger personal_versions_sin_update
    before update on personal_versions
    for each row execute function perfil_bloquear_cambio();

-- Row Level Security sin políticas: nadie accede por la Data API de Supabase.
-- El backend conecta con el rol postgres, que no está sujeto a RLS.
alter table clients enable row level security;
alter table profile_versions enable row level security;
alter table personal_versions enable row level security;
alter table sessions enable row level security;
alter table turns enable row level security;

-- Supabase: quitar cualquier permiso a los roles de la Data API (si existen en esta base).
do $$
declare
    rol text;
begin
    foreach rol in array array['anon', 'authenticated'] loop
        if exists (select 1 from pg_roles where rolname = rol) then
            execute format(
                'revoke all on clients, profile_versions, personal_versions, sessions, turns from %I', rol);
            execute format('revoke execute on function perfil_bloquear_cambio() from %I', rol);
        end if;
    end loop;
end
$$;
