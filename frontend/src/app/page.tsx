/* eslint-disable @next/next/no-img-element -- SVG de marca estático: no necesita el optimizador de imágenes. */
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { Revela } from "@/components/Revela";
import s from "./_portada/landing.module.css";
import { Video } from "./_portada/Video";

const ENLACES = [
  ["#problema", "El problema"],
  ["#como", "Cómo funciona"],
  ["#integracion", "Integración"],
  ["#pruebas", "Pruebas"],
] as const;

const PASOS = [
  { n: "1", t: "Habla", p: "El cliente contesta por voz o por escrito, desde el móvil, con sus palabras.", f: "Una conversación, no un formulario." },
  { n: "2", t: "Comprueba", p: "idóneo plantea escenarios y contrasta lo que dice con lo que demuestra: declaró «alto», demostró «ninguno».", f: "Lo que dice frente a lo que demuestra." },
  { n: "3", t: "Deja pruebas", p: "Cada dato queda con su frase exacta, su fuente y su minuto. Los números los calcula código, no la IA.", f: "Cada dato, con su prueba." },
  { n: "✓", t: "Valida una persona", p: "El asesor recibe el perfil hecho y solo interviene si hay dudas. Hasta que lo valida, el agente no puede usarlo.", f: "La IA prepara; la persona decide." },
] as const;

const CIFRAS = [
  { v: "31 de 31", t: "datos acertados por el extractor", l: "En siete entrevistas simuladas." },
  { v: "10 de 10", t: "datos de Carmen, y detectó la contradicción", l: "Con Carmen simulada." },
  { v: "1,8 s", t: "tarda el asistente en responder", l: "Mediana, en la prueba por escrito." },
  { v: "Voz", t: "probada de punta a punta", l: "De la llamada al perfil, en nuestras pruebas." },
] as const;

function Sello() {
  return <img src="/marca/powered-by-idoneo-claro.svg" alt="Powered by idóneo" className={s.sello} width={93} height={17} />;
}

/** Mini pantalla de la app de la entidad: sus colores, y el sello de idóneo al pie. */
function Movil({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div className={s.movil} role="img" aria-label={`Ejemplo dentro de la app de la entidad: ${titulo}`}>
      <div className={s.movilPantalla} aria-hidden="true">
        <div className={s.movilBarra}>
          <span>Tu entidad</span>
          <i />
        </div>
        <div className={s.movilCuerpo}>
          <span className={s.movilTitulo}>{titulo}</span>
          {children}
        </div>
        <div className={s.movilPie}>
          <Sello />
        </div>
      </div>
    </div>
  );
}

// Portada de idóneo: explica el producto y deja probarlo. Los textos salen del mensaje único del producto.
export default function Portada() {
  return (
    <div className={s.raiz}>
      <header className={s.nav}>
        <div className={s.navCaja}>
          <Link href="/" aria-label="idóneo, inicio">
            <Logo variante="oscuro" alto={26} />
          </Link>
          <nav className={s.enlaces} aria-label="Principal">
            {ENLACES.map(([h, t]) => (
              <a key={h} href={h}>
                {t}
              </a>
            ))}
          </nav>
          <div className={s.navAcciones}>
            <Link href="/admin" className={s.navEntidad}>
              Acceso entidad
            </Link>
            <Link href="/onboarding/entrevista" className={s.navBoton}>
              Pruébalo
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className={s.hero}>
          <div className={s.caja}>
            <div className={s.heroTexto}>
              <span className={s.etiqueta}>
                <i aria-hidden="true" /> Perfil inversor MiFID II · dentro de la app de tu entidad
              </span>
              <h1 className={s.titulo}>
                Perfiles vivos <span className={s.degradado}>que cumplen la norma.</span>
              </h1>
              <p className={s.subtitulo}>Del cuestionario a la conversación.</p>
              <p className={s.entrada}>
                idóneo convierte el test de perfil inversor en una conversación: entiende de verdad al cliente, comprueba lo que
                dice y le entrega al asesor un perfil listo para validar.
              </p>
              <div className={s.acciones}>
                <Link href="/escenario" className={s.botonPrincipal}>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
                    <path d="M8 5.5v13l11-6.5z" />
                  </svg>
                  Mira cómo funciona
                </Link>
                <Link href="/onboarding/entrevista" className={s.botonSecundario}>
                  Pruébalo
                </Link>
              </div>
              <ul className={s.claves}>
                <li>Voz o texto</li>
                <li>Cada dato, con su prueba</li>
                <li>Lo valida siempre una persona</li>
              </ul>
            </div>
            <Video />
          </div>
        </section>

        <section id="problema" className={s.seccion}>
          <div className={s.caja}>
            <Revela className={s.cab}>
              <span className={s.kicker}>El problema</span>
              <h2>El test se fía de lo que el cliente declara.</h2>
              <p>
                Carmen tiene 68 años y 80.000 € en depósitos. En el test de su banco marcó que conoce bien los fondos de renta
                variable. Pero cuando le preguntan si uno podría perder dinero, responde otra cosa.
              </p>
            </Revela>
            <div className={s.compara}>
              <Revela variante="izq" className={s.lado}>
                <span className={s.ladoTitulo}>Hoy · test de casillas</span>
                <ul className={s.casillas}>
                  {["Conozco bien los fondos de renta variable", "Tolero pérdidas temporales", "Mi horizonte es de más de 5 años"].map((c) => (
                    <li key={c}>
                      <span className={s.casilla} aria-hidden="true">
                        ✓
                      </span>
                      {c}
                    </li>
                  ))}
                </ul>
                <p className={s.ladoPie}>Tres clics. Nadie comprueba si es verdad.</p>
              </Revela>
              <Revela retraso={0.15} className={`${s.lado} ${s.ladoBueno}`}>
                <span className={s.ladoTitulo}>Con idóneo · una conversación</span>
                <p className={s.cita}>«Eso no puede pasar, el fondo es del banco.»</p>
                <div className={s.contraste}>
                  <span>
                    <b>Declarado</b> conoce la renta variable
                  </span>
                  <span className={s.contrasteAviso}>
                    <b>Demostrado</b> cree que no puede perder
                  </span>
                </div>
                <p className={s.ladoPie}>Marcó una cosa y demostró la contraria. El test no lo detecta; la conversación, sí.</p>
              </Revela>
            </div>
            <p className={s.nota}>Carmen es un caso simulado.</p>
          </div>
        </section>

        <section id="como" className={`${s.seccion} ${s.clara}`}>
          <div className={s.caja}>
            <Revela className={s.cab}>
              <span className={s.kicker}>Cómo funciona</span>
              <h2>Tres pasos y una firma.</h2>
              <p>La inteligencia artificial escucha y anota. El código calcula. Una persona decide.</p>
            </Revela>
            <ol className={s.pasos}>
              {PASOS.map((p, i) => (
                <Revela como="li" key={p.t} retraso={i * 0.1} className={`${s.paso} ${p.n === "✓" ? s.pasoFirma : ""}`}>
                  <span className={s.pasoNum} aria-hidden="true">
                    {p.n}
                  </span>
                  <h3>{p.t}</h3>
                  <p>{p.p}</p>
                  <span className={s.pasoFrase}>«{p.f}»</span>
                </Revela>
              ))}
            </ol>
          </div>
        </section>

        <section id="integracion" className={`${s.seccion} ${s.clara} ${s.pegada}`}>
          <div className={s.caja}>
            <Revela className={s.cab}>
              <span className={s.kicker}>Integración</span>
              <h2>No es una app. Es una función dentro de la app de tu entidad.</h2>
              <p>
                El cliente ve su banco, con sus colores y su tipografía. idóneo firma en pequeño, al pie, y aparece en tres
                momentos.
              </p>
            </Revela>
            <div className={s.momentos}>
              <Revela como="article" className={s.momento}>
                <Movil titulo="Tu perfil inversor">
                  <span className={s.burbuja}>Cuéntame, ¿para qué quieres invertir?</span>
                  <span className={`${s.burbuja} ${s.burbujaMia}`}>Para complementar la pensión.</span>
                  <span className={s.ondas}>
                    <i /><i /><i /><i /><i />
                  </span>
                  <span className={s.movilFrase}>Invertir empieza por escucharte.</span>
                </Movil>
                <span className={s.momentoNum}>1 · El momento principal</span>
                <h3>Alta del cliente</h3>
                <p>En lugar del test, una conversación que crea un perfil real: qué sabe, cuánto puede perder y qué busca.</p>
              </Revela>
              <Revela como="article" retraso={0.12} className={s.momento}>
                <Movil titulo="¿Ha cambiado algo?">
                  <span className={`${s.burbuja} ${s.burbujaMia}`}>Me han subido el sueldo.</span>
                  <span className={s.burbuja}>Solo te pregunto por eso: 3 preguntas.</span>
                  <span className={s.movilChip}>El resto de tu perfil sigue igual</span>
                </Movil>
                <span className={s.momentoNum}>2 · Cuando algo cambia</span>
                <h3>Microentrevistas</h3>
                <p>Antes de una compra o cuando cambia su vida. Se pregunta solo lo que ha cambiado.</p>
              </Revela>
              <Revela como="article" retraso={0.24} className={s.momento}>
                <Movil titulo="Tu perfil, al día">
                  <ol className={s.versiones}>
                    <li>
                      <b>v1</b> Entrevista inicial
                    </li>
                    <li>
                      <b>v2</b> Validado por una persona
                    </li>
                    <li>
                      <b>v3</b> Cambio de sueldo
                    </li>
                  </ol>
                </Movil>
                <span className={s.momentoNum}>3 · Siempre</span>
                <h3>Perfil vivo</h3>
                <p>La entidad queda al día de lo que el cliente cuenta en cada conversación, sin volver a empezar de cero.</p>
              </Revela>
            </div>
            <ul className={s.integra}>
              <li>
                <strong>Con la marca de la entidad</strong>
                Sus colores y su tipografía. Nuestro sello, al pie del módulo: <Sello />
              </li>
              <li>
                <strong>Con sus agentes de IA</strong>
                El agente de la entidad consulta el perfil por MCP y solo recibe uno validado y vigente.
              </li>
              <li>
                <strong>No recomienda productos</strong>
                Recomienda el agente o el asesor de la entidad. idóneo se ocupa de que sepan a quién recomiendan.
              </li>
            </ul>
          </div>
        </section>

        <section id="asesor" className={s.seccion}>
          <div className={`${s.caja} ${s.dos}`}>
            <Revela className={s.cab}>
              <span className={s.kicker}>Para el asesor</span>
              <h2>Te lo damos hecho; tú validas.</h2>
              <p>
                El asesor recibe el perfil hecho y comprobado, conoce al cliente de forma personal sin una entrevista larga y
                solo interviene ante dudas.
              </p>
              <ul className={s.lista}>
                <li>Cada dato llega con la frase exacta que lo justifica.</li>
                <li>En las entrevistas por voz, puede escuchar ese fragmento de la llamada.</li>
                <li>Hasta que una persona valida, el agente de la entidad no puede usar el perfil.</li>
              </ul>
              <p className={s.frase}>La IA prepara; la persona decide.</p>
            </Revela>
            <Revela variante="zoom" retraso={0.1} className={s.expediente}>
              <div aria-hidden="true">
                <div className={s.expCab}>
                  <span>Carmen · perfil por validar</span>
                  <span className={s.estadoRevisar}>Revisar</span>
                </div>
                <div className={s.expDato}>
                  <span className={s.expNombre}>Conocimiento · renta variable</span>
                  <div className={s.chips}>
                    <span className={s.chip}>Declarado: alto</span>
                    <span className={`${s.chip} ${s.chipAviso}`}>Demostrado: ninguno</span>
                  </div>
                  <div className={s.expCita}>
                    <span className={s.expPlay}>
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M8 5.5v13l11-6.5z" />
                      </svg>
                    </span>
                    <span>«Eso no puede pasar, el fondo es del banco.»</span>
                  </div>
                </div>
                <div className={s.expDato}>
                  <span className={s.expNombre}>Riesgo máximo</span>
                  <div className={s.chips}>
                    <span className={s.chip}>Calculado por código</span>
                  </div>
                </div>
                <div className={s.expPie}>
                  <span className={s.expBoton}>Validar perfil</span>
                  <span>Ejemplo ilustrativo · caso simulado</span>
                </div>
              </div>
            </Revela>
          </div>
        </section>

        <section id="pruebas" className={`${s.seccion} ${s.clara}`}>
          <div className={s.caja}>
            <Revela className={s.cab}>
              <span className={s.kicker}>Pruebas</span>
              <h2>Lo que hemos medido, con su límite.</h2>
            </Revela>
            <dl className={s.cifras}>
              {CIFRAS.map((c, i) => (
                <Revela key={c.v} retraso={i * 0.08} className={s.cifra}>
                  <dt>{c.v}</dt>
                  <dd>
                    {c.t}
                    <small>{c.l}</small>
                  </dd>
                </Revela>
              ))}
            </dl>
            <p className={s.limite}>
              <strong>Límite de estas cifras:</strong> clientes simulados, una sola repetición y casos escritos por el equipo. El
              perfil recoge y documenta lo que MiFID exige, cada dato con su prueba, y lo valida una persona; la responsabilidad
              sigue siendo de la entidad.
            </p>
          </div>
        </section>

        <section id="probar" className={s.seccion}>
          <div className={s.caja}>
            <Revela className={s.cab}>
              <span className={s.kicker}>Pruébalo</span>
              <h2>Dos formas de verlo en marcha.</h2>
            </Revela>
            <div className={s.puertas}>
              <Revela>
                <Link href="/escenario" className={`${s.puerta} ${s.puertaPrincipal}`}>
                  <span className={s.puertaEti}>Sin IA · siempre disponible</span>
                  <h3>Mira cómo funciona</h3>
                  <p>La demo guiada de Carmen: su entrevista en el móvil y, al lado, el perfil que recibe la entidad.</p>
                  <span className={s.ir}>Ver la demo guiada →</span>
                </Link>
              </Revela>
              <Revela retraso={0.12}>
                <Link href="/onboarding/entrevista" className={s.puerta}>
                  <span className={s.puertaEti}>Con IA · cupo diario de pruebas</span>
                  <h3>Pruébalo tú</h3>
                  <p>Haz tu propia entrevista, por voz o escribiendo, y mira el perfil que resulta.</p>
                  <span className={s.ir}>Hacer mi entrevista →</span>
                </Link>
              </Revela>
            </div>
            <p className={s.nota}>
              Prototipo con datos simulados: no introduzcas datos reales. El número de entrevistas con IA está limitado cada día;
              la demo guiada no tiene límite. ¿Eres de la entidad?{" "}
              <Link href="/admin" className={s.enlace}>
                Entra con tu clave
              </Link>
              .
            </p>
          </div>
        </section>
      </main>

      <footer className={s.pie}>
        <div className={s.caja}>
          <div className={s.lema}>
            <Logo variante="oscuro" alto={40} />
            <p>
              Del cuestionario a la conversación.
              <br />
              <span className={s.degradado}>Perfiles vivos que cumplen la norma.</span>
            </p>
          </div>
          <div className={s.pieLinea}>
            <span>idóneo · prototipo · datos simulados</span>
            <span>Hack Finance UC3M 2026</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
