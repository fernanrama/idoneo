"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ETIQUETAS, estadoBloques, mostrarValor } from "@/lib/bloques";
import { useOnboarding } from "@/lib/onboarding";
import { minutos, nombreDato } from "@/lib/revision";
import type { Revision } from "@/lib/tipos";
import type { useEntrevista } from "@/lib/useEntrevista";
import { useRevision } from "@/lib/useRevision";
import { IconoMotivo } from "./IconoMotivo";
import s from "./entrevista.module.css";
import { Anotado, Aura, BloquesNoche, BotonNoche, Icono, MarcaNoche, Ondas, clasesBoton } from "./visual";

type HookEntrevista = ReturnType<typeof useEntrevista>;
type RevisionAbierta = Extract<Revision, { open: true }>;

/**
 * La entrevista tal como la vive el cliente: el aura hace de entrevistador y solo se ve la pregunta
 * actual. Lo que responde el cliente no se muestra; solo un «Anotado» cuando el perfil gana un dato.
 * `compacto` es la versión para la columna izquierda del escenario del pitch.
 */
export function Entrevista({ e, compacto = false, alTerminar }: { e: HookEntrevista; compacto?: boolean; alTerminar?: React.ReactNode }) {
  const [teclado, setTeclado] = useState(false);
  // Las casillas viven aquí: si algo falla y vuelve el inicio, no hay que marcarlas otra vez.
  const [permisos, setPermisos] = useState({ ia: false, grabacion: false });
  const bloques = estadoBloques(e.perfil);
  const enCurso = bloques.find((b) => b.estado === "en_curso");
  const enMarcha = e.estado === "activa" || e.estado === "conectando";
  // «Ha cambiado algo»: si el cliente tiene una revisión abierta, la entrevista es corta y solo pregunta eso.
  const { clientId } = useOnboarding();
  const rev = useRevision(clientId, enMarcha || e.estado === "terminada" ? 2000 : undefined);
  const revision = !compacto && e.modo !== "guion" && rev?.open ? rev : null;

  return (
    <div className={`${s.raiz} ${compacto ? s.compacto : ""}`}>
      <header className={s.cabecera}>
        <MarcaNoche />
        {enMarcha && revision && <BarraRevision r={revision} />}
        {enMarcha && !revision && (
          <div className={s.bloquesCaja} style={{ margin: "0 auto" }}>
            <BloquesNoche bloques={bloques} />
          </div>
        )}
        <span className={`${s.datos} mono`} style={{ marginLeft: enMarcha ? undefined : "auto" }}>
          {e.modo === "guion" ? `Demo guiada · ${e.demo.paso} de ${e.demo.total} · datos simulados` : "Prototipo · datos simulados"}
        </span>
      </header>

      <main className={s.centro}>
        {!compacto && enMarcha && (
          <>
            <div className={`${s.lateral} ${s.lateralIzq} vidrio`}>
              {revision ? (
                <ProgresoRevision r={revision} onTerminar={e.terminar} />
              ) : (
                <>
                  <span className={`${s.titulo} mono`}>Ahora</span>
                  <p>{enCurso ? enCurso.nombre : "Cerrando la entrevista"}</p>
                </>
              )}
            </div>
            <div className={`${s.lateral} ${s.lateralDer} vidrio`}>
              {e.modo === "guion" ? (
                <UltimoDato e={e} />
              ) : (
                <>
                  <span className={`${s.titulo} mono`}>Privacidad</span>
                  <p>Lo que digas solo lo ve tu asesor, con la frase exacta.</p>
                </>
              )}
            </div>
          </>
        )}

        {(e.estado === "inactiva" || e.estado === "error") && (
          <Inicio e={e} compacto={compacto} permisos={permisos} setPermisos={setPermisos} revision={revision} />
        )}

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
            {e.modo === "texto" && e.error && (
              <p role="alert" className={s.error}>
                {e.error}{" "}
                <button className={s.demoBoton} style={{ display: "inline-flex" }} onClick={e.reintentar}>
                  Reintentar
                </button>
              </p>
            )}
            {e.modo === "guion" && (
              <div className={s.respuestaDemo} aria-live="polite">
                {e.demo.respuesta && (
                  <p key={e.demo.respuesta} className={`${s.burbuja} vidrio`}>
                    <span className="mono">Carmen</span>
                    {e.demo.respuesta}
                  </p>
                )}
              </div>
            )}
            <LineaEstado e={e} />
          </>
        )}

        {e.estado === "terminada" && (
          <div className={s.fin}>
            <Aura estado="anotado" tam={compacto ? 200 : 300} />
            <h1>
              {e.modo === "guion"
                ? "Listo. El perfil de Carmen está preparado."
                : revision
                  ? "Listo. Hemos anotado tus cambios."
                  : "Listo. Tu perfil ya está preparado."}
            </h1>
            <p className={s.finTexto}>
              {e.modo === "guion"
                ? "Cada dato lleva su frase y el aviso queda abierto para que la entidad lo revise antes de validar."
                : revision
                  ? "Una persona del banco revisará lo que ha cambiado. Hasta entonces se sigue usando tu perfil anterior, avisando de qué datos están en revisión."
                  : "Una persona del banco lo revisará antes de usarlo. Te avisaremos cuando esté listo."}
            </p>
            {revision && revision.remaining > 0 && (
              <p className={s.finTexto}>
                Han quedado {revision.remaining} {revision.remaining === 1 ? "pregunta" : "preguntas"} sin contestar. Puedes
                retomarlas cuando quieras desde tu perfil.
              </p>
            )}
            <div className={s.finAcciones}>
              {alTerminar ?? (
                <Link href="/onboarding/perfil">
                  <span className={clasesBoton.luz}>
                    {e.modo === "guion" ? "Ver el perfil de Carmen" : revision ? "Ver qué ha cambiado" : "Ver mi perfil"}
                  </span>
                </Link>
              )}
              {e.modo === "guion" && (
                <BotonNoche variante="vidrio" onClick={() => e.iniciarGuion()}>
                  Repetir la demo
                </BotonNoche>
              )}
            </div>
          </div>
        )}
      </main>

      {enMarcha && (
        <footer className={s.dock}>
          <div className={`${s.dockCaja} vidrio`}>
            {e.modo === "guion" && <ControlesDemo e={e} />}
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
  else if (e.asistente === "habla") contenido = <span className="mono">{e.modo === "guion" ? "El asistente pregunta" : "El asistente está hablando"}</span>;
  else if (e.asistente === "escucha")
    contenido = (
      <>
        <Ondas />
        <span className="mono">{e.modo === "guion" ? "Carmen responde" : e.modo === "texto" ? "Tu turno" : "Te escucho"}</span>
      </>
    );
  return (
    <div className={s.estadoLinea} role="status">
      {contenido}
    </div>
  );
}

type Permisos = { ia: boolean; grabacion: boolean };

function Inicio({ e, compacto, permisos, setPermisos, revision }: {
  e: HookEntrevista; compacto: boolean; permisos: Permisos; setPermisos: (p: Permisos) => void; revision: RevisionAbierta | null;
}) {
  const { ia, grabacion } = permisos;
  const setIa = (v: boolean) => setPermisos({ ...permisos, ia: v });
  const setGrabacion = (v: boolean) => setPermisos({ ...permisos, grabacion: v });
  const listo = ia && grabacion;
  // Entrevista corta del pitch: solo se ofrece con el modo asesor de demostración activo (en local).
  const [hayCorta, setHayCorta] = useState(false);
  useEffect(() => {
    let vivo = true;
    api.modoAsesor()
      .then((m) => vivo && setHayCorta(m.enabled && m.clients.includes("carmen-corta")))
      .catch(() => vivo && setHayCorta(false));
    return () => {
      vivo = false;
    };
  }, []);
  // Modo elegido en «Ha cambiado algo» (?modo=voz|texto): se resalta ese botón.
  const [preferido, setPreferido] = useState<string | null>(null);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- se lee una vez de la URL
    setPreferido(new URLSearchParams(window.location.search).get("modo"));
  }, []);
  if (revision) {
    const n = revision.questions.length;
    return (
      <div className={s.inicio}>
        <Aura estado="reposo" tam={compacto ? 200 : 220} />
        <h1>
          Vamos a <span className="texto-degradado">ponerte al día</span>
        </h1>
        <p>
          {revision.remaining < n
            ? `Ya llevas ${n - revision.remaining} de ${n}. Seguimos donde lo dejaste.`
            : `Solo ${n === 1 ? "una pregunta" : `${n} preguntas`}, unos ${minutos(n)} min. Lo demás de tu perfil se queda como está.`}
        </p>
        <div className={`${s.revInicio} vidrio`}>
          <span className={`${s.titulo} mono`}>Lo que nos has contado</span>
          <div className={s.revMotivos}>
            {revision.reasons.map((m, i) => (
              <span key={m.code} className={s.revMotivo} style={{ animationDelay: `${i * 0.08}s` }}>
                <IconoMotivo icono={m.icono} />
                {m.titulo}
              </span>
            ))}
          </div>
          <span className={`${s.titulo} mono`} style={{ marginTop: 6 }}>Te preguntaremos por</span>
          <ul className={s.revLista}>
            {revision.questions.map((q, i) => (
              <li key={q.path} className={q.respondida ? s.revHecha : ""} style={{ animationDelay: `${0.2 + i * 0.07}s` }}>
                {nombreDato(q.path)}
                {q.respondida && " · hecho"}
              </li>
            ))}
          </ul>
        </div>
        <div className={`${s.permisos} vidrio`}>
          <label className={s.permiso}>
            <input type="checkbox" checked={ia} onChange={(ev) => setIa(ev.target.checked)} />
            <span>Entiendo que hablaré con un asistente de inteligencia artificial y que una persona del banco revisará los cambios.</span>
          </label>
          <label className={s.permiso}>
            <input type="checkbox" checked={grabacion} onChange={(ev) => setGrabacion(ev.target.checked)} />
            <span>Acepto que se guarde la conversación para justificar los cambios. No se usará mi voz para identificarme.</span>
          </label>
        </div>
        <div className={s.modos}>
          <BotonNoche onClick={e.iniciarVoz} disabled={!listo} className={preferido === "voz" && listo ? s.revPreferido : undefined}>
            {Icono.micro}
            Hablar
          </BotonNoche>
          <BotonNoche variante="vidrio" onClick={e.iniciarTexto} disabled={!listo}
            className={preferido === "texto" && listo ? s.revPreferido : undefined} style={{ minHeight: 52, paddingInline: 24 }}>
            {Icono.teclado}
            Escribir
          </BotonNoche>
        </div>
        <p className={s.pista} aria-live="polite">
          {listo ? "Te leeremos lo que tenemos anotado y nos dices si sigue igual o qué ha cambiado." : "Marca las dos casillas para poder empezar."}
        </p>
        {e.error && (
          <p role="alert" className={s.error}>
            {e.error}
          </p>
        )}
      </div>
    );
  }
  return (
    <div className={s.inicio}>
      <Aura estado="reposo" tam={compacto ? 200 : 260} />
      <h1>
        Cuando quieras, <span className="texto-degradado">empezamos</span>
      </h1>
      <p>
        {e.corta
          ? "Carmen ya ha contado casi todo: faltan dos preguntas. Alrededor de un minuto."
          : "Una pregunta cada vez, sobre tus objetivos, tu situación y lo que sabes de inversión. Unos ocho minutos."}
      </p>
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
      {hayCorta && (
        <label className={`${s.permiso} vidrio`}>
          <input type="checkbox" checked={e.corta} onChange={(ev) => e.setCorta(ev.target.checked)} />
          <span>
            <strong>Entrevista corta del pitch.</strong> Carmen (datos simulados) ya tiene casi todo el perfil; en
            directo solo se comprueban sus conocimientos de renta variable y su reacción ante una caída.
          </span>
        </label>
      )}
      <p className={`${s.pista} mono`}>¿Cómo prefieres hacerlo?</p>
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
      <p className={s.pista} aria-live="polite">
        {listo
          ? "Hablando o escribiendo, como te resulte más cómodo. Al empezar, el asistente te lo confirmará en voz alta para que quede en tu expediente. Podrás pausar cuando quieras."
          : "Marca las dos casillas para poder empezar."}
      </p>
      <button className={s.demoBoton} onClick={() => e.iniciarGuion()}>
        <span className={s.demoPlay} aria-hidden="true">
          {Icono.play}
        </span>
        <span>
          <strong>Ver la demo guiada</strong>
          Carmen, 68 años · entrevista simulada de un minuto, con voz
        </span>
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

/** En la demo: el último dato que ha entrado en el perfil, con su valor. */
function UltimoDato({ e }: { e: HookEntrevista }) {
  const datos = e.perfil
    ? Object.entries(e.perfil.mifid)
        .filter(([r, f]) => f.value != null && !r.startsWith("disclosures."))
        .sort(([, a], [, b]) => b.updated_at.localeCompare(a.updated_at))
    : [];
  const n = datos.length;
  const ultimo = datos.find(([r]) => !r.endsWith("_months") && !r.endsWith("_capacity_eur")) ?? datos[0];
  return (
    <>
      <span className={`${s.titulo} mono`}>Anotado · {n} datos</span>
      {ultimo ? (
        <p key={ultimo[0]} className={s.anotadoNuevo}>
          {ETIQUETAS[ultimo[0]] ?? ultimo[0]}: <strong>{mostrarValor(ultimo[1].value)}</strong>
        </p>
      ) : (
        <p>Aún nada: cada dato aparecerá con la frase que lo justifica.</p>
      )}
    </>
  );
}

function ControlesDemo({ e }: { e: HookEntrevista }) {
  return (
    <>
      <BotonNoche variante="vidrio" redondo onClick={e.alternarPausa} aria-label={e.pausa ? "Reanudar la demo" : "Pausar la demo"}>
        {e.pausa ? Icono.play : Icono.pausa}
      </BotonNoche>
      <BotonNoche variante="vidrio" redondo onClick={e.demo.siguiente} aria-label="Saltar al siguiente turno">
        {Icono.saltar}
      </BotonNoche>
      <BotonNoche variante="vidrio" onClick={e.demo.cambiarVelocidad} aria-label={`Velocidad ${e.demo.velocidad}x`} style={{ minWidth: 64 }}>
        <span className="mono">{String(e.demo.velocidad).replace(".", ",")}×</span>
      </BotonNoche>
      <BotonNoche variante="vidrio" redondo onClick={e.demo.alternarVoz} aria-label={e.demo.voz ? "Quitar el sonido" : "Activar el sonido"} aria-pressed={e.demo.voz}>
        {e.demo.voz ? Icono.sonido : Icono.silencio}
      </BotonNoche>
    </>
  );
}

/** Cabecera de la microentrevista: una barrita por pregunta, que se enciende al contestarla. */
function BarraRevision({ r }: { r: RevisionAbierta }) {
  const hechas = r.questions.length - r.remaining;
  return (
    <div className={`${s.revBarra} vidrio`} role="progressbar" aria-valuemin={0} aria-valuemax={r.questions.length} aria-valuenow={hechas}
      aria-label="Preguntas de la revisión contestadas">
      <span className="mono">Revisión</span>
      <span className={s.revPuntos}>
        {r.questions.map((q) => <i key={q.path} className={q.respondida ? s.revHecha : ""} />)}
      </span>
      <span className="mono">{hechas} de {r.questions.length}</span>
    </div>
  );
}

/** Lateral de la microentrevista: qué toca ahora y, al acabar, el botón para cerrar. */
function ProgresoRevision({ r, onTerminar }: { r: RevisionAbierta; onTerminar: () => void }) {
  const siguiente = r.questions.find((q) => !q.respondida);
  return (
    <>
      <span className={`${s.titulo} mono`}>{siguiente ? "Ahora" : "Todo contestado"}</span>
      <p key={siguiente?.path ?? "fin"} className={s.anotadoNuevo}>
        {siguiente ? nombreDato(siguiente.path) : "Ya tenemos lo que necesitábamos."}
      </p>
      {!siguiente && (
        <button type="button" className={s.revListo} onClick={onTerminar}>
          Terminar
        </button>
      )}
    </>
  );
}
