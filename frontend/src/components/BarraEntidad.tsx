"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import s from "@/app/entidad/[cid]/entidad.module.css";

export type Acceso = "comprobando" | "dentro" | "fuera";

/**
 * ¿Puede esta pestaña usar las pantallas de la entidad? Sí con la sesión de la entidad (clave en /admin) o con
 * el modo asesor de demostración en local cuando no hay clave configurada. Si no, `redirigir` lleva a /admin para meter la clave y volver aquí.
 */
export function useAccesoEntidad(redirigir = true): { acceso: Acceso; admin: boolean } {
  const [estado, setEstado] = useState<{ acceso: Acceso; admin: boolean }>({ acceso: "comprobando", admin: false });
  const router = useRouter();
  const ruta = usePathname();
  useEffect(() => {
    let vivo = true;
    // Con la entrada de la entidad configurada, siempre hace falta su clave. Sin ella (p. ej., el pitch en
    // local solo con el modo asesor de demostración), basta con ese modo.
    Promise.all([api.sesionAdmin(), api.modoAsesor().catch(() => ({ enabled: false }))])
      .then(([a, m]) => vivo && setEstado({ acceso: a.logged || (!a.enabled && m.enabled) ? "dentro" : "fuera", admin: a.logged }))
      .catch(() => vivo && setEstado({ acceso: "fuera", admin: false }));
    return () => {
      vivo = false;
    };
  }, []);
  useEffect(() => {
    if (redirigir && estado.acceso === "fuera") router.replace(`/admin?volver=${encodeURIComponent(ruta)}`);
  }, [redirigir, estado.acceso, ruta, router]);
  return estado;
}

/** Barra de la entidad: solo sus dos pantallas (perfiles y calidad) y cerrar sesión. Nada del cliente. */
export function BarraEntidad({ sesion, alSalir }: { sesion: boolean; alSalir?: () => void }) {
  const ruta = usePathname();
  const router = useRouter();
  const salir = async () => {
    await api.salirAdmin().catch(() => undefined);
    if (alSalir) alSalir();
    else router.push("/admin");
  };
  const perfiles = ruta === "/admin" || ruta.startsWith("/entidad/");
  return (
    <header className={s.barra}>
      <div className={s.barraCaja}>
        <Link href="/admin" className={s.marca}>
          <span className={s.logo} aria-hidden="true" />
          Idóneo <span>para entidades</span>
        </Link>
        {sesion && (
          <nav className={s.nav} aria-label="Navegación de la entidad">
            <Link href="/admin" aria-current={perfiles ? "page" : undefined}>Perfiles</Link>
            <Link href="/operaciones" aria-current={ruta === "/operaciones" ? "page" : undefined}>Calidad y costes</Link>
            <button type="button" className={s.enlace} style={{ minHeight: 0, color: "inherit" }} onClick={salir}>
              Cerrar sesión
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
