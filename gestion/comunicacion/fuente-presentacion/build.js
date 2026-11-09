// Presentación visual de Idóneo (Hack Finance UC3M 2026). Versión 2.
//
// Uso:  node build_v2.js salida.pptx [--final] [--hecho=voz,extractor,audio]
//   - Sin --final: VERSIÓN DE TRABAJO, con etiquetas ámbar donde algo está pendiente.
//   - Con  --final: sin etiquetas; lo pendiente se reescribe como "siguiente paso".
//   - --hecho=...:  marca como terminado lo que ya funciona (voz, extractor, audio) y cambia las frases a afirmativas.
//   - Las métricas medidas se rellenan en METRICAS (más abajo). Si es null, la final no enseña ese panel.
//
// Colores del tema de la app (frontend/src/tema/tema.css). Sin logos de terceros: solo nombres.
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const fa = require("react-icons/fa");
const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));

const ASSETS = __dirname + "/assets";
const OUT = process.argv[2];
const FINAL = process.argv.includes("--final");
const hechoArg = (process.argv.find((a) => a.startsWith("--hecho=")) || "").slice(8).split(",").filter(Boolean);
const ESTADO = { voz: hechoArg.includes("voz"), extractor: hechoArg.includes("extractor"), audio: hechoArg.includes("audio") };
// Métricas medidas por Pablo. Rellenar cuando existan, por ejemplo:
//   { tiempo: "…", contradicciones: "…", latencia: "…" }
const METRICAS = null;

const THEME = {
  name: "Idoneo",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14202B", lt1: "FFFFFF", dk2: "0B2A4A", lt2: "F4F6F8",
    accent1: "12A37F", accent2: "B45309", accent3: "5B6875", accent4: "E3F6F0", accent5: "FFF4E0", accent6: "0B6B53",
    hlink: "12A37F", folHlink: "5B6875",
  },
};

// pptxgenjs no escribe los colores del tema: se sustituye el esquema de colores del tema del archivo.
async function aplicarTema(file) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const claves = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const esquema = '<a:clrScheme name="' + THEME.name + '">' + claves.map((k) => "<a:" + k + '><a:srgbClr val="' + THEME.colors[k] + '"/></a:' + k + ">").join("") + "</a:clrScheme>";
  for (const name of Object.keys(zip.files)) {
    if (/^ppt\/theme\/theme\d+\.xml$/.test(name)) {
      let xml = await zip.file(name).async("string");
      xml = xml.replace(/<a:clrScheme[\s\S]*?<\/a:clrScheme>/, esquema);
      xml = xml.replace(/(<a:theme\b[^>]*\sname=")[^"]*(")/, "$1" + THEME.name + "$2");
      zip.file(name, xml);
    }
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

const v = (hecho, si, no) => (hecho ? si : no); // frase afirmativa o de "siguiente paso"

async function icon(Icon, hex) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: 256 }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

async function addTransitions(file) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  for (const name of Object.keys(zip.files)) {
    if (/^ppt\/slides\/slide\d+\.xml$/.test(name)) {
      let xml = await zip.file(name).async("string");
      if (!xml.includes("<p:transition") && xml.includes("</p:clrMapOvr>")) {
        xml = xml.replace("</p:clrMapOvr>", '</p:clrMapOvr><p:transition spd="med"><p:fade/></p:transition>');
        zip.file(name, xml);
      }
    }
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Idóneo · Hack Finance UC3M 2026";
  pres.author = "Equipo Hack Finance UC3M";
  const C = pres.SchemeColor;
  const SH = pres.ShapeType;

  // ---------- Layouts ----------
  pres.defineSlideMaster({
    title: "PORTADA", background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.45, w: 5.6, h: 1.4, fontSize: 72, bold: true, color: C.background1, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.95, w: 5.2, h: 1.1, fontSize: 22, color: C.accent4, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "LIBRE", background: { color: C.background2 }, objects: [],
  });
  pres.defineSlideMaster({
    title: "CLARA", background: { color: C.background2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.7, fontSize: 32, bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "OSCURA", background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.7, fontSize: 32, bold: true, color: C.background1, align: "left", valign: "middle", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CIERRE", background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 1.2, w: 8.8, h: 0.6, fontSize: 24, color: C.accent4, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.95, w: 8.8, h: 2.0, fontSize: 40, bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });

  // ---------- Ayudas de dibujo ----------
  const card = (s, name, x, y, w, h, fill, extra) =>
    s.addShape(SH.roundRect, Object.assign({
      x, y, w, h, fill: { color: fill || C.background1 }, rectRadius: 0.12,
      shadow: { type: "outer", color: "0B2A4A", opacity: 0.12, blur: 8, offset: 2, angle: 90 }, objectName: name,
    }, extra || {}));
  const chipW = (t) => t.length * 0.088 + 0.32;
  const chip = (s, name, text, x, y, kind, w) => {
    const k = { pend: [C.accent5, C.accent2], ok: [C.accent4, C.accent6], info: [C.background2, C.accent3], blanco: [C.background1, C.accent3], okb: [C.background1, C.accent6] }[kind];
    s.addText(text, {
      shape: SH.roundRect, x, y, w: w || chipW(text), h: 0.27, fill: { color: k[0] }, color: k[1],
      fontSize: 10, bold: true, align: "center", valign: "middle", margin: 0, rectRadius: 0.13, isTextBox: true, objectName: name,
    });
  };
  // Etiqueta de pendiente: solo en la versión de trabajo y solo si lo que marca no está hecho
  const pend = (s, name, text, x, y, w, hecho) => { if (!FINAL && !hecho) chip(s, name, text, x, y, "pend", w); };
  const circleIcon = (s, name, img, x, y, d, fill) => {
    s.addShape(SH.ellipse, { x, y, w: d, h: d, fill: { color: fill || C.accent1 }, objectName: name + " (círculo)" });
    s.addImage({ data: img, x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5, altText: name, objectName: name });
  };
  const wave = (s, x0, yc, n, w, gap, hs, color, name) => {
    for (let i = 0; i < n; i++) {
      const h = hs[i % hs.length];
      s.addShape(SH.roundRect, { x: x0 + i * (w + gap), y: yc - h / 2, w, h, rectRadius: w / 2, fill: { color: i % 4 === 3 ? C.accent4 : color }, objectName: name + " " + (i + 1) });
    }
  };

  // ---------- Iconos ----------
  const I = {
    mic: await icon(fa.FaMicrophone, "FFFFFF"), search: await icon(fa.FaSearch, "FFFFFF"), file: await icon(fa.FaFileAlt, "FFFFFF"),
    check: await icon(fa.FaCheck, "FFFFFF"), calc: await icon(fa.FaCalculator, "FFFFFF"), brain: await icon(fa.FaBrain, "FFFFFF"),
    user: await icon(fa.FaMobileAlt, "FFFFFF"), shield: await icon(fa.FaShieldAlt, "FFFFFF"), robot: await icon(fa.FaRobot, "FFFFFF"),
    bank: await icon(fa.FaUniversity, "FFFFFF"), arrowW: await icon(fa.FaArrowRight, "FFFFFF"), arrowG: await icon(fa.FaArrowRight, "5B6875"),
    userCheck: await icon(fa.FaUserCheck, "FFFFFF"),
  };

  pres.addSection({ title: "Presentación" });
  const SEC = "Presentación";

  // =========================================================
  // 1 · Portada
  // =========================================================
  let s = pres.addSlide({ masterName: "PORTADA", sectionTitle: SEC });
  s.addText("HACK FINANCE UC3M 2026", { x: 0.6, y: 0.7, w: 5, h: 0.3, fontSize: 11, bold: true, charSpacing: 3, color: C.accent1, margin: 0, isTextBox: true, objectName: "Etiqueta del evento" });
  s.addText("Idóneo", { placeholder: "title" });
  s.addText("Un test MiFID que habla, comprueba y deja pruebas", { placeholder: "body" });
  s.addText("Prototipo con datos simulados", { x: 0.6, y: 4.8, w: 5, h: 0.3, fontSize: 12, color: C.background2, margin: 0, isTextBox: true, objectName: "Pie de portada" });
  wave(s, 6.45, 2.8, 15, 0.12, 0.07, [0.4, 0.8, 1.3, 1.9, 1.4, 2.3, 1.6, 2.7, 1.8, 2.2, 1.2, 1.7, 0.9, 0.6, 0.35], C.accent1, "Onda de voz");
  s.addNotes("[0:00 – 0:05] Buenos días. Esto es Idóneo. (Pendiente: nombre definitivo y presentación del equipo.)");

  // =========================================================
  // 2 · Carmen: lo que marcó / lo que dijo
  // =========================================================
  s = pres.addSlide({ masterName: "LIBRE", sectionTitle: SEC });
  s.addShape(SH.rect, { x: 5, y: 0, w: 5, h: 5.625, fill: { color: C.text2 }, objectName: "Mitad oscura" });
  s.addText("CARMEN · 68 AÑOS · 80.000 € · CASO SIMULADO", { x: 0.5, y: 0.45, w: 4.3, h: 0.3, fontSize: 10, bold: true, charSpacing: 2, color: C.accent3, margin: 0, isTextBox: true, objectName: "Contexto de Carmen" });
  chip(s, "Etiqueta: test", "LO QUE MARCÓ EN EL TEST", 0.5, 1.2, "blanco", 2.3);
  card(s, "Tarjeta: casilla marcada", 0.5, 1.7, 4.0, 1.7);
  circleIcon(s, "Casilla marcada", I.check, 0.75, 2.25, 0.6);
  s.addText("Conozco bien los fondos de renta variable", { x: 1.55, y: 1.85, w: 2.8, h: 1.4, fontSize: 22, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Respuesta marcada" });
  s.addText("Casilla marcada en el test MiFID de su banco", { x: 0.5, y: 3.6, w: 4.0, h: 0.4, fontSize: 12, color: C.accent3, margin: 0, isTextBox: true, objectName: "Origen de la respuesta" });
  s.addShape(SH.ellipse, { x: 4.6, y: 2.15, w: 0.8, h: 0.8, fill: { color: C.accent2 }, objectName: "Símbolo distinto (círculo)" });
  s.addText("≠", { x: 4.6, y: 2.15, w: 0.8, h: 0.8, fontSize: 30, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Símbolo distinto" });
  chip(s, "Etiqueta: hablando", "LO QUE DIJO, HABLANDO", 5.6, 1.2, "info", 2.2);
  s.addText("«Eso no puede pasar, el fondo es del banco.»", { x: 5.6, y: 1.65, w: 3.9, h: 1.9, fontSize: 28, italic: true, bold: true, color: C.background1, margin: 0, valign: "middle", isTextBox: true, objectName: "Cita de Carmen" });
  wave(s, 5.6, 4.25, 24, 0.09, 0.06, [0.25, 0.5, 0.85, 0.4, 0.7, 0.3, 0.95, 0.55, 0.35, 0.75], C.accent1, "Onda de la cita");
  s.addText("Minuto 0:57 de la conversación de ejemplo", { x: 5.6, y: 4.85, w: 3.9, h: 0.3, fontSize: 11, color: C.accent4, margin: 0, isTextBox: true, objectName: "Minuto de la cita" });
  s.addNotes("[0:05 – 0:38] Imaginad a Carmen. Tiene 68 años y 80.000 euros en depósitos. En el test MiFID de su banco marcó que conoce bien los fondos de renta variable. Pero cuando le preguntan qué pasaría si su fondo baja, dice: «eso no puede pasar, el fondo es del banco». Marcó una cosa y demostró la contraria. Y el test, que se basa en lo que ella declara, no lo detecta. Carmen es un caso simulado.");

  // =========================================================
  // 3 · Solución: habla, comprueba, deja pruebas
  // =========================================================
  s = pres.addSlide({ masterName: "LIBRE", sectionTitle: SEC });
  s.addShape(SH.ellipse, { x: 5.8, y: 0.7, w: 4.2, h: 4.2, fill: { color: C.accent4 }, objectName: "Círculo de fondo del móvil" });
  const bloques = [
    ["Habla", "Onboarding por voz, primero para el móvil", I.mic, ["VOZ POR PROBAR", ESTADO.voz]],
    ["Comprueba", "Plantea escenarios y contrasta lo declarado con lo demostrado", I.search, null],
    ["Deja pruebas", v(ESTADO.audio, "Cada dato con cita, audio y versión", "Cada dato con su cita, fuente y versión"), I.file, ["CLIP DE AUDIO PENDIENTE", ESTADO.audio]],
  ];
  bloques.forEach(([word, sub, img, tag], i) => {
    const y = 0.6 + i * 1.5;
    circleIcon(s, "Icono: " + word, img, 0.5, y + 0.08, 0.75);
    s.addText(word, { x: 1.5, y, w: 4.2, h: 0.85, fontSize: 44, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Palabra: " + word });
    s.addText(sub, { x: 1.5, y: y + 0.85, w: 3.6, h: 0.5, fontSize: 14, color: C.accent3, margin: 0, valign: "top", isTextBox: true, objectName: "Descripción: " + word });
    if (tag) pend(s, "Estado: " + word, tag[0], 1.5, y + 1.22, null, tag[1]);
  });
  s.addShape(SH.roundRect, { x: 6.85, y: 0.6, w: 2.17, h: 4.55, rectRadius: 0.2, fill: { color: C.text2 }, objectName: "Marco del móvil" });
  s.addImage({ path: ASSETS + "/entrevista_movil.png", x: 6.94, y: 0.71, w: 1.99, h: 4.31, altText: "Captura de la entrevista en el móvil: Carmen dice «eso no puede pasar, el fondo es del banco» y el asistente se lo explica", objectName: "Captura de la entrevista" });
  s.addText("Declarado ≠\ndemostrado", {
    shape: SH.roundRect, x: 5.2, y: 2.95, w: 1.65, h: 0.85, rectRadius: 0.12, fill: { color: C.accent5 }, color: C.accent2, fontSize: 14, bold: true, align: "center", valign: "middle",
    margin: 0, rotate: -4, isTextBox: true, shadow: { type: "outer", color: "0B2A4A", opacity: 0.18, blur: 6, offset: 2, angle: 90 }, objectName: "Etiqueta flotante: declarado distinto de demostrado",
  });
  s.addNotes("[0:38 – 1:08] Idóneo cambia el test por una conversación. Habla: onboarding por voz, pensado primero para el móvil" + v(ESTADO.voz, ".", " (pendiente: voz probada).") +
    " Comprueba: plantea escenarios y contrasta lo declarado con lo demostrado. Y deja pruebas: cada dato con su cita, su fuente y su versión" + v(ESTADO.audio, ", y su clip de audio.", " (pendiente: clip de audio).") +
    " Nosotros no recomendamos productos: garantizamos que el agente de la entidad sabe quién es Carmen.");

  // =========================================================
  // 4 · De la conversación al dato (oscura)
  // =========================================================
  s = pres.addSlide({ masterName: "OSCURA", sectionTitle: SEC });
  s.addText("De la conversación al dato", { placeholder: "title" });
  s.addText("ASISTENTE", { x: 0.5, y: 1.2, w: 2, h: 0.25, fontSize: 10, bold: true, charSpacing: 2, color: C.accent4, margin: 0, isTextBox: true, objectName: "Etiqueta asistente" });
  s.addShape(SH.roundRect, { x: 0.5, y: 1.5, w: 3.2, h: 0.9, rectRadius: 0.2, fill: { color: C.background1 }, objectName: "Burbuja del asistente (forma)" });
  s.addText("¿Podría perder dinero un fondo así?", { x: 0.75, y: 1.5, w: 2.75, h: 0.9, fontSize: 16, color: C.text2, valign: "middle", margin: 0, isTextBox: true, objectName: "Burbuja del asistente" });
  s.addText("CARMEN · 0:57", { x: 0.9, y: 2.75, w: 2.5, h: 0.25, fontSize: 10, bold: true, charSpacing: 2, color: C.accent4, margin: 0, isTextBox: true, objectName: "Etiqueta Carmen" });
  s.addShape(SH.roundRect, { x: 0.9, y: 3.05, w: 3.0, h: 1.3, rectRadius: 0.2, fill: { color: C.accent1 }, objectName: "Burbuja de Carmen (forma)" });
  s.addText("«Eso no puede pasar, el fondo es del banco.»", { x: 1.15, y: 3.05, w: 2.55, h: 1.3, fontSize: 16, bold: true, italic: true, color: C.background1, valign: "middle", margin: 0, isTextBox: true, objectName: "Burbuja de Carmen" });
  circleIcon(s, "Flecha: Claude comprueba", I.arrowW, 4.3, 2.3, 0.6);
  s.addText("Claude lo compara", { x: 4.0, y: 2.95, w: 1.35, h: 0.4, fontSize: 11, color: C.accent4, align: "center", margin: 0, isTextBox: true, objectName: "Texto de la flecha" });
  pend(s, "Estado: extractor", "EN DESARROLLO", 3.98, 3.4, 1.4, ESTADO.extractor);
  // Tarjeta del dato
  card(s, "Tarjeta del dato", 5.55, 1.2, 3.95, 3.55);
  s.addText("CONOCIMIENTO · FONDOS DE RENTA VARIABLE", { x: 5.75, y: 1.35, w: 3.6, h: 0.3, fontSize: 10, bold: true, charSpacing: 1, color: C.accent3, margin: 0, isTextBox: true, objectName: "Etiqueta del dato" });
  s.addText("Declaró", { x: 5.75, y: 1.75, w: 1.4, h: 0.25, fontSize: 11, color: C.accent3, margin: 0, isTextBox: true, objectName: "Etiqueta declaró" });
  s.addText("Alto", { x: 5.75, y: 1.98, w: 1.4, h: 0.65, fontSize: 32, color: C.accent3, strike: "sngStrike", margin: 0, valign: "middle", isTextBox: true, objectName: "Valor declarado" });
  s.addImage({ data: I.arrowG, x: 7.05, y: 2.18, w: 0.26, h: 0.26, altText: "flecha", objectName: "Flecha del dato" });
  s.addText("Demostró", { x: 7.5, y: 1.75, w: 1.8, h: 0.25, fontSize: 11, color: C.accent3, margin: 0, isTextBox: true, objectName: "Etiqueta demostró" });
  s.addText("Ninguno", { x: 7.5, y: 1.98, w: 1.9, h: 0.65, fontSize: 32, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Valor demostrado" });
  chip(s, "Fuente del dato", "FUENTE: DEMOSTRADO", 5.75, 2.85, "ok", 1.75);
  chip(s, "Prueba del dato", "PRUEBA · MINUTO 0:57", 7.65, 2.85, "info", 1.65);
  s.addShape(SH.roundRect, { x: 5.75, y: 3.3, w: 3.55, h: 0.45, rectRadius: 0.1, fill: { color: C.accent5 }, objectName: "Alerta del dato (forma)" });
  s.addText("Declarado ≠ demostrado", { x: 5.95, y: 3.3, w: 3.2, h: 0.45, fontSize: 14, bold: true, color: C.accent2, valign: "middle", margin: 0, isTextBox: true, objectName: "Alerta del dato" });
  s.addText("Tolerancia al riesgo", { x: 5.75, y: 3.9, w: 3.5, h: 0.25, fontSize: 11, color: C.accent3, margin: 0, isTextBox: true, objectName: "Etiqueta tolerancia" });
  s.addText("Declaró 3 de 5 → demostró 1 de 5", { x: 5.75, y: 4.15, w: 3.55, h: 0.4, fontSize: 15, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Tolerancia declarada y demostrada" });
  s.addText(v(ESTADO.extractor, "Datos simulados: la cita y el minuto salen de la conversación de ejemplo.", "Datos simulados. Hoy el perfil se carga con la conversación de ejemplo; que Claude lo extraiga en directo es el siguiente paso."),
    { x: 0.5, y: 4.95, w: 9, h: 0.4, fontSize: 11, color: C.accent4, margin: 0, isTextBox: true, objectName: "Nota: datos simulados" });
  s.addNotes("[1:08 – 1:38] Así se ve el paso clave. Carmen dice «eso no puede pasar». " + v(ESTADO.extractor, "Claude lo compara con lo que declaró", "El sistema lo compara con lo que declaró (pendiente: extractor con Claude en directo)") +
    ": había dicho alto, ha demostrado ninguno. El dato queda guardado con su fuente, la cita exacta y el minuto en que lo dijo. Y con su tolerancia al riesgo pasa igual: declaró tres sobre cinco, demostró uno.");

  // =========================================================
  // 5 · Lo que recibe el agente (escala de riesgo)
  // =========================================================
  s = pres.addSlide({ masterName: "CLARA", sectionTitle: SEC });
  s.addText("Lo que recibe el agente", { placeholder: "title" });
  s.addText("Carmen: riesgo máximo 3", { shape: SH.roundRect, x: 2.55, y: 1.1, w: 2.45, h: 0.4, rectRadius: 0.2, fill: { color: C.text2 }, color: C.background1, fontSize: 14, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Marca de riesgo máximo" });
  s.addShape(SH.triangle, { x: 3.625, y: 1.52, w: 0.3, h: 0.2, flipV: true, fill: { color: C.text2 }, objectName: "Flecha de la marca" });
  for (let i = 1; i <= 7; i++) {
    const on = i <= 3;
    s.addText(String(i), {
      shape: SH.roundRect, x: 0.8 + (i - 1) * 1.2, y: 1.8, w: 1.15, h: 0.6, rectRadius: 0.1,
      fill: on ? { color: C.accent1 } : { color: C.accent3, transparency: 80 }, color: on ? C.background1 : C.accent3,
      fontSize: 20, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Escala de riesgo " + i,
    });
  }
  s.addText("Indicador de riesgo de los productos (SRI): 1 = bajo · 7 = alto", { x: 0.8, y: 2.45, w: 8.4, h: 0.25, fontSize: 12, color: C.accent3, margin: 0, isTextBox: true, objectName: "Leyenda de la escala" });
  s.addText("Manda el criterio más restrictivo de los tres", { x: 0.8, y: 2.8, w: 8.4, h: 0.3, fontSize: 14, bold: true, color: C.text2, margin: 0, isTextBox: true, objectName: "Título de los criterios" });
  const crit = [
    ["Tolerancia", "1 de 5\n→ Conservador", true],
    ["Capacidad de pérdida", "74.600 € de 80.000 €\n→ Muy agresivo", false],
    ["Plazo", "10 años\n→ Agresivo", false],
  ];
  crit.forEach(([h, t, gana], i) => {
    const x = 0.8 + i * 2.9;
    card(s, "Criterio: " + h, x, 3.15, 2.7, 1.0, gana ? C.accent4 : C.background1);
    s.addText(h, { x: x + 0.15, y: 3.22, w: 1.8, h: 0.28, fontSize: 12, bold: true, color: C.accent3, margin: 0, valign: "middle", isTextBox: true, objectName: "Criterio título: " + h });
    s.addText(t, { x: x + 0.15, y: 3.52, w: 2.4, h: 0.58, fontSize: 14, bold: true, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "Criterio valor: " + h });
    if (gana) chip(s, "Marca: manda", "MANDA", x + 2.7 - 0.85, 3.22, "okb", 0.7);
  });
  const conv = [["Depósitos", "Conveniente", "ok"], ["Renta fija", "Conveniente", "ok"], ["Renta variable", "No conveniente", "pend"]];
  conv.forEach(([t, tag, kind], i) => {
    const x = 0.8 + i * 2.9;
    card(s, "Conveniencia: " + t, x, 4.3, 2.7, 0.5);
    s.addText(t, { x: x + 0.15, y: 4.3, w: 1.2, h: 0.5, fontSize: 13, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "Producto: " + t });
    chip(s, "Resultado: " + t, tag.toUpperCase(), x + 2.7 - 1.45, 4.41, kind, 1.33);
  });
  s.addText("Un asesor valida el perfil antes de que sea apto · Idóneo no recomienda", { shape: SH.roundRect, x: 0.8, y: 4.95, w: 8.5, h: 0.4, rectRadius: 0.2, fill: { color: C.text2 }, color: C.background1, fontSize: 13, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Banda de validación humana" });
  s.addNotes("[1:38 – 2:10] Esto es lo que recibe el agente. El riesgo máximo de Carmen es tres sobre siete. Sale de tres criterios y manda el más restrictivo: su tolerancia al riesgo. Y la conveniencia: la renta variable no es conveniente para ella; los depósitos y la renta fija, sí. Todo se calcula con código, no con el modelo, y lo valida una persona antes de que el perfil sea apto.");

  // =========================================================
  // 6 · La IA como contrapeso (oscura)
  // =========================================================
  s = pres.addSlide({ masterName: "OSCURA", sectionTitle: SEC });
  s.addText("La IA como contrapeso", { placeholder: "title" });
  s.addText([
    { text: "ESMA avisa: ", options: { color: C.accent1, bold: true } },
    { text: "con sistemas automatizados, el riesgo de que el cliente se sobrevalore es mayor.", options: { color: C.background1 } },
  ], { x: 0.5, y: 1.05, w: 9, h: 1.1, fontSize: 25, margin: 0, valign: "top", isTextBox: true, objectName: "Aviso de ESMA" });
  s.addText("Directrices de ESMA sobre idoneidad (2023), párrafo 52", { x: 0.5, y: 2.05, w: 9, h: 0.3, fontSize: 11, color: C.accent4, margin: 0, isTextBox: true, objectName: "Fuente del aviso" });
  const hMetricas = !FINAL || METRICAS;
  const hCard = hMetricas ? 1.8 : 1.9;
  const oy = hMetricas ? 0 : 0.25; // sin panel de métricas, las tarjetas bajan para centrar el bloque
  const fd = hMetricas ? 14 : 17;
  const roles = [
    ["Voz", v(ESTADO.voz, "Carmen contesta hablando, no rellenando casillas", "Carmen contestará hablando, no rellenando casillas"), I.mic, ["VOZ SIN PROBAR", ESTADO.voz]],
    ["Claude", v(ESTADO.extractor, "Comprueba lo que dice y marca las contradicciones", "Comprobará lo que dice y marcará las contradicciones"), I.brain, ["EN DESARROLLO", ESTADO.extractor]],
    ["Código", "Riesgo, pérdida y conveniencia: el modelo nunca calcula un número", I.calc, null],
  ];
  roles.forEach(([h, d, img, tag], i) => {
    const x = 0.5 + i * 3.05;
    card(s, "Rol: " + h, x, 2.65 + oy, 2.9, hCard);
    circleIcon(s, "Icono: " + h, img, x + 0.2, 2.8 + oy, 0.55);
    s.addText(h, { x: x + 0.9, y: 2.8 + oy, w: 1.2, h: 0.55, fontSize: 20, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Rol título: " + h });
    s.addText(d, { x: x + 0.2, y: 3.45 + oy, w: 2.5, h: hCard - 0.95, fontSize: fd, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Rol descripción: " + h });
    if (tag) pend(s, "Estado: " + h, tag[0], x + 0.2, 2.65 + oy + hCard - 0.4, null, tag[1]);
  });
  if (hMetricas) {
    const m = [["Tiempo frente a un formulario", METRICAS && METRICAS.tiempo], ["Contradicciones detectadas", METRICAS && METRICAS.contradicciones], ["Latencia de la voz", METRICAS && METRICAS.latencia]];
    m.forEach(([t, val], i) => {
      const x = 0.5 + i * 3.05;
      s.addShape(SH.roundRect, { x, y: 4.65, w: 2.9, h: 0.7, rectRadius: 0.1, fill: { color: C.background1, transparency: 88 }, objectName: "Panel métrica: " + t });
      s.addText(t, { x: x + 0.15, y: 4.69, w: 2.6, h: 0.3, fontSize: 12, color: C.accent4, margin: 0, valign: "middle", isTextBox: true, objectName: "Métrica: " + t });
      if (val) s.addText(val, { x: x + 0.15, y: 4.98, w: 2.6, h: 0.32, fontSize: 16, bold: true, color: C.background1, margin: 0, valign: "middle", isTextBox: true, objectName: "Valor métrica: " + t });
      else chip(s, "Estado métrica " + (i + 1), "PENDIENTE DE MEDIR", x + 0.15, 5.0, "pend", 1.8);
    });
  }
  s.addNotes("[2:10 – 2:37] ¿Por qué una IA? ESMA advierte de que con sistemas automatizados el riesgo de que el cliente se sobrevalore es mayor. Idóneo es el contrapeso, y tiene tres piezas: la voz, para que Carmen conteste hablando" + v(ESTADO.voz, "", " (pendiente: voz probada)") +
    "; Claude, que comprueba lo que dice" + v(ESTADO.extractor, "", " (pendiente: extractor)") + "; y código, que calcula los números, porque el modelo nunca calcula un número." +
    (METRICAS ? " Impacto medido: " + [METRICAS.tiempo, METRICAS.contradicciones, METRICAS.latencia].join("; ") + "." : " (Pendiente: impacto medido: tiempo frente a un formulario, contradicciones detectadas y latencia — Pablo. Si no se mide, no se dice.)"));

  // =========================================================
  // 7 · Entra en vuestros agentes
  // =========================================================
  s = pres.addSlide({ masterName: "CLARA", sectionTitle: SEC });
  s.addText("Entra en vuestros agentes", { placeholder: "title" });
  const nx = [0.5, 2.8, 5.1, 7.4], nw = 1.9;
  const nodos = [
    ["Cliente", "Habla desde el móvil", I.user, false],
    ["Idóneo", "Perfil verificado", I.shield, true],
    ["Agente", "GPTadvisor · Claude con MyInvestor", I.robot, false],
    ["Propuesta", "La hace el agente", I.userCheck, false],
  ];
  nodos.forEach(([h, d, img, hi], i) => {
    card(s, "Nodo: " + h, nx[i], 1.85, nw, 1.15, hi ? C.text2 : C.background1, hi ? { line: { color: C.accent1, width: 3 } } : {});
    circleIcon(s, "Icono: " + h, img, nx[i] + 0.12, 1.97, 0.4, hi ? C.accent1 : C.text2);
    s.addText(h, { x: nx[i] + 0.6, y: 1.95, w: nw - 0.65, h: 0.45, fontSize: 15, bold: true, color: hi ? C.background1 : C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Nodo título: " + h });
    s.addText(d, { x: nx[i] + 0.12, y: 2.42, w: nw - 0.24, h: 0.55, fontSize: 12, color: hi ? C.accent4 : C.accent3, margin: 0, valign: "top", isTextBox: true, objectName: "Nodo texto: " + h });
    if (i < 3) s.addImage({ data: I.arrowG, x: nx[i] + nw + 0.08, y: 2.31, w: 0.24, h: 0.24, altText: "flecha", objectName: "Flecha " + (i + 1) });
  });
  // Tramos protegidos
  s.addShape(SH.line, { x: 3.75, y: 1.7, w: 2.3, h: 0, line: { color: C.accent1, width: 4 }, objectName: "Tramo protegido por Idóneo" });
  s.addText("Idóneo protege lo que el agente recibe", { x: 3.45, y: 1.1, w: 2.8, h: 0.55, fontSize: 14, bold: true, color: C.accent6, align: "center", margin: 0, valign: "bottom", isTextBox: true, objectName: "Texto del tramo de Idóneo" });
  s.addShape(SH.line, { x: 6.05, y: 1.7, w: 2.3, h: 0, line: { color: C.accent3, width: 4 }, objectName: "Tramo protegido por GPTadvisor" });
  s.addText("GPTadvisor protege lo que el agente responde", { x: 6.3, y: 1.1, w: 2.5, h: 0.55, fontSize: 14, bold: true, color: C.accent3, align: "center", margin: 0, valign: "bottom", isTextBox: true, objectName: "Texto del tramo de GPTadvisor" });
  s.addText("No recomienda · valida una persona", { x: nx[1], y: 3.08, w: nw, h: 0.4, fontSize: 11, color: C.accent3, align: "center", margin: 0, isTextBox: true, objectName: "Nota de Idóneo" });
  s.addText("Es quien recomienda", { x: nx[2], y: 3.08, w: nw, h: 0.4, fontSize: 11, color: C.accent3, align: "center", margin: 0, isTextBox: true, objectName: "Nota del agente" });
  pend(s, "Estado: MCP", "MCP: URL PÚBLICA PENDIENTE", nx[1] + 0.05, 3.5, 2.1, false);
  const ent = [
    ["MyInvestor", I.bank, "Recibe un perfil ya hecho y auditable, y cubre la conveniencia en la compra sin asesoramiento."],
    ["GPTadvisor", I.robot, "Su agente recibe un perfil con fuente, versión y prueba de cada dato."],
  ];
  ent.forEach(([h, img, d], i) => {
    const x = 0.5 + i * 4.6;
    card(s, "Valor: " + h, x, 3.95, 4.4, 1.2);
    circleIcon(s, "Icono valor: " + h, img, x + 0.2, 4.15, 0.55);
    s.addText(h, { x: x + 0.95, y: 4.05, w: 3.3, h: 0.35, fontSize: 16, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Valor título: " + h });
    s.addText(d, { x: x + 0.95, y: 4.4, w: 3.3, h: 0.7, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Valor texto: " + h });
  });
  s.addNotes("[2:37 – 3:04] Y esto encaja en vuestros agentes. GPTadvisor protege lo que su agente responde. Idóneo protege lo que su agente recibe. Para MyInvestor, un perfil ya hecho y auditable, y la conveniencia para quien compra sin asesoramiento. Nosotros no recomendamos: recomienda el agente de la entidad, y valida una persona. (El MCP de MyInvestor solo se usa como conector dentro de Claude: sus términos no permiten otra cosa sin permiso. Pendiente: URL pública de nuestro MCP.)");

  // =========================================================
  // 8 · Cierre y paso a la demo
  // =========================================================
  s = pres.addSlide({ masterName: "CIERRE", sectionTitle: SEC });
  s.addText("GPTadvisor hace fiable la recomendación.", { placeholder: "body" });
  s.addText("Idóneo hace fiable el perfil sobre el que se recomienda", { placeholder: "title" });
  s.addText("DEMO EN VIVO · DATOS SIMULADOS", { shape: SH.roundRect, x: 0.6, y: 4.3, w: 4.2, h: 0.5, rectRadius: 0.25, fill: { color: C.accent1 }, color: C.background1, fontSize: 14, bold: true, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Aviso de demo" });
  wave(s, 6.3, 4.55, 18, 0.1, 0.07, [0.25, 0.5, 0.9, 0.4, 0.7, 0.3, 1.0, 0.55, 0.35, 0.75], C.accent1, "Onda de cierre");
  s.addNotes("[3:04 – 3:24] Seamos claros con los límites: los datos de Carmen son simulados y el perfil queda en borrador hasta que una persona lo valida. GPTadvisor hace fiable la recomendación. Idóneo hace fiable el perfil sobre el que se recomienda. Vamos a verlo. (Cambiar a la app: demo en vivo de 2:30; plan B en DEMO_GUION.md. Idea futura, solo si existe el miércoles: las entidades usan los perfiles para saber qué clientes encajan con un producto nuevo.)");

  await pres.writeFile({ fileName: OUT });
  await aplicarTema(OUT);
  await addTransitions(OUT);
  console.log("OK", FINAL ? "(FINAL)" : "(TRABAJO)", OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
