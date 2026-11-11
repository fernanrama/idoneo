"use client";

import Link from "next/link";
import { useState } from "react";
import { valorConUnidad } from "@/components/PanelVivo";
import { type EstadoClip, type Fragmento, useReproductor } from "@/lib/audio";
import { ETIQUETAS, FUENTES, mostrarValor } from "@/lib/bloques";
import { GUION_CARMEN } from "@/lib/guion";
import type { Perfil } from "@/lib/tipos";
import s from "./asesor.module.css";

const normalizar = (texto: string) =>
  texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9ñ ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

/** La frase de Carmen grabada para la demo (`public/demo/carmen/`) que contiene la cita. */
function audioDeLaCita(cita: string): Fragmento | null {
  const c = normalizar(cita);
  if (!c) return null;
  const indice = GUION_CARMEN.findIndex((t) => {
    if (t.speaker !== "client") return false;
    const texto = normalizar(t.text);
    return texto.includes(c) || c.includes(texto);
  });
  if (indice < 0) return null;
  return { url: `/demo/carmen/${String(indice).padStart(2, "0")}-client.mp3`, start: 0, end: null, exact: true, privado: false };
}

/**
 * Lo que recibe el asesor al acabar la demo guiada: el perfil hecho, cada dato con su frase exacta
 * y su audio, y la validación. La validación aquí es una SIMULACIÓN local: no llama al servidor.
 * La validación real vive en la vista de la entidad, con clave.
 */
export function AsesorDemo({ perfil, alVolver }: { perfil: Perfil; alVolver: () => void }) {
  const [validado, setValidado] = useState(false);
  const { activo, reproducir } = useReproductor(perfil.client_id);
  const estadoDe = (clave: string): EstadoClip => (activo?.clave === clave ? activo.estado : "parado");

  const datos = Object.entries(perfil.mifid).filter(([ruta, f]) => f.value != null && !ruta.startsWith("disclosures."));
  const conCita = datos.filter(([, f]) => f.source !== "calculated" && f.evidence[0]?.quote);
  const calculados = datos.filter(([, f]) => f.source === "calculated");
  const alertas = perfil.alerts.filter((a) => a.status === "open");
  const conAlerta = new Set(alertas.map((a) => a.path));
  // Primero, lo que el asesor tiene que mirar.
  conCita.sort(([a], [b]) => Number(conAlerta.has(b)) - Number(conAlerta.has(a)));

  const cita = (clave: string, texto: string) => {
    const clip = audioDeLaCita(texto);
    return (
      <div className={s.cita}>
        <BotonEscuchar clip={clip} estado={estadoDe(clave)} alPulsar={(c) => void reproducir(clave, c)} />
        <span>«{texto}»</span>
      </div>
    );
  };

  return (
    <section className={s.raiz} aria-label="Lo que recibe el asesor">
      <header className={s.cab}>
        <div>
          <span className={s.kicker}>Vista del asesor · demo</span>
          <h2>Carmen, 68 años</h2>
        </div>
        <span className={`${s.estado} ${validado ? s.estadoOk : s.estadoRevisar}`} role="status">
          {validado ? "Validado por una persona · simulación" : "Por validar"}
        </span>
      </header>
      <p className={s.entrada}>
        El perfil llega hecho. Cada dato trae la frase exacta que lo justifica; pulsa ▶ para oír a Carmen decirla.
      </p>

      {alertas.map((a) => (
        <div key={a.id} className={s.alerta}>
          <strong>{a.flag === "declared_vs_demonstrated" ? "Lo que dice frente a lo que demuestra" : "Revisar con el cliente"}</strong>
          <p>{a.message}</p>
          {a.evidence[0]?.quote && cita(`alerta-${a.id}`, a.evidence[0].quote)}
        </div>
      ))}

      <ul className={s.datos}>
        {conCita.map(([ruta, f]) => (
          <li key={ruta} className={conAlerta.has(ruta) ? s.datoAviso : ""}>
            <div className={s.datoCab}>
              <span>{ETIQUETAS[ruta] ?? ruta}</span>
              <span className={s.chip}>{FUENTES[f.source] ?? f.source}</span>
            </div>
            <strong className={s.valor}>{valorConUnidad(ruta, f.value)}</strong>
            {f.declared != null && f.declared !== f.value && <span className={s.declaro}>Declaró «{mostrarValor(f.declared)}»</span>}
            {cita(ruta, f.evidence[0].quote)}
          </li>
        ))}
      </ul>

      {calculados.length > 0 && (
        <div className={s.calculados}>
          <span className={s.kicker}>Calculado por código, no por la IA</span>
          <dl>
            {calculados.map(([ruta, f]) => (
              <div key={ruta}>
                <dt>{ETIQUETAS[ruta] ?? ruta}</dt>
                <dd>{valorConUnidad(ruta, f.value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      <footer className={s.pie}>
        <p>
          {validado
            ? "Validado. A partir de aquí, el agente de la entidad puede consultar este perfil. Es una simulación dentro de la demo: no cambia ningún dato."
            : "Hasta que una persona lo valida, el agente de la entidad no puede usar este perfil."}
        </p>
        <div className={s.acciones}>
          {!validado && (
            <button type="button" className={s.validar} onClick={() => setValidado(true)}>
              Validar perfil
            </button>
          )}
          <Link href="/onboarding/perfil" className={validado ? s.validar : s.secundario}>
            Ver el perfil de Carmen →
          </Link>
          <button type="button" className={s.secundario} onClick={alVolver}>
            ← Cómo se construyó
          </button>
        </div>
      </footer>
    </section>
  );
}

function BotonEscuchar({ clip, estado, alPulsar }: { clip: Fragmento | null; estado: EstadoClip; alPulsar: (c: Fragmento) => void }) {
  if (!clip) return <span className={`${s.play} ${s.playApagado}`} aria-hidden="true" />;
  const texto = estado === "sonando" ? "Parar" : estado === "cargando" ? "Cargando el audio" : estado === "error" ? "No se pudo reproducir; volver a intentarlo" : "Escuchar la frase";
  return (
    <button type="button" className={`${s.play} ${estado === "sonando" ? s.playSonando : ""}`} onClick={() => alPulsar(clip)} aria-label={texto} title={texto} aria-pressed={estado === "sonando"}>
      {estado === "sonando" ? (
        <i className={s.cuadro} aria-hidden="true" />
      ) : estado === "cargando" ? (
        "…"
      ) : estado === "error" ? (
        "!"
      ) : (
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">
          <path d="M8 5.5v13l11-6.5z" />
        </svg>
      )}
    </button>
  );
}
