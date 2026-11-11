"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import s from "../entidad/[cid]/entidad.module.css";

const CLIENTE = /^[a-z0-9][a-z0-9_-]{0,63}$/;
const campo: React.CSSProperties = {
  width: "100%", maxWidth: 420, minHeight: 48, padding: "0 16px", borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.25)", background: "rgba(255,255,255,0.08)", color: "inherit", font: "inherit",
};

/** Entrada de la entidad: clave del equipo y código del cliente que se quiere revisar y validar. */
export default function VistaAdmin() {
  const router = useRouter();
  const sugerido = useSearchParams().get("cliente") ?? "";
  const [estado, setEstado] = useState<{ enabled: boolean; logged: boolean } | null>(null);
  const [clave, setClave] = useState("");
  const [cliente, setCliente] = useState(sugerido);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api.sesionAdmin().then(setEstado).catch(() => setEstado({ enabled: false, logged: false }));
  }, []);
  useEffect(cargar, [cargar]);

  const entrar = async (e: React.FormEvent) => {
    e.preventDefault();
    setOcupado(true);
    setError(null);
    try {
      await api.entrarAdmin(clave);
      setClave("");
      cargar();
    } catch (err) {
      setError((err as { status?: number }).status === 401 ? "Clave incorrecta." : "No se ha podido iniciar sesión. Inténtalo de nuevo.");
    } finally {
      setOcupado(false);
    }
  };
  const abrir = (e: React.FormEvent) => {
    e.preventDefault();
    const cid = cliente.trim();
    if (!CLIENTE.test(cid)) {
      setError("El código del cliente no es válido (por ejemplo, cliente-1a2b3c… o carmen-68).");
      return;
    }
    router.push(`/entidad/${encodeURIComponent(cid)}`);
  };
  const salir = async () => {
    await api.salirAdmin().catch(() => undefined);
    cargar();
  };

  return (
    <div className={`tema-asesor ${s.raiz}`}>
      <header className={s.barra}>
        <div className={s.barraCaja}>
          <Link href="/" className={s.marca}>
            <span className={s.logo} aria-hidden="true" />
            Idóneo <span>para entidades</span>
          </Link>
        </div>
      </header>
      <section className={s.hero}>
        <div className={s.puntos} aria-hidden="true" />
        <div className={s.heroCaja}>
          <div className={s.heroTexto}>
            <h1>
              <span className={s.grad}>Administración</span>
              <br />
              de la entidad
            </h1>
            {!estado && <p>Comprobando…</p>}
            {estado && !estado.enabled && (
              <p role="note">La administración no está activada en este despliegue. Los perfiles se pueden consultar, pero no validar.</p>
            )}
            {estado?.enabled && !estado.logged && (
              <form onSubmit={entrar} style={{ display: "grid", gap: 12, marginTop: 16 }}>
                <p>Entra con la clave del equipo para revisar y validar perfiles como asesor.</p>
                <label htmlFor="clave-admin" style={{ fontWeight: 600 }}>Clave de administración</label>
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
              <form onSubmit={abrir} style={{ display: "grid", gap: 12, marginTop: 16 }}>
                <p>Sesión iniciada. Escribe el código del cliente: aparece en su página «Mi perfil».</p>
                <label htmlFor="cliente-admin" style={{ fontWeight: 600 }}>Código del cliente</label>
                <input id="cliente-admin" value={cliente} onChange={(e) => setCliente(e.target.value)}
                  placeholder="cliente-1a2b3c…" style={campo} required />
                <div className={s.accion}>
                  <button type="submit" className={s.boton}>
                    Abrir expediente <span aria-hidden="true">→</span>
                  </button>
                  <button type="button" className={s.enlace} onClick={salir}>Cerrar sesión</button>
                </div>
              </form>
            )}
            {error && <p role="alert" className={s.error}>{error}</p>}
          </div>
        </div>
      </section>
    </div>
  );
}
