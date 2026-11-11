import Link from "next/link";
import s from "./landing.module.css";
import { VIDEO } from "./configVideo";

/** Hueco del vídeo del hero: archivo propio, vídeo incrustado o, mientras no lo haya, un cartel hacia la demo guiada. */
export function Video() {
  if (VIDEO.mp4) {
    return (
      <div className={s.video}>
        <video controls preload="metadata" playsInline poster={VIDEO.poster ?? undefined} aria-label="Vídeo de presentación de idóneo">
          <source src={VIDEO.mp4} type="video/mp4" />
        </video>
      </div>
    );
  }
  if (VIDEO.embed) {
    return (
      <div className={s.video}>
        <iframe
          src={VIDEO.embed}
          title="Vídeo de presentación de idóneo"
          loading="lazy"
          allow="accelerometer; encrypted-media; picture-in-picture; fullscreen"
          allowFullScreen
        />
      </div>
    );
  }
  return (
    <Link href="/escenario" className={`${s.video} ${s.cartel}`} aria-label="Ver la demo guiada de Carmen">
      <span className={s.cartelOndas} aria-hidden="true">
        {[0.35, 0.6, 1, 0.75, 0.45, 0.85, 0.55, 0.3].map((h, i) => (
          <i key={i} style={{ height: `${h * 100}%`, animationDelay: `${i * 0.12}s` }} />
        ))}
      </span>
      <span className={s.cartelPlay} aria-hidden="true">
        <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
          <path d="M8 5.5v13l11-6.5z" />
        </svg>
      </span>
      <span className={s.cartelTexto}>
        <strong>Mira la demo guiada</strong>
        <span>Carmen, 68 años · caso simulado · 2 minutos</span>
      </span>
    </Link>
  );
}
