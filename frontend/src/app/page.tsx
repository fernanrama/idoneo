"use client";

import Link from "next/link";
import { clasesBoton, Icono, MarcaNoche, Noche } from "@/components/visual";
import { AuraPreguntas } from "./_portada/AuraPreguntas";
import s from "./_portada/portada.module.css";

const CLIENTE_DEMO = "carmen-68";

const PASOS = [
  {
    n: "01",
    titulo: "Conversa",
    texto: "El cliente habla o escribe con sus palabras. Una sola pregunta en pantalla, sin casillas ni jerga.",
    icono: Icono.micro,
  },
  {
    n: "02",
    titulo: "Verifica",
    texto: "Cada dato se guarda con la frase exacta que lo justifica. Si lo declarado no cuadra con lo demostrado, salta un aviso.",
    icono: Icono.aviso,
  },
  {
    n: "03",
    titulo: "Valida y entrega",
    texto: "Una persona de la entidad revisa y firma. El perfil queda versionado y listo para su agente vía MCP.",
    icono: Icono.check,
  },
];

// Portada del producto. Solo cuenta qué hace Idóneo; no muestra resultados de pruebas.
export default function Portada() {
  return (
    <Noche className={s.raiz}>
      <div className={s.caja}>
        <header className={s.nav}>
          <MarcaNoche />
          <nav className={`${s.enlaces} mono`} aria-label="Principal">
            <a href="#como">Cómo funciona</a>
            <a href="#limites">Qué no hace</a>
            <a href="#agentes">Para agentes</a>
            <Link href={`/entidad/${CLIENTE_DEMO}`}>Vista de la entidad</Link>
          </nav>
        </header>

        <main>
          <section className={s.hero}>
            <div>
              <span className={`${s.etiqueta} vidrio mono`}>
                <i aria-hidden="true" /> Perfil MiFID II conversacional
              </span>
              <h1 className={s.titulo}>
                <span>Tu perfil inversor.</span>
                <span className="texto-degradado">En una conversación.</span>
              </h1>
              <p className={s.entrada}>
                Idóneo sustituye el test de idoneidad por una charla. Escucha, anota cada dato con su frase y entrega a la
                entidad un perfil verificable, listo para validar.
              </p>
              <div className={s.acciones}>
                <Link href="/onboarding/entrevista" className={clasesBoton.luz}>
                  {Icono.micro} Empezar a hablar
                </Link>
                <Link href="/escenario" className={clasesBoton.vidrio}>
                  Ver la demo guiada →
                </Link>
              </div>
              <div className={`${s.hecho} mono`}>
                <span>Hecho con</span>
                <span className="vidrio">Voz</span>
                <span className="vidrio">Agentes de IA</span>
                <span className="vidrio">Reglas fijas</span>
                <span className="vidrio">MCP</span>
              </div>
            </div>
            <AuraPreguntas />
          </section>

          <section id="como" className={s.seccion}>
            <div className={s.seccionCab}>
              <div>
                <span className={`${s.kicker} mono`}>Cómo funciona</span>
                <h2>De una conversación a un perfil que se puede auditar.</h2>
              </div>
              <p>Los números del perfil salen de reglas fijas, nunca del modelo. La IA escucha y anota; las reglas calculan.</p>
            </div>
            <div className={s.tres}>
              {PASOS.map((p) => (
                <article key={p.n} className={`${s.carta} vidrio`}>
                  <span className={s.cartaIcono}>{p.icono}</span>
                  <span className={`${s.num} mono`}>{p.n}</span>
                  <h3>{p.titulo}</h3>
                  <p>{p.texto}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="limites" className={s.seccion}>
            <div className={s.dos}>
              <div className={`${s.panelNo} vidrio`}>
                <span className={`${s.kicker} mono`}>Qué no hace</span>
                <h3>No recomendamos productos.</h3>
                <p>
                  Idóneo solo construye el perfil. Qué ofrecer al cliente lo decide la entidad, con su catálogo y sus agentes, a
                  partir de un perfil que ya está validado.
                </p>
                <ul className={s.lista}>
                  <li>Cada dato con su fuente: declarado, demostrado, calculado o del asesor.</li>
                  <li>Avisos cuando lo que dice el cliente no encaja con lo que ha hecho.</li>
                  <li>Siempre revisado por una persona antes de usarse.</li>
                </ul>
              </div>
              <div id="agentes" className={`${s.panelNo} vidrio`}>
                <span className={`${s.kicker} mono`}>Para agentes</span>
                <h3>El perfil, servido por MCP.</h3>
                <p>El agente de la entidad pide las restricciones del cliente y solo recibe un perfil validado y vigente.</p>
                <pre className={s.codigo}>
                  <em>{"// get_investment_constraints"}</em>
                  {"\n{\n  "}
                  <b>&quot;usable&quot;</b>
                  {": true,\n  "}
                  <b>&quot;funds_query&quot;</b>
                  {': { "max_risk": 3, "currency": "EUR" },\n  '}
                  <b>&quot;portfolios_query&quot;</b>
                  {': { "profile": "MODERADO" },\n  '}
                  <b>&quot;appropriateness&quot;</b>
                  {': { "equity_funds": "not_appropriate" }\n}'}
                </pre>
                <span className="mono" style={{ fontSize: 11, color: "var(--n-tenue)" }}>
                  Ejemplo ilustrativo
                </span>
                <Link href={`/entidad/${CLIENTE_DEMO}`} className={`${s.enlace} mono`}>
                  Abrir la vista de la entidad →
                </Link>
              </div>
            </div>
          </section>
        </main>

        <footer className={`${s.pie} mono`}>
          <span>Idóneo · prototipo · datos simulados</span>
          <span>Hack Finance UC3M</span>
        </footer>
      </div>
    </Noche>
  );
}
