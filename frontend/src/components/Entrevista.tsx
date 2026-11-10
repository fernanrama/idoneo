"use client";

import Link from "next/link";
import { useState } from "react";
import { estadoBloques } from "@/lib/bloques";
import type { useEntrevista } from "@/lib/useEntrevista";
import s from "./entrevista.module.css";
import { Anotado, Aura, BloquesNoche, BotonNoche, Icono, MarcaNoche, Ondas, clasesBoton } from "./visual";

type HookEntrevista = ReturnType<typeof useEntrevista>;

/**
 * La entrevista tal como la vive el cliente: el aura hace de entrevistador y solo se ve la pregunta
 * actual. Lo que responde el cliente no se muestra; solo un «Anotado» cuando el perfil gana un dato.
 * `compacto` es la versión para la columna izquierda del escenario del pitch.
 */
export function Entrevista({ e, compacto = false, alTerminar }: { e: HookEntrevista; compacto?: boolean; alTerminar?: React.ReactNode }) {
  const [teclado, setTeclado] = useState(false);
  const bloques = estadoBloques(e.perfil);
  const enCurso = bloques.find((b) => b.estado === "en_curso");
  const enMarcha = e.estado === "activa" || e.estado === "conectando";

  return (
    <div className={`${s.raiz} ${compacto ? s.compacto : ""}`}>
      <header className={s.cabecera}>
        <MarcaNoche />
        {enMarcha && (
          <div className={s.bloquesCaja} style={{ margin: "0 auto" }}>
            <BloquesNoche bloques={bloques} />
          </div>
        )}
        <span className={`${s.datos} mono`} style={{ marginLeft: enMarcha ? undefined : "auto" }}>
          {e.modo === "guion" ? "Demo guiada · datos simulados" : "Prototipo · datos simulados"}
        </span>
      </header>

      <main className={s.centro}>
        {!compacto && enMarcha && (
          <>
            <div className={`${s.lateral} ${s.lateralIzq} vidrio`}>
              <span className={`${s.titulo} mono`}>Ahora</span>
              <p>{enCurso ? enCurso.nombre : "Cerrando la entrevista"}</p>
            </div>
            <div className={`${s.lateral} ${s.lateralDer} vidrio`}>
              <span className={`${s.titulo} mono`}>Privacidad</span>
              <p>Lo que digas solo lo ve tu asesor, con la frase exacta.</p>
            </div>
          </>
        )}

        {(e.estado === "inactiva" || e.estado === "error") && <Inicio e={e} compacto={compacto} />}

        {enMarcha && (
          <>
            <button
              onClick={e.alternarPausa}
              aria-label={e.pausa ? "Reanudar la entrevista" : "Pausar la entrevista"}
              style={{ background: "none", border: 0, padding: 0 }}
            >
              <Aura estado={e.asistente} tam={compacto ? 240 : 380} />
            </button>
            <div className={s.zonaPregunta} aria-live="polite" aria-label="Pregunta del asistente">
              {e.pregunta && (
                <p key={e.pregunta} className={s.pregunta}>
                  {e.pregunta}
                </p>
              )}
            </div>
            <LineaEstado e={e} />
          </>
        )}

        {e.estado === "terminada" && (
          <div className={s.fin}>
            <Aura estado="anotado" tam={compacto ? 200 : 300} />
            <h1>Listo. Tu perfil ya está preparado.</h1>
            <div className={s.finAcciones}>
              {alTerminar ?? (
                <Link href="/onboarding/perfil">
                  <span className={clasesBoton.luz}>Ver mi perfil</span>
                </Link>
              )}
            </div>
          </div>
        )}
      </main>

      {enMarcha && (
        <footer className={s.dock}>
          <div className={`${s.dockCaja} vidrio`}>
            {e.modo === "voz" && (
              <BotonNoche variante="vidrio" redondo onClick={() => setTeclado((t) => !t)} aria-label="Escribir en lugar de hablar" aria-pressed={teclado}>
                {Icono.teclado}
              </BotonNoche>
            )}
            {(e.modo === "texto" || (e.modo === "voz" && teclado)) && <Respuesta onEnviar={e.enviarTexto} deshabilitada={e.asistente === "pensando"} />}
            {e.modo === "voz" && (
              <button
                className={`${s.micro} ${e.asistente === "escucha" ? s.microVivo : ""} ${e.pausa ? s.microApagado : ""}`}
                onClick={e.alternarPausa}
                aria-label={e.pausa ? "Activar el micrófono" : "Silenciar el micrófono"}
                aria-pressed={!e.pausa}
              >
                {Icono.micro}
              </button>
            )}
            <BotonNoche variante="vidrio" redondo className={s.terminarBoton} onClick={e.terminar} aria-label="Terminar la entrevista">
              {Icono.cerrar}
            </BotonNoche>
          </div>
        </footer>
      )}
    </div>
  );
}

function LineaEstado({ e }: { e: HookEntrevista }) {
  let contenido: React.ReactNode = null;
  if (e.asistente === "anotado") contenido = <Anotado />;
  else if (e.asistente === "pausa") contenido = <span className="mono">En pausa · toca el aura para seguir</span>;
  else if (e.asistente === "pensando") contenido = <span className="mono">Pensando…</span>;
  else if (e.asistente === "habla") contenido = <span className="mono">El asistente está hablando</span>;
  else if (e.asistente === "escucha")
    contenido = (
      <>
        <Ondas />
        <span className="mono">{e.modo === "texto" ? "Tu turno" : "Te escucho"}</span>
      </>
    );
  return (
    <div className={s.estadoLinea} role="status">
      {contenido}
    </div>
  );
}

function Inicio({ e, compacto }: { e: HookEntrevista; compacto: boolean }) {
  const [ia, setIa] = useState(false);
  const [grabacion, setGrabacion] = useState(false);
  const listo = ia && grabacion;
  return (
    <div className={s.inicio}>
      <Aura estado="reposo" tam={compacto ? 200 : 260} />
      <h1>
        Cuando quieras, <span className="texto-degradado">empezamos</span>
      </h1>
      <p>Una pregunta cada vez, sobre tus objetivos, tu situación y lo que sabes de inversión. Unos ocho minutos.</p>
      <div className={`${s.permisos} vidrio`}>
        <label className={s.permiso}>
          <input type="checkbox" checked={ia} onChange={(ev) => setIa(ev.target.checked)} />
          <span>Entiendo que hablaré con un asistente de inteligencia artificial y que una persona del banco revisará el resultado.</span>
        </label>
        <label className={s.permiso}>
          <input type="checkbox" checked={grabacion} onChange={(ev) => setGrabacion(ev.target.checked)} />
          <span>Acepto que se guarde la conversación para justificar mi perfil. No se usará mi voz para identificarme.</span>
        </label>
      </div>
      <div className={s.modos}>
        <BotonNoche onClick={e.iniciarVoz} disabled={!listo}>
          {Icono.micro}
          Hablar
        </BotonNoche>
        <BotonNoche variante="vidrio" onClick={e.iniciarTexto} disabled={!listo} style={{ minHeight: 52, paddingInline: 24 }}>
          {Icono.teclado}
          Escribir
        </BotonNoche>
      </div>
      <button className={s.enlaceDemo} onClick={() => e.iniciarGuion(1)}>
        Ver la demo guiada (datos simulados)
      </button>
      {e.error && (
        <p role="alert" className={s.error}>
          {e.error}
        </p>
      )}
    </div>
  );
}

function Respuesta({ onEnviar, deshabilitada }: { onEnviar: (t: string) => void; deshabilitada?: boolean }) {
  const [texto, setTexto] = useState("");
  return (
    <form
      style={{ display: "flex", gap: 8, alignItems: "center" }}
      onSubmit={(ev) => {
        ev.preventDefault();
        if (!texto.trim() || deshabilitada) return;
        onEnviar(texto.trim());
        setTexto("");
      }}
    >
      <label className="oculto-visual" htmlFor="respuesta">
        Tu respuesta
      </label>
      <input
        id="respuesta"
        className={s.entrada}
        value={texto}
        onChange={(ev) => setTexto(ev.target.value)}
        placeholder="Escribe tu respuesta…"
        autoComplete="off"
        autoFocus
      />
      <BotonNoche variante="vidrio" redondo type="submit" aria-label="Enviar" disabled={deshabilitada || !texto.trim()}>
        {Icono.enviar}
      </BotonNoche>
    </form>
  );
}
