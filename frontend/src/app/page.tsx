"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Revela } from "@/components/Revela";
import { clasesBoton, Icono, MarcaNoche, Noche } from "@/components/visual";
import { AuraPreguntas } from "./_portada/AuraPreguntas";
import { Historia } from "./_portada/Historia";
import s from "./_portada/portada.module.css";

const ENLACES = [
  ["#problema", "El problema"],
  ["#como", "Cómo funciona"],
  ["#entidad", "Para la entidad"],
  ["#probar", "Pruébalo"],
] as const;

// Portada del producto. Solo explica qué hace Idóneo; no muestra resultados de pruebas.
export default function Portada() {
  const [conFondo, setConFondo] = useState(false);
  useEffect(() => {
    const f = () => setConFondo(window.scrollY > 24);
    f();
    window.addEventListener("scroll", f, { passive: true });
    return () => window.removeEventListener("scroll", f);
  }, []);

  return (
    <Noche className={s.raiz}>
      <header className={`${s.nav} ${conFondo ? s.navFondo : ""}`}>
        <div className={s.navCaja}>
          <MarcaNoche />
          <nav className={`${s.enlaces} mono`} aria-label="Principal">
            {ENLACES.map(([h, t]) => (
              <a key={h} href={h}>
                {t}
              </a>
            ))}
          </nav>
          <Link href="/onboarding/entrevista" className={s.navBoton}>
            Empezar
          </Link>
        </div>
      </header>

      <div className={s.caja}>
        <main>
          <section className={s.hero}>
            <div>
              <span className={`${s.etiqueta} vidrio mono`}>
                <i aria-hidden="true" /> Perfil inversor MiFID II
              </span>
              <h1 className={s.titulo}>
                <span>Tu perfil inversor.</span>
                <span className="texto-degradado">En una conversación.</span>
              </h1>
              <p className={s.entrada}>
                Idóneo sustituye el test de idoneidad por una conversación. Escucha al cliente, anota cada dato con la frase que lo
                justifica y entrega a la entidad un perfil que se puede revisar, validar y auditar.
              </p>
              <div className={s.acciones}>
                <Link href="/onboarding/entrevista" className={clasesBoton.luz}>
                  {Icono.micro} Soy cliente
                </Link>
                <Link href="/admin" className={clasesBoton.luz}>
                  {Icono.check} Soy entidad
                </Link>
              </div>
              <Link href="/escenario" className={`${s.demoEnlace} mono`}>
                <span aria-hidden="true">{Icono.play}</span> O mira antes la demo guiada de Carmen, 68 años
              </Link>
              <ul className={s.claves}>
                <li>Voz o texto</li>
                <li>Una pregunta cada vez</li>
                <li>Revisado por una persona</li>
              </ul>
            </div>
            <AuraPreguntas />
          </section>

          <a href="#problema" className={`${s.bajar} mono`} aria-label="Bajar a la explicación">
            <span aria-hidden="true" />
            Desliza
          </a>

          <section id="problema" className={s.seccion}>
            <Revela className={s.seccionCab}>
              <div>
                <span className={`${s.kicker} mono`}>El problema</span>
                <h2>El test de idoneidad mide lo que el cliente cree saber.</h2>
              </div>
              <p>
                Las directrices de ESMA sobre idoneidad (2023) piden no depender indebidamente de la autoevaluación del cliente y
                advierten de que el riesgo de sobrevalorarse es mayor en procesos automatizados con poca interacción humana.
              </p>
            </Revela>
            <div className={s.compara}>
              <Revela variante="izq" className={`${s.lado} vidrio`}>
                <span className={`${s.ladoTitulo} mono`}>Hoy · test de casillas</span>
                <ul className={s.casillas}>
                  {["Conozco bien los fondos de renta variable", "Tolero pérdidas temporales", "Mi horizonte es de más de 5 años"].map(
                    (c, i) => (
                      <li key={c} style={{ animationDelay: `${0.4 + i * 0.35}s` }}>
                        <span className={s.casilla}>{Icono.check}</span>
                        {c}
                      </li>
                    ),
                  )}
                </ul>
                <p className={s.ladoPie}>Tres clics. Nadie comprueba si es verdad ni de dónde sale cada respuesta.</p>
              </Revela>
              <Revela retraso={0.15} className={`${s.lado} ${s.ladoBueno} vidrio`}>
                <span className={`${s.ladoTitulo} mono`}>Con Idóneo · una conversación</span>
                <p className={s.cita}>«Eso no puede pasar, el fondo es del banco.»</p>
                <div className={s.alertaMini}>
                  {Icono.aviso}
                  <span>
                    <strong>Declarado ≠ demostrado.</strong> Marcó que conoce la renta variable, pero cree que un fondo de su banco no
                    puede perder valor.
                  </span>
                </div>
                <p className={s.ladoPie}>La entidad ve la frase exacta, sabe qué revisar y decide con pruebas.</p>
              </Revela>
            </div>
          </section>

          <section id="como" className={s.seccion}>
            <Revela className={s.seccionCab}>
              <div>
                <span className={`${s.kicker} mono`}>Cómo funciona</span>
                <h2>De una conversación a un perfil que se puede auditar.</h2>
              </div>
              <p>Cinco pasos. La inteligencia artificial escucha y anota; las reglas calculan; una persona decide.</p>
            </Revela>
            <Historia />
          </section>

          <section id="entidad" className={s.seccion}>
            <Revela className={s.seccionCab}>
              <div>
                <span className={`${s.kicker} mono`}>Para la entidad</span>
                <h2>Un perfil listo para revisar, no un PDF que firmar.</h2>
              </div>
              <p>Pensado para que el equipo de cumplimiento y el agente de la entidad trabajen sobre el mismo perfil.</p>
            </Revela>
            <div className={s.tres}>
              <Revela como="article" className={`${s.carta} vidrio`}>
                <span className={s.cartaIcono}>{Icono.aviso}</span>
                <h3>Avisos con su prueba</h3>
                <p>Cada incoherencia llega con la frase que la provoca y el momento exacto de la conversación, listo para repreguntar.</p>
                <div className={s.fuentes}>
                  <span className={s.fDeclarado}>Declarado</span>
                  <span className={s.fDemostrado}>Demostrado</span>
                  <span className={s.fCalculado}>Calculado</span>
                  <span className={s.fAsesor}>Asesor</span>
                </div>
              </Revela>
              <Revela como="article" retraso={0.12} className={`${s.carta} vidrio`}>
                <span className={s.cartaIcono}>{Icono.check}</span>
                <h3>Un perfil que sigue vivo</h3>
                <p>
                  Si algo cambia (un sueldo, un gasto, otra idea), el cliente lo cuenta y solo se le pregunta eso. Cada cambio es una
                  versión nueva, y hasta que una persona la valida el agente sabe qué datos están en revisión.
                </p>
                <ol className={s.versiones}>
                  <li>
                    <b>v1</b> Entrevista inicial
                  </li>
                  <li>
                    <b>v2</b> Validado por la entidad
                  </li>
                  <li>
                    <b>v3</b> «Me han subido el sueldo» · 3 preguntas
                  </li>
                </ol>
              </Revela>
              <Revela como="article" retraso={0.24} className={`${s.carta} vidrio`}>
                <span className={s.cartaIcono}>{Icono.enviar}</span>
                <h3>Servido por MCP</h3>
                <p>El agente de la entidad pide las restricciones del cliente y solo recibe un perfil validado y vigente.</p>
                <code className={s.codigoMini}>get_investment_constraints</code>
              </Revela>
            </div>

            <Revela className={`${s.limite} vidrio`}>
              <div>
                <span className={`${s.kicker} mono`}>Qué no hace</span>
                <h3>No recomienda productos.</h3>
              </div>
              <p>
                Idóneo solo construye el perfil. Qué ofrecer al cliente lo decide la entidad, con su catálogo y sus agentes, dentro de
                los límites de un perfil ya validado.
              </p>
            </Revela>
          </section>

          <section id="probar" className={s.seccion}>
            <Revela className={s.seccionCab}>
              <div>
                <span className={`${s.kicker} mono`}>Pruébalo</span>
                <h2>Dos puertas y una demo.</h2>
              </div>
            </Revela>
            <div className={s.tres}>
              {[
                { h: "/onboarding/entrevista", t: "Como cliente", p: "Haz tu entrevista, por voz o escribiendo. Al acabar ves tu perfil y lo actualizas cuando algo cambie.", i: Icono.micro },
                { h: "/escenario", t: "La demo guiada", p: "Carmen, 68 años: la entrevista y lo que recibe la entidad, a la vez. Acaba en el mismo perfil que la tuya.", i: Icono.play },
                { h: "/admin", t: "Como entidad", p: "Entra con la clave, abre la bandeja, revisa evidencias y avisos y valida cada perfil.", i: Icono.check },
              ].map((c, n) => (
                <Revela key={c.h} retraso={n * 0.12}>
                  <Link href={c.h} className={`${s.carta} ${s.cartaEnlace} vidrio`}>
                    <span className={s.cartaIcono}>{c.i}</span>
                    <h3>{c.t}</h3>
                    <p>{c.p}</p>
                    <span className={`${s.ir} mono`}>Abrir →</span>
                  </Link>
                </Revela>
              ))}
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
