// Presentación de Idóneo (Hack Finance UC3M 2026). Versión 4: estilo «noche» de la web y MUY POCO TEXTO.
//
// Uso:  node build.js salida.pptx [--final] [--hecho=voz,extractor,audio,mcp]
//   - Cada diapositiva: el mensaje (título), la imagen y SOLO el texto necesario para entenderla.
//     Lo que se cuenta con detalle va en las NOTAS DEL ORADOR (y en ../PITCH_GUION.md).
//   - Sin --final: las notas incluyen avisos «(Pendiente: …)» para el equipo. Con --final, no.
//   - --hecho=...:  marca lo que ya funciona (voz, extractor, audio, mcp) y cambia las frases de las notas.
//
// Regla de diseño (pedida por Rodrigo, 10/11): ni relleno ni vacío. Sí: título con el mensaje y rótulos que
// explican el dibujo (14 pt o más). No: pies de página, números de diapositiva, etiquetas decorativas ni
// párrafos. Antes de añadir una frase, preguntarse si sin ella se entiende la diapositiva.
//
// Estilo de la web (frontend/src/tema/visual.css, clase .tema-noche): fondo casi negro, brillos azul, violeta y
// rosa, tarjetas de «vidrio» y la esfera 3D (assets/esfera_*.png, mismo shader que la web: ver esfera.html).
// Sin logos de terceros. Letras: Segoe UI (viene en todo Windows).
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
const ESTADO = { voz: hechoArg.includes("voz"), extractor: hechoArg.includes("extractor"), audio: hechoArg.includes("audio"), mcp: hechoArg.includes("mcp") };

// Nombre del equipo: NO sale en la diapositiva (regla de poco texto); solo lo dice quien presenta (notas).
const EQUIPO = "";

// Métricas MEDIDAS. Salen de docs/evaluacion/README.md:
//   - E-04 (10/11): extractor sobre 7 entrevistas simuladas, 31 de 31 datos esperados, 0 erróneos.
//   - E-05 (10/11): Carmen simulada por Claude, 10 de 10 datos y alerta «declarado ≠ demostrado»; mediana 1,8 s.
// En pantalla: la cifra y 1-3 palabras. Los límites (simulados, una repetición) se dicen en voz alta y la
// diapositiva lleva una sola marca «simulados». null = no hay nada medido: la diapositiva 6 enseña los tres roles.
const METRICAS = [
  { n: "31/31", t: "datos bien sacados de 7 entrevistas de prueba" },
  { n: "10/10", t: "datos de Carmen, y detecta su contradicción" },
  { n: "1,8 s", t: "tarda el asistente en responder (mediana, en texto)" },
];

// ---------- Paleta (visual.css · .tema-noche) ----------
const K = {
  fondo: "05070D", tinta: "F3F5FB", suave: "B7BFCE", tenue: "8A93A8",
  azul: "9DB8FF", violeta: "C49BFF", rosa: "F08AD0", verde: "9BEBC9",
  ambar: "FFB86B", ambarTexto: "FFD2A1", oscuro: "0B1030",
};
const F = { tit: "Segoe UI Semibold", txt: "Segoe UI", mono: "Consolas" };

const THEME = {
  name: "Idoneo noche",
  colors: {
    dk1: K.fondo, lt1: K.tinta, dk2: K.oscuro, lt2: K.suave,
    accent1: K.azul, accent2: K.violeta, accent3: K.rosa, accent4: K.verde, accent5: K.ambar, accent6: K.tenue,
    hlink: K.azul, folHlink: K.violeta,
  },
};

const v = (hecho, si, no) => (hecho ? si : no); // frase afirmativa o de "siguiente paso"
const nota = (t) => (FINAL ? "" : t); // avisos internos solo en la versión de trabajo

// ---------- Texto con degradado azul → violeta → rosa (un color por letra, sigue siendo texto editable) ----------
const hex2rgb = (h) => [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
const rgb2hex = (c) => c.map((x) => Math.round(x).toString(16).padStart(2, "0")).join("").toUpperCase();
function colorEn(t, paradas) {
  const tramo = Math.min(Math.floor(t * (paradas.length - 1)), paradas.length - 2);
  const local = t * (paradas.length - 1) - tramo;
  const a = hex2rgb(paradas[tramo]), b = hex2rgb(paradas[tramo + 1]);
  return rgb2hex(a.map((x, i) => x + (b[i] - x) * local));
}
const grad = (texto, extra, paradas = [K.azul, K.violeta, K.rosa]) =>
  [...texto].map((ch, i, arr) => ({ text: ch, options: Object.assign({ color: colorEn(arr.length > 1 ? i / (arr.length - 1) : 0, paradas) }, extra || {}) }));

// ---------- Imágenes generadas ----------
const png64 = (buf) => "image/png;base64," + buf.toString("base64");

// Fondo oscuro con brillos difusos, como el de la web
async function fondo(brillos) {
  const W = 1920, H = 1080;
  const defs = brillos.map((b, i) => `<radialGradient id="g${i}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#${b.c}" stop-opacity="${b.o}"/><stop offset="1" stop-color="#${b.c}" stop-opacity="0"/></radialGradient>`).join("");
  const elipses = brillos.map((b, i) => `<ellipse cx="${b.x * W}" cy="${b.y * H}" rx="${b.r * W}" ry="${b.r * W * 0.8}" fill="url(#g${i})"/>`).join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><defs>${defs}</defs><rect width="100%" height="100%" fill="#${K.fondo}"/>${elipses}</svg>`;
  return png64(await sharp(Buffer.from(svg)).png().toBuffer());
}
async function icono(Icon, hex, tam = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + hex, size: tam }));
  return sharp(Buffer.from(svg)).png().toBuffer();
}
// Baldosa con degradado y el icono en oscuro (como .cartaIcono de la portada web)
async function baldosa(Icon) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#${K.azul}"/><stop offset="0.55" stop-color="#${K.violeta}"/><stop offset="1" stop-color="#${K.rosa}"/></linearGradient></defs><rect width="256" height="256" rx="84" fill="url(#d)"/></svg>`;
  const ic = await sharp(await icono(Icon, "0B0D18", 120)).resize(120, 120).toBuffer();
  return png64(await sharp(Buffer.from(svg)).composite([{ input: ic, left: 68, top: 68 }]).png().toBuffer());
}
// Captura con esquinas redondeadas
async function redondear(ruta, radio) {
  const img = sharp(ruta);
  const { width, height } = await img.metadata();
  const mascara = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><rect width="${width}" height="${height}" rx="${radio}" fill="#fff"/></svg>`);
  return png64(await img.ensureAlpha().composite([{ input: mascara, blend: "dest-in" }]).png().toBuffer());
}
// Esfera más tenue (para ponerla detrás de otra cosa)
async function atenuar(ruta, factor) {
  const { data, info } = await sharp(ruta).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  for (let i = 3; i < data.length; i += 4) data[i] = Math.round(data[i] * factor);
  return png64(await sharp(data, { raw: info }).png().toBuffer());
}

// pptxgenjs no escribe los colores del tema: se sustituye el esquema del archivo. También se añade el fundido.
async function retocarArchivo(file) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const claves = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const esquema = '<a:clrScheme name="' + THEME.name + '">' + claves.map((k) => "<a:" + k + '><a:srgbClr val="' + THEME.colors[k] + '"/></a:' + k + ">").join("") + "</a:clrScheme>";
  for (const name of Object.keys(zip.files)) {
    let xml;
    if (/^ppt\/theme\/theme\d+\.xml$/.test(name)) {
      xml = await zip.file(name).async("string");
      xml = xml.replace(/<a:clrScheme[\s\S]*?<\/a:clrScheme>/, esquema);
      xml = xml.replace(/(<a:theme\b[^>]*\sname=")[^"]*(")/, "$1" + THEME.name + "$2");
    } else if (/^ppt\/slides\/slide\d+\.xml$/.test(name)) {
      xml = await zip.file(name).async("string");
      if (!xml.includes("<p:transition") && xml.includes("</p:clrMapOvr>")) xml = xml.replace("</p:clrMapOvr>", '</p:clrMapOvr><p:transition spd="med"><p:fade/></p:transition>');
    }
    if (xml) zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
  pres.theme = { headFontFace: F.tit, bodyFontFace: F.txt };
  pres.title = "Idóneo · Hack Finance UC3M 2026";
  pres.author = "Equipo Hack Finance UC3M";
  const SH = pres.ShapeType;
  pres.defineSlideMaster({ title: "NOCHE", background: { color: K.fondo }, objects: [] });
  pres.addSection({ title: "Pitch" });
  const nueva = (bg) => { const s = pres.addSlide({ masterName: "NOCHE", sectionTitle: "Pitch" }); s.background = { data: bg }; return s; };

  // ---------- Recursos ----------
  const BG = {
    portada: await fondo([{ x: 0.74, y: 0.48, r: 0.42, c: "8A5CFF", o: 0.42 }, { x: 0.08, y: 0.05, r: 0.35, c: "1F3BFF", o: 0.28 }, { x: 0.95, y: 1.0, r: 0.3, c: "FF7FD1", o: 0.16 }]),
    a: await fondo([{ x: 0.0, y: 0.0, r: 0.38, c: "1F3BFF", o: 0.3 }, { x: 1.0, y: 1.0, r: 0.42, c: "8A5CFF", o: 0.26 }]),
    b: await fondo([{ x: 0.8, y: 0.45, r: 0.4, c: "8A5CFF", o: 0.32 }, { x: 0.1, y: 1.05, r: 0.35, c: "1F3BFF", o: 0.22 }]),
    c: await fondo([{ x: 0.5, y: 0.5, r: 0.48, c: "6B4EF0", o: 0.3 }, { x: 1.0, y: 0.0, r: 0.3, c: "FF7FD1", o: 0.16 }]),
    centro: await fondo([{ x: 0.5, y: 0.45, r: 0.45, c: "8A5CFF", o: 0.36 }, { x: 0.12, y: 1.0, r: 0.35, c: "1F3BFF", o: 0.22 }, { x: 0.92, y: 0.95, r: 0.3, c: "FF7FD1", o: 0.16 }]),
  };
  const ESF = {
    aura: png64(fs.readFileSync(ASSETS + "/esfera_aura.png")),
    auraTenue: await atenuar(ASSETS + "/esfera_aura.png", 0.55),
    entidad: png64(fs.readFileSync(ASSETS + "/esfera_entidad.png")),
  };
  const CAP = {
    movil: await redondear(ASSETS + "/entrevista_movil_noche.jpg", 34),
    entidad: await redondear(ASSETS + "/entidad_carmen.jpg", 18),
  };
  const B = {
    mic: await baldosa(fa.FaMicrophone), buscar: await baldosa(fa.FaSearch), prueba: await baldosa(fa.FaFingerprint),
    brain: await baldosa(fa.FaBrain), calc: await baldosa(fa.FaCalculator),
    movil: await baldosa(fa.FaMobileAlt), robot: await baldosa(fa.FaRobot), propuesta: await baldosa(fa.FaUserCheck),
    flecha: await baldosa(fa.FaArrowRight),
  };
  const IC = {
    check: png64(await icono(fa.FaCheck, K.oscuro)), checkVerde: png64(await icono(fa.FaCheckCircle, K.verde)),
    flecha: png64(await icono(fa.FaArrowRight, K.tenue)), aviso: png64(await icono(fa.FaExclamationTriangle, K.rosa)),
    play: png64(await icono(fa.FaPlay, K.oscuro)), playClaro: png64(await icono(fa.FaPlayCircle, K.azul)),
    escudo: png64(await icono(fa.FaShieldAlt, K.violeta)), nada: png64(await icono(fa.FaTimesCircle, K.rosa)),
  };

  // Círculo con degradado y un halo suave (para el símbolo ≠)
  const CIRCULO = png64(await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#${K.azul}"/><stop offset="0.55" stop-color="#${K.violeta}"/><stop offset="1" stop-color="#${K.rosa}"/></linearGradient></defs><circle cx="128" cy="128" r="126" fill="url(#d)"/></svg>`)).png().toBuffer());

  // ---------- Ayudas de dibujo ----------
  const texto = (s, t, o) => s.addText(t, Object.assign({ margin: 0, isTextBox: true, fontFace: F.txt, color: K.tinta }, o));
  // Tarjeta de vidrio: blanco casi transparente con borde fino (.vidrio de la web)
  const vidrio = (s, name, x, y, w, h, extra) => s.addShape(SH.roundRect, Object.assign({
    x, y, w, h, rectRadius: 0.16, fill: { color: "FFFFFF", transparency: 95 }, line: { color: "FFFFFF", transparency: 88, width: 0.75 }, objectName: name,
  }, extra || {}));
  const onda = (s, x0, yc, n, w, gap, hs, name) => {
    for (let i = 0; i < n; i++) {
      const h = hs[i % hs.length];
      const c = colorEn(n > 1 ? i / (n - 1) : 0, [K.azul, K.violeta, K.rosa]);
      s.addShape(SH.roundRect, { x: x0 + i * (w + gap), y: yc - h / 2, w, h, rectRadius: w / 2, fill: { color: c }, line: { color: c, width: 0 }, objectName: name + " " + (i + 1) });
    }
  };
  // Pastilla grande y legible (no es una etiqueta pequeña: 14 pt como mínimo)
  const pastilla = (s, name, partes, x, y, w, h, estilo) => {
    const e = {
      ambar: { fill: { color: K.ambar, transparency: 84 }, line: { color: K.ambar, transparency: 40, width: 1 } },
      vidrio: { fill: { color: "FFFFFF", transparency: 93 }, line: { color: "FFFFFF", transparency: 80, width: 0.75 } },
      verde: { fill: { color: K.verde, transparency: 84 }, line: { color: K.verde, transparency: 40, width: 1 } },
      boton: { fill: { color: K.azul }, line: { color: K.azul, width: 0 }, shadow: { type: "outer", color: K.azul, opacity: 0.45, blur: 22, offset: 0, angle: 90 } },
    }[estilo];
    s.addShape(SH.roundRect, Object.assign({ x, y, w, h, rectRadius: h / 2, objectName: name + " (forma)" }, e));
    texto(s, partes, { x, y, w, h, fontSize: 16, align: "center", valign: "middle", objectName: name });
  };

  // Título de la diapositiva: el mensaje en una frase
  const titulo = (s, t, o) => texto(s, t, Object.assign({ x: 0.7, y: 0.45, w: 8.6, h: 0.7, fontFace: F.tit, fontSize: 28, valign: "middle", objectName: "Título" }, o));
  // Rótulo que explica una parte del dibujo (legible: 14 pt, nada de letra pequeña)
  const rotulo = (s, t, x, y, w, color) => texto(s, t, { x, y, w, h: 0.32, fontFace: F.tit, fontSize: 14, color: color || K.azul, valign: "middle", objectName: "Rótulo: " + t });

  // =========================================================
  // 1 · Portada: nombre, lema y la esfera
  // =========================================================
  let s = nueva(BG.portada);
  s.addShape(SH.ellipse, { x: 4.95, y: 2.05, w: 5.0, h: 1.35, fill: { type: "none" }, line: { color: K.violeta, transparency: 70, width: 0.75 }, objectName: "Órbita exterior" });
  s.addShape(SH.ellipse, { x: 5.45, y: 2.25, w: 4.0, h: 0.95, fill: { type: "none" }, line: { color: K.azul, transparency: 60, width: 0.75 }, objectName: "Órbita interior" });
  s.addImage({ data: ESF.aura, x: 5.15, y: 0.4, w: 4.6, h: 4.6, altText: "Esfera de plasma de Idóneo, el aura que escucha", objectName: "Esfera" });
  texto(s, "Idóneo", { x: 0.7, y: 1.05, w: 5, h: 1.3, fontFace: F.tit, fontSize: 72, charSpacing: -1, valign: "middle", objectName: "Nombre del producto" });
  texto(s, [{ text: "Tu perfil inversor,", options: { color: K.tinta, breakLine: true } }, ...grad("en una conversación.")],
    { x: 0.7, y: 2.45, w: 5.2, h: 1.2, fontFace: F.tit, fontSize: 30, valign: "top", lineSpacingMultiple: 0.95, objectName: "Lema" });
  texto(s, "El test MiFID que habla, comprueba y deja pruebas.", { x: 0.7, y: 3.8, w: 4.6, h: 0.75, fontSize: 16, color: K.suave, valign: "top", objectName: "Qué es" });
  s.addNotes("[0:00 – 0:05] Buenos días. " + (EQUIPO ? "Somos " + EQUIPO + " y esto" : "Esto") + " es Idóneo: tu perfil inversor, en una conversación." +
    nota(EQUIPO ? "" : " (Pendiente: decidir si se dice el nombre del equipo.)"));

  // =========================================================
  // 2 · Carmen: la casilla marcada ≠ lo que dijo
  // =========================================================
  s = nueva(BG.a);
  titulo(s, "El test se fía de lo que el cliente declara");
  texto(s, "Carmen · 68 años · 80.000 € en depósitos · caso simulado", { x: 0.7, y: 1.15, w: 8.6, h: 0.35, fontSize: 14, color: K.suave, valign: "middle", objectName: "Quién es Carmen" });
  // Izquierda: el test de casillas, con la pregunta y la respuesta marcada
  rotulo(s, "En el test marcó", 0.7, 1.75, 3.9);
  vidrio(s, "Tarjeta del test", 0.7, 2.15, 3.9, 2.4);
  texto(s, "¿Conoce los fondos de renta variable?", { x: 0.9, y: 2.3, w: 3.65, h: 0.45, fontFace: F.tit, fontSize: 14, valign: "middle", objectName: "Pregunta del test" });
  [["No los conozco", false], ["Un poco", false], ["Los conozco bien", true]].forEach(([t, marcada], i) => {
    const y = 2.92 + i * 0.56;
    if (marcada) vidrio(s, "Fila marcada (fondo)", 0.85, y - 0.08, 3.6, 0.56, { fill: { color: K.azul, transparency: 86 }, line: { color: K.azul, transparency: 40, width: 1 } });
    s.addShape(SH.roundRect, { x: 1.05, y: y + 0.06, w: 0.28, h: 0.28, rectRadius: 0.06, fill: marcada ? { color: K.azul } : { type: "none" }, line: { color: marcada ? K.azul : K.tenue, width: 1.25 }, objectName: "Casilla " + (i + 1) });
    if (marcada) s.addImage({ data: IC.check, x: 1.1, y: y + 0.11, w: 0.18, h: 0.18, altText: "marcada", objectName: "Marca de la casilla" });
    texto(s, t, { x: 1.48, y, w: 2.9, h: 0.4, fontFace: marcada ? F.tit : F.txt, fontSize: marcada ? 17 : 14, color: marcada ? K.tinta : K.tenue, valign: "middle", objectName: "Opción: " + t });
  });
  // Círculo con el degradado de la web (azul → violeta → rosa) en vez de ámbar
  s.addImage({ data: CIRCULO, x: 4.63, y: 3.0, w: 0.78, h: 0.78, altText: "círculo", objectName: "Símbolo distinto (círculo)" });
  texto(s, "≠", { x: 4.63, y: 3.0, w: 0.78, h: 0.78, fontFace: F.tit, fontSize: 32, color: K.oscuro, align: "center", valign: "middle", objectName: "Símbolo distinto" });
  // Derecha: la pregunta que le hacen en la conversación y lo que contesta (sin la pregunta, la cita no se entiende)
  rotulo(s, "En la conversación", 5.6, 1.75, 3.9, K.rosa);
  texto(s, "Le preguntan:", { x: 5.6, y: 2.15, w: 3.9, h: 0.3, fontSize: 14, color: K.tenue, valign: "middle", objectName: "Rótulo pregunta" });
  texto(s, "¿Un fondo de renta variable puede perder dinero?", { x: 5.6, y: 2.45, w: 3.9, h: 0.65, fontFace: F.tit, fontSize: 17, valign: "top", objectName: "Pregunta de la conversación" });
  texto(s, "Carmen responde:", { x: 5.6, y: 3.25, w: 3.9, h: 0.3, fontSize: 14, color: K.tenue, valign: "middle", objectName: "Rótulo respuesta" });
  texto(s, "«Eso no puede pasar, el fondo es del banco.»", { x: 5.6, y: 3.55, w: 3.9, h: 0.85, fontFace: F.tit, fontSize: 21, italic: true, color: K.rosa, valign: "top", lineSpacingMultiple: 0.98, objectName: "Cita de Carmen" });
  // Abajo: la conclusión, para que nadie tenga que deducirla
  texto(s, [{ text: "Dice que los conoce, ", options: { color: K.tinta } }, ...grad("pero no sabe que pueden perder dinero.", { fontFace: F.tit })],
    { x: 0.7, y: 4.8, w: 8.6, h: 0.45, fontSize: 18, align: "center", valign: "middle", objectName: "Conclusión" });
  s.addNotes("[0:05 – 0:38] Imaginad a Carmen. Tiene 68 años y 80.000 euros en depósitos. En el test MiFID de su banco marcó que conoce bien los fondos de renta variable. Pero cuando le preguntan si un fondo así podría perder dinero, dice: «eso no puede pasar, el fondo es del banco». Marcó una cosa y demostró la contraria. Y el test, que se fía de lo que ella declara, no lo detecta. Carmen es un caso simulado.");

  // =========================================================
  // 3 · Solución: tres palabras con su icono y el móvil
  // =========================================================
  s = nueva(BG.b);
  titulo(s, "Idóneo cambia el test por una conversación", { w: 5.6, h: 1.0, fontSize: 26 });
  [["Habla", "Por voz o por escrito, desde el móvil", B.mic], ["Comprueba", "Plantea casos y detecta contradicciones", B.buscar], ["Deja pruebas", "Guarda la frase que justifica cada dato", B.prueba]].forEach(([palabra, sub, img], i) => {
    const y = 1.6 + i * 1.18;
    s.addImage({ data: img, x: 0.7, y: y + 0.08, w: 0.6, h: 0.6, altText: palabra, objectName: "Icono: " + palabra });
    texto(s, palabra, { x: 1.55, y, w: 3.8, h: 0.6, fontFace: F.tit, fontSize: 30, valign: "middle", objectName: "Palabra: " + palabra });
    texto(s, sub, { x: 1.57, y: y + 0.6, w: 3.75, h: 0.4, fontSize: 15, color: K.suave, valign: "top", objectName: "Qué significa: " + palabra });
  });
  texto(s, "Pantalla real del prototipo", { x: 6.3, y: 5.27, w: 2.75, h: 0.28, fontSize: 12, color: K.tenue, align: "center", valign: "middle", objectName: "Qué es la captura" });
  s.addImage({ data: ESF.auraTenue, x: 5.05, y: 0.35, w: 4.9, h: 4.9, altText: "Brillo de la esfera", objectName: "Brillo detrás del móvil" });
  s.addShape(SH.roundRect, { x: 6.5, y: 0.42, w: 2.32, h: 4.82, rectRadius: 0.3, fill: { color: "0B0E1A" }, line: { color: "FFFFFF", transparency: 78, width: 1 }, shadow: { type: "outer", color: "000000", opacity: 0.5, blur: 24, offset: 6, angle: 90 }, objectName: "Marco del móvil" });
  s.addImage({ data: CAP.movil, x: 6.615, y: 0.535, w: 2.09, h: 4.52, altText: "Captura de la demo guiada en el móvil: el asistente pregunta si un fondo de renta variable podría perder dinero y Carmen contesta «Eso no puede pasar, el fondo es del banco»", objectName: "Captura de la entrevista" });
  s.addNotes("[0:38 – 1:08] Idóneo cambia el test por una conversación. Habla: el cliente contesta por voz o por escrito, desde el móvil. Comprueba: plantea escenarios y contrasta lo declarado con lo demostrado. Y deja pruebas: cada dato con su frase, su fuente y su versión" + v(ESTADO.audio, ", y su clip de audio.", ".") +
    " Nosotros no recomendamos productos: garantizamos que el agente de la entidad sabe quién es Carmen." + nota(v(ESTADO.voz, "", " (Pendiente: voz probada.)") + " (El móvil enseña la demo guiada de la app, con datos simulados.)"));

  // =========================================================
  // 4 · De la frase al dato: Alto → Ninguno
  // =========================================================
  s = nueva(BG.a);
  titulo(s, "Cada dato queda con su prueba");
  rotulo(s, "Carmen, en la conversación", 0.6, 1.55, 3.3, K.rosa);
  s.addShape(SH.roundRect, { x: 0.6, y: 1.95, w: 3.1, h: 1.55, rectRadius: 0.22, fill: { color: K.violeta, transparency: 80 }, line: { color: K.violeta, transparency: 45, width: 1 }, objectName: "Burbuja de Carmen (forma)" });
  texto(s, "«Eso no puede pasar, el fondo es del banco.»", { x: 0.85, y: 1.95, w: 2.65, h: 1.55, fontFace: F.tit, fontSize: 19, italic: true, valign: "middle", objectName: "Burbuja de Carmen" });
  s.addImage({ data: B.flecha, x: 3.95, y: 2.42, w: 0.6, h: 0.6, altText: "Claude lo extrae", objectName: "Flecha: Claude extrae" });
  texto(s, "La IA lo\nanaliza", { x: 3.75, y: 3.1, w: 1.0, h: 0.5, fontSize: 13, color: K.suave, align: "center", valign: "top", objectName: "Texto de la flecha" });
  rotulo(s, "Conocimiento de renta variable", 4.8, 1.55, 4.6);
  vidrio(s, "Tarjeta del dato", 4.8, 1.95, 4.6, 2.9, { fill: { color: "FFFFFF", transparency: 93 } });
  texto(s, "Declaró en el test", { x: 5.1, y: 2.1, w: 1.7, h: 0.3, fontSize: 13, color: K.tenue, valign: "middle", objectName: "Etiqueta declaró" });
  texto(s, "Alto", { x: 5.1, y: 2.35, w: 1.25, h: 0.75, fontSize: 32, color: K.tenue, strike: "sngStrike", valign: "middle", objectName: "Valor declarado" });
  s.addImage({ data: IC.flecha, x: 6.38, y: 2.58, w: 0.3, h: 0.3, altText: "flecha", objectName: "Flecha del dato" });
  texto(s, "Demostró hablando", { x: 6.85, y: 2.1, w: 2.3, h: 0.3, fontSize: 13, color: K.tenue, valign: "middle", objectName: "Etiqueta demostró" });
  texto(s, grad("Ninguno"), { x: 6.85, y: 2.35, w: 2.45, h: 0.75, fontFace: F.tit, fontSize: 34, valign: "middle", objectName: "Valor demostrado" });
  // El aviso usa el rosa de la web (no ámbar): mismo tono que la frase de Carmen
  s.addShape(SH.roundRect, { x: 5.1, y: 3.25, w: 4.0, h: 0.62, rectRadius: 0.16, fill: { color: K.rosa, transparency: 86 }, line: { color: K.rosa, transparency: 40, width: 1 }, objectName: "Alerta del dato (forma)" });
  s.addImage({ data: IC.aviso, x: 5.35, y: 3.4, w: 0.32, h: 0.32, altText: "aviso", objectName: "Icono de alerta" });
  texto(s, "Declarado ≠ demostrado", { x: 5.85, y: 3.25, w: 3.15, h: 0.62, fontFace: F.tit, fontSize: 17, color: K.rosa, valign: "middle", objectName: "Alerta del dato" });
  s.addImage({ data: IC.playClaro, x: 5.12, y: 4.12, w: 0.24, h: 0.24, altText: "prueba", objectName: "Icono de la prueba" });
  texto(s, "Prueba: su frase, en el minuto 0:57", { x: 5.48, y: 4.02, w: 3.7, h: 0.44, fontSize: 14, color: K.suave, valign: "middle", objectName: "Prueba del dato" });
  texto(s, "Así la entidad sabe de dónde sale cada dato del perfil.", { x: 0.6, y: 4.0, w: 3.9, h: 0.75, fontSize: 15, color: K.suave, valign: "top", objectName: "Para qué sirve" });
  s.addNotes("[1:08 – 1:38] Así se ve el paso clave. Carmen dice «eso no puede pasar». " + v(ESTADO.extractor, "Claude lo extrae mientras habla y lo compara con lo que declaró", "El sistema lo compara con lo que declaró") +
    ": había dicho alto, ha demostrado ninguno. El dato queda guardado con su fuente, la frase exacta y el minuto en que lo dijo. Con su tolerancia al riesgo pasa igual: declaró tres sobre cinco, demostró uno." + nota(v(ESTADO.extractor, "", " (Pendiente: extractor con Claude en directo.)")));

  // =========================================================
  // 5 · Lo que ve la entidad: la captura real, grande
  // =========================================================
  s = nueva(BG.c);
  titulo(s, "Lo que recibe la entidad");
  texto(s, "Calculado con reglas fijas en código, no por el modelo", { x: 0.7, y: 1.12, w: 8.6, h: 0.36, fontSize: 15, color: K.suave, valign: "middle", objectName: "Subtítulo" });
  const bw = 5.5, bh = bw * 841 / 1800, bx = 0.7, by = 1.8;
  s.addShape(SH.roundRect, { x: bx - 0.05, y: by - 0.05, w: bw + 0.1, h: bh + 0.1, rectRadius: 0.16, fill: { color: "FFFFFF", transparency: 90 }, line: { color: "FFFFFF", transparency: 75, width: 1 }, shadow: { type: "outer", color: "000000", opacity: 0.55, blur: 26, offset: 8, angle: 90 }, objectName: "Marco de la captura" });
  s.addImage({ data: CAP.entidad, x: bx, y: by, w: bw, h: bh, altText: "Captura de la vista de la entidad: carmen-68, perfil por validar, aviso declarado distinto de demostrado y botón Validar perfil", objectName: "Captura de la vista de la entidad" });
  // Derecha: las tres cosas que importan, con icono
  const claves = [
    [IC.escudo, [{ text: "Perfil conservador", options: { fontFace: F.tit, color: K.tinta } }, { text: "\nProductos hasta riesgo 3 de 7", options: { color: K.suave, fontSize: 13 } }]],
    [IC.nada, [{ text: "Renta variable: no", options: { fontFace: F.tit, color: K.tinta } }, { text: "\nNo demostró entenderla: no es conveniente", options: { color: K.suave, fontSize: 13 } }]],
    [IC.checkVerde, [{ text: "Lo valida una persona", options: { fontFace: F.tit, color: K.tinta } }, { text: "\nSi no, el agente no puede usarlo", options: { color: K.suave, fontSize: 13 } }]],
  ];
  texto(s, "Pantalla real del prototipo: vista de la entidad", { x: bx, y: by + bh + 0.12, w: bw, h: 0.3, fontSize: 12, color: K.tenue, align: "center", valign: "middle", objectName: "Qué es la captura" });
  claves.forEach(([ic, t], i) => {
    const y = by + i * 0.95;
    s.addImage({ data: ic, x: 6.6, y: y + 0.1, w: 0.36, h: 0.36, altText: "icono", objectName: "Icono clave " + (i + 1) });
    texto(s, t, { x: 7.12, y, w: 2.75, h: 0.8, fontSize: 17, valign: "top", objectName: "Clave " + (i + 1) });
  });
  s.addNotes("[1:38 – 2:10] Esto es lo que ve la entidad. Carmen es conservadora: riesgo máximo tres sobre siete. Sale de tres criterios y manda el más restrictivo, su tolerancia al riesgo. Y la conveniencia: los depósitos y la renta fija, sí; la renta variable, no. Todo lo calculan reglas fijas en código, no el modelo. Y hasta que una persona de la entidad lo valida, el agente no puede usarlo.");

  // =========================================================
  // 6 · Lo medido: tres cifras enormes
  // =========================================================
  s = nueva(BG.b);
  // Arriba: el aviso de ESMA, que justifica por qué hace falta comprobar
  texto(s, [
    { text: "ESMA avisa: ", options: { color: K.azul, fontFace: F.tit } },
    { text: "con sistemas automatizados, el cliente tiende más a ", options: { color: K.tinta } },
    ...grad("sobrevalorarse.", { fontFace: F.tit }),
  ], { x: 0.7, y: 0.5, w: 8.6, h: 1.05, fontSize: 24, valign: "middle", objectName: "Aviso de ESMA" });
  texto(s, "Directrices de ESMA (el supervisor europeo) sobre idoneidad, 2023, párrafo 52", { x: 0.7, y: 1.5, w: 8.6, h: 0.32, fontSize: 13, color: K.tenue, valign: "middle", objectName: "Fuente del aviso" });
  // Debajo: cómo responde Idóneo, con los tres papeles en una línea
  rotulo(s, "Por eso Idóneo comprueba, con tres piezas:", 0.7, 1.98, 8.6);
  [["Voz", "escucha", B.mic], ["Claude (IA)", "analiza", B.brain], ["Código", "hace las cuentas", B.calc]].forEach(([h, d, img], i) => {
    const x = 0.7 + i * 2.95;
    s.addImage({ data: img, x, y: 2.38, w: 0.44, h: 0.44, altText: h, objectName: "Icono: " + h });
    texto(s, [{ text: h + " ", options: { fontFace: F.tit, color: K.tinta } }, { text: d, options: { color: K.suave } }], { x: x + 0.56, y: 2.38, w: 2.6, h: 0.44, fontSize: 15, valign: "middle", objectName: "Rol: " + h });
  });
  if (METRICAS) {
    rotulo(s, "Lo que hemos medido:", 0.7, 3.05, 8.6);
    METRICAS.forEach((m, i) => {
      const cx = 0.5 + i * 3.05;
      texto(s, grad(m.n), { x: cx, y: 3.35, w: 2.95, h: 0.8, fontFace: F.tit, fontSize: 42, align: "center", valign: "middle", objectName: "Cifra " + (i + 1) });
      texto(s, m.t, { x: cx + 0.15, y: 4.15, w: 2.65, h: 0.6, fontSize: 14, color: K.suave, align: "center", valign: "top", objectName: "Qué mide " + (i + 1) });
    });
    texto(s, "Medido con clientes simulados y una repetición", { x: 0.7, y: 4.85, w: 8.6, h: 0.35, fontSize: 13, color: K.tenue, align: "center", valign: "middle", objectName: "Límite de la medida" });
  }
  // Sin métricas, la diapositiva se queda con el aviso de ESMA y los tres papeles (no se inventan cifras).
  s.addNotes("[2:10 – 2:58] ¿Por qué una IA? ESMA advierte de que con sistemas automatizados el riesgo de que el cliente se sobrevalore es mayor. Idóneo es el contrapeso. La voz, para que Carmen conteste hablando. Claude, que extrae cada dato y marca las contradicciones. Y código, que calcula los números, porque el modelo nunca calcula un número." +
    (METRICAS ? " Lo que hemos medido: el extractor acertó 31 de 31 datos en siete entrevistas; con Carmen, 10 de 10, y detectó la contradicción; y el asistente responde en 1,8 segundos de mediana, en la prueba por escrito. Con un límite que decimos claro: clientes simulados, una repetición y casos escritos por nosotros." + nota(" (Fuente: PLAN_Y_EVIDENCIAS, E-04 y E-05. Si cambian las METRICAS, cambiar también esta frase.)") : nota(" (Pendiente: impacto medido. Si no se mide, no se dice.)")));

  // =========================================================
  // 7 · Entra en vuestros agentes: el cauce, con iconos
  // =========================================================
  s = nueva(BG.centro);
  texto(s, "Se conecta a los agentes de IA de las entidades", { x: 0.5, y: 0.45, w: 9.0, h: 0.7, fontFace: F.tit, fontSize: 28, align: "center", valign: "middle", objectName: "Título" });
  texto(s, [{ text: "GPTadvisor protege lo que el agente responde. ", options: { color: K.suave } }, { text: "Idóneo, lo que recibe.", options: { color: K.tinta, fontFace: F.tit } }],
    { x: 0.7, y: 1.15, w: 8.6, h: 0.4, fontSize: 16, align: "center", valign: "middle", objectName: "Subtítulo" });
  const nodos = [
    ["Cliente", "Habla desde el móvil", B.movil, 0.95],
    ["Idóneo", "Perfil con pruebas", ESF.entidad, 1.5],
    ["Agente", "GPTadvisor, o Claude con MyInvestor", B.robot, 0.95],
    ["Propuesta", "La hace el agente, no Idóneo", B.propuesta, 0.95],
  ];
  const xc = [1.45, 3.85, 6.15, 8.55], yc = 2.75; // centros
  nodos.forEach(([h, d, img, tam], i) => {
    if (i === 1) s.addShape(SH.ellipse, { x: xc[i] - 1.15, y: yc - 0.38, w: 2.3, h: 0.76, fill: { type: "none" }, line: { color: K.violeta, transparency: 60, width: 0.75 }, objectName: "Órbita de Idóneo" });
    s.addImage({ data: img, x: xc[i] - tam / 2, y: yc - tam / 2, w: tam, h: tam, altText: h, objectName: "Icono: " + h });
    texto(s, h, { x: xc[i] - 1.1, y: yc + 0.85, w: 2.2, h: 0.42, fontFace: F.tit, fontSize: 19, align: "center", valign: "middle", objectName: "Nodo: " + h });
    texto(s, d, { x: xc[i] - 1.05, y: yc + 1.27, w: 2.1, h: 0.6, fontSize: 13, color: K.suave, align: "center", valign: "top", objectName: "Nodo texto: " + h });
    if (i < 3) s.addImage({ data: IC.flecha, x: (xc[i] + xc[i + 1]) / 2 - 0.13 + (i === 0 ? -0.12 : i === 1 ? 0.12 : 0), y: yc - 0.13, w: 0.26, h: 0.26, altText: "flecha", objectName: "Flecha " + (i + 1) });
  });
  pastilla(s, "MCP", [{ text: "por MCP", options: { color: K.verde, fontFace: F.tit } }], 4.5, yc - 0.85, 1.3, 0.42, "verde");
  texto(s, [{ text: "MCP: ", options: { color: K.verde, fontFace: F.tit } }, { text: "el estándar con el que los agentes de IA usan herramientas externas", options: { color: K.suave } }],
    { x: 0.5, y: 4.95, w: 9.0, h: 0.35, fontSize: 14, align: "center", valign: "middle", objectName: "Qué es MCP" });
  s.addNotes("[2:58 – 3:28] Y esto entra en los agentes que ya tenéis. GPTadvisor protege lo que su agente responde; Idóneo protege lo que su agente recibe. Se conecta por MCP, el estándar de los agentes de IA: el agente pide las restricciones de Carmen y recibe riesgo máximo tres y la renta variable como no conveniente. Nosotros no recomendamos: recomienda el agente de la entidad, y valida una persona." +
    nota(" (El MCP de MyInvestor solo se usa como conector dentro de Claude: sus términos no permiten otra cosa sin permiso. " + v(ESTADO.mcp, "Probado el 9/11 por un túnel temporal: hay que levantarlo antes de la demo.)", "Pendiente: URL pública de nuestro MCP.)")));

  // =========================================================
  // 8 · Cierre: la esfera, una frase y «demo en vivo»
  // =========================================================
  s = nueva(BG.centro);
  s.addShape(SH.ellipse, { x: 2.8, y: 1.0, w: 4.4, h: 0.8, fill: { type: "none" }, line: { color: K.violeta, transparency: 72, width: 0.75 }, objectName: "Órbita" });
  s.addImage({ data: ESF.aura, x: 3.7, y: 0.05, w: 2.6, h: 2.6, altText: "Esfera de Idóneo", objectName: "Esfera" });
  texto(s, "GPTadvisor hace fiable la recomendación.", { x: 0.5, y: 2.6, w: 9.0, h: 0.45, fontSize: 18, color: K.suave, align: "center", valign: "middle", objectName: "Frase 1" });
  texto(s, [{ text: "Idóneo hace fiable", options: { color: K.tinta, breakLine: true } }, ...grad("el perfil sobre el que se recomienda.")],
    { x: 0.5, y: 3.05, w: 9.0, h: 1.15, fontFace: F.tit, fontSize: 30, align: "center", valign: "middle", lineSpacingMultiple: 0.95, objectName: "Frase 2" });
  s.addShape(SH.roundRect, { x: 2.85, y: 4.5, w: 4.3, h: 0.55, rectRadius: 0.275, fill: { color: K.azul }, line: { color: K.azul, width: 0 }, shadow: { type: "outer", color: K.azul, opacity: 0.45, blur: 22, offset: 0, angle: 90 }, objectName: "Botón demo (forma)" });
  s.addImage({ data: IC.play, x: 3.15, y: 4.65, w: 0.24, h: 0.24, altText: "reproducir", objectName: "Icono de reproducir" });
  texto(s, "Demo en vivo · datos simulados", { x: 3.45, y: 4.5, w: 3.6, h: 0.55, fontFace: F.tit, fontSize: 15, color: K.oscuro, align: "center", valign: "middle", objectName: "Botón demo" });
  s.addNotes("[3:28 – 3:45] Un límite claro: los datos de Carmen son simulados y el perfil queda en borrador hasta que una persona lo valida. GPTadvisor hace fiable la recomendación. Idóneo hace fiable el perfil sobre el que se recomienda. Vamos a verlo." + nota(" (Cambiar a la app: demo en vivo de 2:15; plan B en DEMO_GUION.md.)"));

  await pres.writeFile({ fileName: OUT });
  await retocarArchivo(OUT);
  console.log("OK", FINAL ? "(FINAL)" : "(TRABAJO)", OUT, JSON.stringify(ESTADO));
}
main().catch((e) => { console.error(e); process.exit(1); });
