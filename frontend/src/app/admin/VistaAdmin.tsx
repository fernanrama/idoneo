"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { BarraEntidad } from "@/components/BarraEntidad";
import { api } from "@/lib/api";
import { ESTADOS } from "@/lib/bloques";
import type { ClienteBandeja } from "@/lib/tipos";
import s from "../entidad/[cid]/entidad.module.css";

const CLIENTE = /^[a-z0-9][a-z0-9_-]{0,63}$/;
const SONDEO_MS = 5000;
const POR_VALIDAR = new Set(["pending_validation", "review_due"]);
const campo: React.CSSProperties = {
  width: "100%", maxWidth: 420, minHeight: 48, padding: "0 16px", borderRadius: 12,
  border: "1px solid rgba(18,18,42,0.18)", background: "#ffffff", color: "inherit", font: "inherit",
};

const fecha = (iso: string) =>
  new Date(iso).toLocaleString("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

/**
 * Entrada de la entidad: se inicia sesión con la clave del equipo y se llega a la bandeja de perfiles.
 * Desde ahí (o con `?cliente=<código>`, como enlaza «Mi perfil») se abre el expediente para revisar y validar.
 */
export default function VistaAdmin() {
  const router = useRouter();
  const params = useSearchParams();
  const sugerido = params.get("cliente") ?? "";
  // A dónde volver tras meter la clave (p. ej. /operaciones). Solo rutas propias.
  const volver = /^\/[a-z]/.test(params.get("volver") ?? "") ? params.get("volver")! : null;
  const [estado, setEstado] = useState<{ enabled: boolean; logged: boolean } | null>(null);
  const [clave, setClave] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api.sesionAdmin().then(setEstado).catch(() => setEstado({ enabled: false, logged: false }));
  }, []);
  useEffect(cargar, [cargar]);

  // Viene de «Validarlo como entidad» o de otra pantalla de la entidad: con la sesión iniciada, directo allí.
  useEffect(() => {
    if (!estado?.logged) return;
    if (CLIENTE.test(sugerido)) router.replace(`/entidad/${encodeURIComponent(sugerido)}`);
    else if (volver && volver !== "/admin") router.replace(volver);
  }, [estado, sugerido, volver, router]);

  const entrar = async (e: React.FormEvent) => {
    e.preventDefault();
    setOcupado(true);
    setError(null);
    try {
      await api.entrarAdmin(clave);
      setClave("");
      cargar();
    } catch (err) {
      const status = (err as { status?: number }).status;
      setError(status === 401 ? "Clave incorrecta." : status === 404 ? "La entrada de la entidad aún no está activada." : "No se ha podido iniciar sesión. Inténtalo de nuevo.");
    } finally {
      setOcupado(false);
    }
  };
  return (
    <div className={`tema-asesor ${s.raiz}`}>
      <BarraEntidad sesion={estado?.logged === true} alSalir={cargar} />
      <section className={s.hero}>
        <div className={s.puntos} aria-hidden="true" />
        <div className={s.heroCaja}>
          <div className={s.heroTexto}>
            <h1>
              <span className={s.grad}>Bandeja</span>
              <br />
              de la entidad
            </h1>
            {!estado && <p>Comprobando…</p>}
            {estado && !estado.logged && (
              <form onSubmit={entrar} style={{ display: "grid", gap: 12, marginTop: 16 }}>
                <p>Entra con la clave del equipo para ver los perfiles que llegan, revisar sus evidencias y validarlos.</p>
                <label htmlFor="clave-admin" style={{ fontWeight: 600 }}>Clave de la entidad</label>
                <input id="clave-admin" type="password" autoComplete="current-password" value={clave}
                  onChange={(e) => setClave(e.target.value)} style={campo} required />
                <div className={s.accion}>
                  <button type="submit" className={s.boton} disabled={ocupado || !clave}>
                    {ocupado ? "Entrando…" : "Entrar"} <span aria-hidden="true">→</span>
                  </button>
                </div>
              </form>
            )}
            {estado?.logged && (
              <p>Cada entrevista y cada demo guiada llega aquí. Abre un perfil para revisar sus evidencias y validarlo.</p>
            )}
            {error && <p role="alert" className={s.error}>{error}</p>}
          </div>
        </div>
      </section>
      {estado?.logged && (
        <main className={s.cuerpo}>
          <Bandeja />
          <AbrirCodigo inicial={sugerido} />
        </main>
      )}
    </div>
  );
}

function Bandeja() {
  const [filas, setFilas] = useState<ClienteBandeja[] | null>(null);
  const [error, setError] = useState(false);
  const [soloPendientes, setSoloPendientes] = useState(true);
  useEffect(() => {
    let vivo = true;
    const tick = () =>
      api.bandejaEntidad()
        .then((d) => vivo && (setFilas(d.clients), setError(false)))
        .catch(() => vivo && setError(true));
    tick();
    const id = setInterval(tick, SONDEO_MS);
    return () => {
      vivo = false;
      clearInterval(id);
    };
  }, []);
  const pendientes = filas?.filter((f) => POR_VALIDAR.has(f.status)).length ?? 0;
  const visibles = (filas ?? []).filter((f) => !soloPendientes || POR_VALIDAR.has(f.status));
  return (
    <section className={s.tarj} style={{ padding: "22px 24px" }} aria-labelledby="t-bandeja">
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12, marginBottom: 10 }}>
        <h2 id="t-bandeja" style={{ margin: 0, fontSize: 20 }}>
          Perfiles recientes
        </h2>
        <span className={s.meta}>{filas ? `${pendientes} por validar · ${filas.length} en total` : "Cargando…"}</span>
        <label style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 8, fontSize: 14 }}>
          <input type="checkbox" checked={soloPendientes} onChange={(e) => setSoloPendientes(e.target.checked)} />
          Solo los que hay que validar
        </label>
      </div>
      {error && <p role="alert" className={s.error}>No se ha podido cargar la bandeja. Se reintenta sola.</p>}
      {filas && visibles.length === 0 && (
        <p className={s.meta} style={{ fontSize: 14 }}>
          {soloPendientes ? "No hay perfiles por validar ahora mismo." : "Aún no hay perfiles."} Haz una entrevista o la demo
          guiada y aparecerá aquí.
        </p>
      )}
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {visibles.map((f) => (
          <li key={f.client_id} className={s.fila}>
            <Link
              href={`/entidad/${encodeURIComponent(f.client_id)}`}
              style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "6px 14px", padding: "14px 4px", minHeight: 44 }}
            >
              <code style={{ fontWeight: 600, overflowWrap: "anywhere" }}>{f.client_id}</code>
              <span className={`${s.insignia} ${s[`ins_${f.status}`] ?? ""}`}>{ESTADOS[f.status] ?? f.status}</span>
              {(/simulad/i.test(f.reason) || f.client_id.startsWith("carmen")) && <span className={s.meta}>Datos simulados</span>}
              <span className={s.meta} style={{ marginLeft: "auto" }}>
                v{f.version} · {fecha(f.updated_at)}
              </span>
              <span aria-hidden="true">→</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

function AbrirCodigo({ inicial }: { inicial: string }) {
  const router = useRouter();
  const [cliente, setCliente] = useState(inicial);
  const [error, setError] = useState<string | null>(null);
  const abrir = (e: React.FormEvent) => {
    e.preventDefault();
    const cid = cliente.trim();
    if (!CLIENTE.test(cid)) {
      setError("El código del cliente no es válido (por ejemplo, cliente-1a2b3c… o carmen-68).");
      return;
    }
    router.push(`/entidad/${encodeURIComponent(cid)}`);
  };
  return (
    <form onSubmit={abrir} className={s.tarj} style={{ padding: "22px 24px", display: "grid", gap: 10 }}>
      <label htmlFor="cliente-admin" style={{ fontWeight: 600 }}>¿Tienes el código de un cliente?</label>
      <p className={s.meta} style={{ margin: 0, fontSize: 14 }}>Aparece al final de su página «Mi perfil».</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        <input id="cliente-admin" value={cliente} onChange={(e) => setCliente(e.target.value)}
          placeholder="cliente-1a2b3c…" style={campo} required />
        <button type="submit" className={s.boton}>
          Abrir expediente <span aria-hidden="true">→</span>
        </button>
      </div>
      {error && <p role="alert" className={s.error}>{error}</p>}
    </form>
  );
}
