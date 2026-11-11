// Presentación de idóneo (Hack Finance UC3M 2026). Versión 5 (11/11): marca «Aurora» y papel TÉCNICO.
//
// El pitch abre con el vídeo (problema, solución y cómo funciona). Estas diapositivas van DESPUÉS y cuentan lo
// que el vídeo no puede: cómo está hecho por dentro, por qué es fiable y cómo se integra.
//
// Uso:  node build.js salida.pptx [--final]
//   - Sin --final: las notas incluyen avisos «(Pendiente: …)» para el equipo. Con --final, no.
//
// Regla de diseño: cada diapositiva lleva su mensaje (título), el dibujo y SOLO los rótulos necesarios.
// Lo que se dice va en las NOTAS DEL ORADOR. Nada de pies de página, números ni párrafos.
//
// Marca (docs/marca/README.md): fondo noche, degradado menta → turquesa, tipografía Sora (instalada en el
// portátil que proyecta; en otro equipo, exportar a PDF antes). Verde, ámbar y rojo, solo para estados.
// Sin logos de terceros.

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const fa = require("react-icons/fa");

const ASSETS = __dirname + "/assets";
const MARCA = path.resolve(__dirname, "../../docs/marca");
const OUT = process.argv[2] || "../Idoneo_presentacion.pptx";
const FINAL = process.argv.includes("--final");
const nota = (t) => (FINAL ? "" : t);

// Nombre del equipo: solo se dice en voz alta, no sale escrito.
const EQUIPO = "Real Betis";

// ---------- Marca ----------
const K = {
  noche: "0C1A1F", noche2: "103038", tinta: "F7FBFA", suave: "B4C6CB", tenue: "7E9399",
  menta: "7CE7C4", turquesa: "2BB3C0", vidrio: "FFFFFF",
  verde: "1F9D6B", ambar: "D99A1E", rojo: "D64545",
};
const F = { tit: "Sora SemiBold", txt: "Sora", fina: "Sora Light", mono: "Consolas" };

// ---------- Imágenes generadas ----------
const png64 = (buf) => "image/png;base64," + buf.toString("base64");

async function fondo(brillos) {
  const W = 1920, H = 1080;
  const g = brillos.map((b, i) => `<radialGradient id="b${i}" cx="${b.x}" cy="${b.y}" r="${b.r}" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#${b.c}" stop-opacity="${b.o}"/><stop offset="1" stop-color="#${b.c}" stop-opacity="0"/></radialGradient>`).join("");
  const r = brillos.map((_, i) => `<rect width="${W}" height="${H}" fill="url(#b${i})"/>`).join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><defs><linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#${K.noche}"/><stop offset="1" stop-color="#${K.noche2}"/></linearGradient>${g}</defs><rect width="${W}" height="${H}" fill="url(#f)"/>${r}</svg>`;
  return png64(await sharp(Buffer.from(svg)).png().toBuffer());
}
async function icono(Icon, hex, tam = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: String(tam) }));
  return png64(await sharp(Buffer.from(svg)).png().toBuffer());
}
// Baldosa: icono oscuro sobre un cuadrado redondeado con el degradado Aurora
async function baldosa(Icon) {
  const inner = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + K.noche, size: "120" }));
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#${K.menta}"/><stop offset="1" stop-color="#${K.turquesa}"/></linearGradient></defs><rect width="256" height="256" rx="64" fill="url(#d)"/><g transform="translate(68 68)">${inner}</g></svg>`;
  return png64(await sharp(Buffer.from(svg)).png().toBuffer());
}
async function redondear(ruta, radio) {
  const img = sharp(ruta); const { width: w, height: h } = await img.metadata();
  const mask = Buffer.from(`<svg width="${w}" height="${h}"><rect width="${w}" height="${h}" rx="${radio}" fill="#fff"/></svg>`);
  return png64(await img.composite([{ input: mask, blend: "dest-in" }]).png().toBuffer());
}
const leePng = (f) => png64(fs.readFileSync(path.join(MARCA, f)));

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
  pres.theme = { headFontFace: F.tit, bodyFontFace: F.txt };
  pres.title = "idóneo · Hack Finance UC3M 2026";
  pres.author = "Equipo Hack Finance UC3M";
  const SH = pres.ShapeType;
  pres.defineSlideMaster({ title: "NOCHE", background: { color: K.noche }, objects: [] });
  const nueva = (bg) => { const s = pres.addSlide({ masterName: "NOCHE" }); s.background = { data: bg }; return s; };

  // ---------- Recursos ----------
  const BG = {
    portada: await fondo([{ x: 0.78, y: 0.4, r: 0.45, c: K.menta, o: 0.22 }, { x: 0.1, y: 1.0, r: 0.4, c: K.turquesa, o: 0.18 }]),
    a: await fondo([{ x: 0.0, y: 0.0, r: 0.4, c: K.turquesa, o: 0.16 }, { x: 1.0, y: 1.0, r: 0.42, c: K.menta, o: 0.12 }]),
    b: await fondo([{ x: 0.85, y: 0.3, r: 0.42, c: K.menta, o: 0.14 }, { x: 0.1, y: 1.05, r: 0.35, c: K.turquesa, o: 0.14 }]),
    centro: await fondo([{ x: 0.5, y: 0.45, r: 0.5, c: K.turquesa, o: 0.2 }, { x: 0.5, y: 1.1, r: 0.4, c: K.menta, o: 0.12 }]),
  };
  const LOGO = leePng("idoneo-logo-sobre-oscuro.png"); // 2000 x 635
  const SELLO = leePng("powered-by-idoneo-claro.png"); // 1200 x 219
  const ICONO = leePng("idoneo-icono-app-512.png");
  const CAP = { entidad: await redondear(ASSETS + "/entidad_carmen.jpg", 18) };
  const B = {
    mic: await baldosa(fa.FaMicrophone), brain: await baldosa(fa.FaBrain), cita: await baldosa(fa.FaQuoteRight),
    calc: await baldosa(fa.FaCalculator), user: await baldosa(fa.FaUserCheck), robot: await baldosa(fa.FaRobot),
    alta: await baldosa(fa.FaUserPlus), cambio: await baldosa(fa.FaSyncAlt), vivo: await baldosa(fa.FaWaveSquare),
  };
  const IC = {
    flecha: await icono(fa.FaArrowRight, K.tenue), abajo: await icono(fa.FaArrowDown, K.tenue),
    ok: await icono(fa.FaCheckCircle, K.verde), no: await icono(fa.FaTimesCircle, K.rojo), aviso: await icono(fa.FaExclamationTriangle, K.ambar),
    escudo: await icono(fa.FaShieldAlt, K.turquesa), play: await icono(fa.FaPlay, K.noche),
  };

  // ---------- Ayudas de dibujo ----------
  const texto = (s, t, o) => s.addText(t, Object.assign({ margin: 0, isTextBox: true, fontFace: F.txt, color: K.tinta }, o));
  const titulo = (s, t, o) => texto(s, t, Object.assign({ x: 0.6, y: 0.4, w: 8.8, h: 0.7, fontFace: F.tit, fontSize: 26, valign: "middle", objectName: "Título" }, o));
  const sub = (s, t, o) => texto(s, t, Object.assign({ x: 0.6, y: 1.05, w: 8.8, h: 0.4, fontSize: 14, color: K.suave, valign: "middle", objectName: "Subtítulo" }, o));
  const vidrio = (s, x, y, w, h, nombre, borde) => s.addShape(SH.roundRect, {
    x, y, w, h, rectRadius: 0.12, fill: { color: K.vidrio, transparency: 94 },
    line: { color: borde || K.vidrio, transparency: borde ? 30 : 86, width: 1 }, objectName: nombre,
  });
  const pastilla = (s, t, x, y, w, color) => {
    s.addShape(SH.roundRect, { x, y, w, h: 0.34, rectRadius: 0.17, fill: { color }, line: { color, width: 0 }, objectName: "Pastilla: " + t });
    texto(s, t, { x, y, w, h: 0.34, fontFace: F.tit, fontSize: 11, color: "FFFFFF", align: "center", valign: "middle" });
  };
  const img = (s, data, x, y, w, h, nombre) => s.addImage({ data, x, y, w, h, objectName: nombre });

  // ===== 1 · Portada =====
  let s = nueva(BG.portada);
  img(s, LOGO, 0.75, 1.35, 4.6, 4.6 * 635 / 2000, "Logotipo idóneo");
  texto(s, "Invertir empieza por escucharte.", { x: 0.75, y: 3.1, w: 7.5, h: 0.6, fontFace: F.tit, fontSize: 28, valign: "middle", objectName: "Lema" });
  texto(s, "Tu perfil inversor, en una conversación.", { x: 0.75, y: 3.7, w: 7.5, h: 0.45, fontFace: F.fina, fontSize: 18, color: K.suave, valign: "middle", objectName: "Subtítulo" });
  s.addNotes(`Somos ${EQUIPO}. Acabáis de ver idóneo desde fuera; ahora, por dentro.` +
    nota("\n(Pendiente: decidir quién presenta esta parte.)"));

  // ===== 2 · Cómo funciona por dentro =====
  s = nueva(BG.a);
  titulo(s, "Cómo funciona por dentro");
  sub(s, "FastAPI orquesta piezas pequeñas con contratos tipados.");
  const pasos = [
    [B.mic, "Conversación", "Voz (ElevenLabs) o texto. Claude conduce la entrevista."],
    [B.brain, "Extractor", "Claude propone cada dato con su cita literal."],
    [B.cita, "Guardas y rúbrica", "El código comprueba la cita y el contexto, y decide."],
    [B.calc, "Perfil con pruebas", "Riesgo e idoneidad: reglas fijas en Python."],
    [B.user, "Validación humana", "Sin ella, el perfil no sale."],
    [B.robot, "Agente de la entidad", "Lo lee por API o MCP y recomienda."],
  ];
  const xw = 1.42, x0 = 0.55, gap = 0.13;
  pasos.forEach(([b, h, d], i) => {
    const x = x0 + i * (xw + gap);
    vidrio(s, x, 1.75, xw, 2.75, "Paso: " + h, i === 4 ? K.menta : null);
    img(s, b, x + xw / 2 - 0.32, 1.98, 0.64, 0.64, "Icono: " + h);
    texto(s, h, { x: x + 0.08, y: 2.78, w: xw - 0.16, h: 0.55, fontFace: F.tit, fontSize: 11.5, align: "center", valign: "middle" });
    texto(s, d, { x: x + 0.1, y: 3.33, w: xw - 0.2, h: 1.05, fontSize: 10.5, color: K.suave, align: "center", valign: "top" });
    if (i < pasos.length - 1) img(s, IC.flecha, x + xw + 0.005, 3.0, 0.12, 0.12, "Flecha");
  });
  texto(s, [{ text: "La IA entiende y propone. ", options: { color: K.tinta, fontFace: F.tit } }, { text: "El código decide y calcula. ", options: { color: K.menta, fontFace: F.tit } }, { text: "Una persona valida.", options: { color: K.tinta, fontFace: F.tit } }],
    { x: 0.6, y: 4.75, w: 8.8, h: 0.45, fontSize: 15, align: "center", valign: "middle", objectName: "Idea clave" });
  s.addNotes("Así está montado. El cliente habla y Claude conduce la conversación. En cada turno, el extractor propone los datos con la frase exacta del cliente. Pero el código no se fía: comprueba que la cita existe y decide el nivel con una rúbrica fija. Los números, como el riesgo, los calculan reglas en Python, nunca el modelo. Y nada sale hasta que una persona lo valida.");

  // ===== 3 · Cada dato con su prueba =====
  s = nueva(BG.b);
  titulo(s, "Cada dato, con su prueba");
  sub(s, "Lo que el cliente declara frente a lo que demuestra. Carmen, caso simulado.");
  vidrio(s, 0.6, 1.7, 3.1, 2.55, "Burbuja de Carmen");
  texto(s, "CARMEN · MIN 0:57", { x: 0.85, y: 1.9, w: 2.7, h: 0.3, fontFace: F.mono, fontSize: 10, color: K.tenue, charSpacing: 2 });
  texto(s, "«Eso no puede pasar, el fondo es del banco.»", { x: 0.85, y: 2.25, w: 2.65, h: 1.6, fontFace: F.tit, fontSize: 19, italic: true, valign: "middle", objectName: "Cita" });
  img(s, IC.flecha, 3.85, 2.85, 0.28, 0.28, "Flecha");
  vidrio(s, 4.3, 1.7, 5.1, 2.55, "Dato extraído", K.ambar);
  texto(s, "Conocimiento de renta variable", { x: 4.55, y: 1.88, w: 4.6, h: 0.35, fontFace: F.tit, fontSize: 14 });
  texto(s, "Declaró", { x: 4.55, y: 2.35, w: 2.0, h: 0.3, fontSize: 11, color: K.tenue });
  texto(s, "Alto", { x: 4.55, y: 2.62, w: 2.0, h: 0.55, fontFace: F.tit, fontSize: 28, color: K.suave });
  texto(s, "Demostró", { x: 6.85, y: 2.35, w: 2.3, h: 0.3, fontSize: 11, color: K.tenue });
  texto(s, "Ninguno", { x: 6.85, y: 2.62, w: 2.4, h: 0.55, fontFace: F.tit, fontSize: 28, color: K.menta });
  img(s, IC.aviso, 4.55, 3.4, 0.26, 0.26, "Aviso");
  texto(s, "Declarado ≠ demostrado · lo revisa el asesor", { x: 4.9, y: 3.36, w: 4.3, h: 0.34, fontFace: F.tit, fontSize: 12, color: K.ambar, valign: "middle" });
  texto(s, "Fuente: conversación · cita literal · minuto · versión del perfil", { x: 4.55, y: 3.78, w: 4.7, h: 0.3, fontFace: F.mono, fontSize: 9.5, color: K.tenue });
  texto(s, "Si la cita no aparece literal en la conversación, el dato se descarta con su motivo.", { x: 0.6, y: 4.55, w: 8.8, h: 0.4, fontSize: 13, color: K.suave, align: "center", valign: "middle", objectName: "Regla" });
  s.addNotes("El paso clave, con Carmen: declaró alto, demostró ninguno. El dato guarda la cita, el minuto y la versión del perfil, y el aviso llega al asesor. Si el modelo inventa una cita, el código la descarta.");

  // ===== 4 · Lo que recibe la entidad =====
  s = nueva(BG.a);
  titulo(s, "Lo que recibe el asesor");
  img(s, CAP.entidad, 0.6, 1.3, 5.0, 3.75, "Captura: vista de la entidad");
  const filas = [
    [IC.escudo, "Perfil conservador", "Riesgo máximo 3 de 7: manda el criterio más restrictivo."],
    [IC.no, "Renta variable: no", "No es conveniente: no demostró entenderla."],
    [IC.ok, "Lo valida una persona", "Hasta entonces, el agente no puede usarlo."],
  ];
  filas.forEach(([ic, h, d], i) => {
    const y = 1.45 + i * 1.2;
    vidrio(s, 5.85, y, 3.55, 1.02, "Resultado: " + h);
    img(s, ic, 6.05, y + 0.32, 0.36, 0.36, "Icono: " + h);
    texto(s, h, { x: 6.55, y: y + 0.14, w: 2.75, h: 0.36, fontFace: F.tit, fontSize: 13.5, valign: "middle" });
    texto(s, d, { x: 6.55, y: y + 0.5, w: 2.75, h: 0.42, fontSize: 10.5, color: K.suave, valign: "top" });
  });
  s.addNotes("El asesor recibe el perfil hecho: conservador, riesgo máximo tres de siete, y renta variable no conveniente. Solo interviene ante dudas, como este aviso, y valida. Hasta entonces, el agente no puede usarlo.");

  // ===== 5 · Dentro de la app de cada entidad =====
  s = nueva(BG.b);
  titulo(s, "Dentro de la app de cada entidad");
  sub(s, "No es otra app: una función con su marca, integrada en la de la entidad.");
  const momentos = [
    [B.alta, "Alta", "Una conversación crea el perfil real del cliente."],
    [B.cambio, "Microentrevistas", "«¿Ha cambiado algo?» Solo se pregunta lo que cambió."],
    [B.vivo, "Perfil vivo", "La entidad, al día de lo que el cliente cuenta."],
  ];
  momentos.forEach(([b, h, d], i) => {
    const x = 0.6 + i * 2.05;
    vidrio(s, x, 1.65, 1.9, 2.2, "Momento: " + h, i === 0 ? K.menta : null);
    img(s, b, x + 0.65, 1.85, 0.6, 0.6, "Icono: " + h);
    texto(s, h, { x: x + 0.1, y: 2.55, w: 1.7, h: 0.4, fontFace: F.tit, fontSize: 14, align: "center", valign: "middle" });
    texto(s, d, { x: x + 0.12, y: 2.98, w: 1.66, h: 0.8, fontSize: 10.5, color: K.suave, align: "center", valign: "top" });
  });
  // Sello sobre una tarjeta clara (como se ve dentro de la app anfitriona)
  s.addShape(SH.roundRect, { x: 0.6, y: 4.1, w: 5.9, h: 0.75, rectRadius: 0.1, fill: { color: "FFFFFF" }, line: { color: "FFFFFF", width: 0 }, objectName: "Tarjeta clara" });
  texto(s, "Fondo Global Equilibrado", { x: 0.8, y: 4.18, w: 2.6, h: 0.3, fontFace: F.tit, fontSize: 11, color: "282828" });
  pastilla(s, "✓ Encaja contigo", 0.8, 4.47, 1.45, K.verde);
  img(s, SELLO, 4.15, 4.33, 2.15, 2.15 * 219 / 1200, "Sello Powered by idóneo");
  // MCP
  vidrio(s, 6.85, 1.65, 2.55, 3.2, "MCP", K.turquesa);
  texto(s, "Por MCP", { x: 7.0, y: 1.8, w: 2.25, h: 0.36, fontFace: F.tit, fontSize: 15, color: K.menta });
  texto(s, "El estándar con el que los agentes de IA usan herramientas.", { x: 7.0, y: 2.18, w: 2.25, h: 0.62, fontSize: 10, color: K.suave, valign: "top" });
  texto(s, "Agente → get_investment_constraints", { x: 7.0, y: 2.9, w: 2.3, h: 0.5, fontFace: F.mono, fontSize: 9.5, color: K.tinta, valign: "top" });
  texto(s, "← riesgo máx. 3\n← renta variable: no conveniente", { x: 7.0, y: 3.4, w: 2.3, h: 0.62, fontFace: F.mono, fontSize: 9.5, color: K.menta, valign: "top" });
  texto(s, "Probado con Claude y el conector de MyInvestor", { x: 7.0, y: 4.1, w: 2.3, h: 0.6, fontSize: 9.5, color: K.tenue, valign: "top" });
  s.addNotes("idóneo vive dentro de la app de cada entidad, con su marca: Powered by idóneo. En el alta, en microentrevistas cuando algo cambia y manteniendo el perfil vivo. Y se conecta a sus agentes de IA por MCP: el agente pide las restricciones de Carmen y recibe riesgo máximo tres y renta variable no conveniente. Probado con Claude y el conector de MyInvestor." +
    nota("\n(No decir precio. Si preguntan: lo contrata la entidad y lo integra como una función más.)"));

  // ===== 6 · Lo que hemos medido =====
  s = nueva(BG.centro);
  titulo(s, "Lo que hemos medido", { align: "center" });
  texto(s, [{ text: "ESMA avisa: ", options: { color: K.menta, fontFace: F.tit } }, { text: "con sistemas automatizados, el cliente tiende a sobrevalorarse.", options: { color: K.suave } }],
    { x: 0.8, y: 1.05, w: 8.4, h: 0.45, fontSize: 13.5, align: "center", valign: "middle", objectName: "Motivo" });
  const cifras = [
    ["31/31", "datos acertados", "7 entrevistas difíciles (E-04)"],
    ["70/70", "datos cubiertos", "laboratorio, 8 entrevistas (E-07)"],
    ["0", "falsas alarmas", "verificador: 24 pruebas (E-06)"],
    ["43 s", "entrevista corta", "perfil listo para validar (E-08)"],
  ];
  cifras.forEach(([n, h, d], i) => {
    const x = 0.6 + i * 2.23;
    vidrio(s, x, 1.8, 2.05, 2.3, "Cifra: " + h);
    texto(s, n, { x, y: 2.0, w: 2.05, h: 0.85, fontFace: F.tit, fontSize: 38, color: K.menta, align: "center", valign: "middle" });
    texto(s, h, { x: x + 0.1, y: 2.9, w: 1.85, h: 0.4, fontFace: F.tit, fontSize: 13, align: "center", valign: "middle" });
    texto(s, d, { x: x + 0.05, y: 3.32, w: 1.95, h: 0.6, fontSize: 9, color: K.tenue, align: "center", valign: "top" });
  });
  texto(s, "Clientes simulados · casos escritos por el equipo · no es una validación independiente", { x: 0.6, y: 4.4, w: 8.8, h: 0.4, fontSize: 12, color: K.suave, align: "center", valign: "middle", objectName: "Límite" });
  s.addNotes("¿Por qué comprobar? ESMA avisa: con sistemas automatizados, el cliente tiende a sobrevalorarse. Lo que hemos medido: 31 de 31 datos acertados, 70 de 70 cubiertos, cero falsas alarmas y el perfil listo para validar en unos 43 segundos. Con un límite claro: clientes simulados y casos escritos por nosotros.");

  // ===== 7 · Cierre =====
  s = nueva(BG.centro);
  img(s, ICONO, 4.45, 0.75, 1.1, 1.1, "Icono idóneo");
  texto(s, "GPTadvisor hace fiable la recomendación.", { x: 0.5, y: 2.15, w: 9.0, h: 0.55, fontSize: 22, color: K.suave, align: "center", valign: "middle", objectName: "Frase 1" });
  texto(s, "idóneo hace fiable el perfil sobre el que se recomienda.", { x: 0.3, y: 2.7, w: 9.4, h: 0.75, fontFace: F.tit, fontSize: 22, align: "center", valign: "middle", objectName: "Frase 2" });
  s.addShape(SH.roundRect, { x: 3.3, y: 4.05, w: 3.4, h: 0.55, rectRadius: 0.27, fill: { color: K.menta }, line: { color: K.menta, width: 0 }, objectName: "Botón demo" });
  img(s, IC.play, 3.6, 4.22, 0.2, 0.2, "Play");
  texto(s, "Demo en vivo · datos simulados", { x: 3.88, y: 4.05, w: 2.82, h: 0.55, fontFace: F.tit, fontSize: 11.5, color: K.noche, valign: "middle" });
  s.addNotes("GPTadvisor hace fiable la recomendación. idóneo hace fiable el perfil sobre el que se recomienda. Vamos a verlo." +
    nota("\n(Si no da tiempo a la demo en directo: cerrar aquí con el lema «Invertir empieza por escucharte».)"));

  await pres.writeFile({ fileName: OUT });
  console.log("Escrito", OUT, FINAL ? "(final)" : "(trabajo)");
}

main().catch((e) => { console.error(e); process.exit(1); });
