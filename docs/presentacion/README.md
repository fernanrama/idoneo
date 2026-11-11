# Fuente de la presentación y del resumen de una cara

Genera `Idoneo_presentacion.pptx` (en esta carpeta): **7 diapositivas técnicas** con la marca de idóneo (fondo noche, degradado menta → turquesa, tipografía Sora; ver [`docs/marca/`](../../docs/marca/README.md)). Lo que se dice está en las notas del orador de cada diapositiva.

El pitch abre con el **vídeo** (problema, solución y cómo funciona). Estas diapositivas van **después** y cuentan lo que el vídeo no puede:

| # | Mensaje |
|---|---|
| 1 | Portada: logo y lema «Invertir empieza por escucharte» |
| 2 | Cómo funciona por dentro: conversación → extractor → guardas y rúbrica → perfil con pruebas → validación humana → agente de la entidad |
| 3 | Cada dato, con su prueba: Carmen, declarado frente a demostrado |
| 4 | Lo que recibe el asesor: perfil conservador, conveniencia y validación |
| 5 | Dentro de la app de cada entidad: alta, microentrevistas, perfil vivo, sello «Powered by idóneo» y MCP |
| 6 | Lo que hemos medido, con su límite (clientes simulados) |
| 7 | Cierre y paso a la demo en vivo |

**Regla de diseño: solo el texto necesario.** Cada diapositiva lleva su mensaje (título), el dibujo y los rótulos justos para entenderla. Lo que se cuenta con detalle va en las notas.

## Requisitos

- Node 18 o superior. Una sola vez: `npm install` (pptxgenjs, sharp, react y react-icons).
- Tipografía **Sora** instalada en el equipo que **proyecta** (Google Fonts, gratuita; en Windows: clic derecho en cada `.ttf` → «Instalar»). Si se presenta desde otro equipo sin Sora, exportar antes a PDF desde PowerPoint.
- El logo y el sello se leen de `docs/marca/` (PNG).

## Uso

```bash
node build.js Idoneo_presentacion.pptx            # TRABAJO: notas con avisos «(Pendiente: …)»
node build.js Idoneo_presentacion.pptx --final    # FINAL: notas limpias
```

**Cierra PowerPoint antes de generar:** Windows bloquea el archivo abierto.

En `build.js` se editan a mano `EQUIPO` (solo se dice en voz alta) y las cifras de la diapositiva 6, que salen de [`docs/evaluacion/README.md`](../../docs/evaluacion/README.md).

## Versión HTML animada (`entrega/Idoneo_presentacion.html`)

Un solo archivo que se abre con doble clic en cualquier navegador y **funciona sin internet**: lleva dentro las fuentes (Sora e IBM Plex Mono, licencia OFL), el logo, el sello y la captura. Pensado para proyector: el lienzo es 1920 × 1080 y se escala a la pantalla.

| Tecla | Qué hace |
|---|---|
| → · espacio · clic | Siguiente paso o diapositiva (muchas se construyen por pasos) |
| ← | Paso o diapositiva anterior |
| F | Pantalla completa |
| N | Notas del orador abajo |
| S | Sonido suave al avanzar (apagado por defecto, no hace falta) |
| Inicio / Fin | Primera / última |

Orden: portada → **parte de Alex** (cómo funciona, el mapa completo por dentro, harness, memoria, LLMOps, lo que mejoró y laboratorio) → las diapositivas de siempre (cada dato con su prueba, lo que recibe el asesor, dentro de la app, lo que hemos medido, cierre). El guion de cada una va en las notas (tecla N). Se puede saltar a una diapositiva con `#número` al final de la URL.

Las cifras salen de [`docs/evaluacion/`](../../docs/evaluacion/README.md): las del laboratorio (20 entrevistas, 1.280 llamadas a Claude, 165 de 166 datos) son la suma de los dos informes de [`docs/evaluacion/laboratorio/e07/`](../../docs/evaluacion/laboratorio/e07/). Si hay una tirada nueva, se cambian a mano en `html/deck.html`.

Regenerar tras editar `html/deck.html`:

```bash
python docs/presentacion/html/generar.py   # desde la raíz del repo
```

## Resumen de una cara

`Idoneo_una_cara.html` es la fuente de `entrega/Idoneo_una_cara.pdf` (A4, una página). Para regenerar el PDF con Chrome:

```bash
chrome --headless=new --no-pdf-header-footer --virtual-time-budget=5000 --print-to-pdf=../../entrega/Idoneo_una_cara.pdf "file:///…/docs/presentacion/Idoneo_una_cara.html"
```

## Recursos (`assets/`)

- `entidad_carmen.jpg`: vista de la entidad (`/entidad/carmen-68`), perfil por validar con el aviso. Si cambia el diseño de la web, rehacer la captura para que el jurado vea lo mismo en la demo.
- `entrevista_movil_noche.jpg`, `esfera_*.png` y `esfera.html`: recursos de la versión anterior (estilo «noche»); se conservan por si se recuperan.

## Reglas

- No se ponen en pantalla los valores de «confianza» del perfil (son supuestos del equipo).
- Sin logos de terceros: solo los nombres (ElevenLabs, Claude, MyInvestor, GPTadvisor).
- Carmen y todos sus datos son **simulados**, y así se dice.
- Ningún precio: idóneo se presenta como una función integrada en la app de la entidad.
