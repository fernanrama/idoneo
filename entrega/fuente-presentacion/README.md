# Fuente de la presentación

Genera `../Idoneo_presentacion.pptx`: **9 diapositivas técnicas** (la última, de reserva para las preguntas) con la marca de idóneo (fondo noche, degradado menta → turquesa, tipografía Sora; ver [`docs/marca/`](../../docs/marca/README.md)). Lo que se dice está en las notas del orador de cada diapositiva.

El pitch abre con el **vídeo** (problema, solución y cómo funciona). Estas diapositivas van **después** y cuentan lo que el vídeo no puede:

| # | Mensaje |
|---|---|
| 1 | Portada: logo y lema «Invertir empieza por escucharte» |
| 2 | Cómo funciona por dentro: conversación → extractor → guardas y rúbrica → perfil con pruebas → validación humana → agente de la entidad |
| 3 | Cada dato, con su prueba: Carmen, declarado frente a demostrado |
| 4 | Lo que recibe el asesor: perfil conservador, conveniencia y validación |
| 5 | Dentro de la app de cada entidad: alta, microentrevistas, perfil vivo, sello «Powered by idóneo» y MCP |
| 6 | Frente al test de casillas: 0 de 5 frente a 5 de 5, con su límite (clientes simulados) |
| 7 | Lo que cuesta preguntar bien: coste por entrevista, coste con un asesor y una multa pública de la CNMV |
| 8 | Cierre con dos peticiones y paso a la demo en vivo |
| 9 | Reserva: lo que hemos medido (31/31, 70/70, 0 falsas alarmas y 43 s) |

**Regla de diseño: solo el texto necesario.** Cada diapositiva lleva su mensaje (título), el dibujo y los rótulos justos para entenderla. Lo que se cuenta con detalle va en las notas.

## Requisitos

- Node 18 o superior. Una sola vez: `npm install` (pptxgenjs, sharp, react y react-icons).
- Tipografía **Sora** instalada en el equipo que **proyecta** (Google Fonts, gratuita; en Windows: clic derecho en cada `.ttf` → «Instalar»). Si se presenta desde otro equipo sin Sora, exportar antes a PDF desde PowerPoint.
- El logo y el sello se leen de `docs/marca/` (PNG).

## Uso

```bash
node build.js ../Idoneo_presentacion.pptx            # TRABAJO: notas con avisos «(Pendiente: …)»
node build.js ../Idoneo_presentacion.pptx --final    # FINAL: notas limpias
```

**Cierra PowerPoint antes de generar:** Windows bloquea el archivo abierto.

En `build.js` se editan a mano `EQUIPO` (solo se dice en voz alta) y las cifras de las diapositivas 6, 7 y 9. Las de la 6 y la 9 salen de [`docs/evaluacion/README.md`](../../docs/evaluacion/README.md); las de la 7, con sus fuentes y lo que falta por sustituir, están en [`docs/pitch.md`](../../docs/pitch.md).

## Resumen de una cara

`../Idoneo_una_cara.html` es la fuente de `../Idoneo_una_cara.pdf` (A4, una página). Para regenerar el PDF con Chrome:

```bash
chrome --headless=new --no-pdf-header-footer --virtual-time-budget=5000 --print-to-pdf=Idoneo_una_cara.pdf "file:///…/entrega/Idoneo_una_cara.html"
```

## Recursos (`assets/`)

- `entidad_carmen.jpg`: vista de la entidad (`/entidad/carmen-68`), perfil por validar con el aviso. Si cambia el diseño de la web, rehacer la captura para que el jurado vea lo mismo en la demo.
- `entrevista_movil_noche.jpg`, `esfera_*.png` y `esfera.html`: recursos de la versión anterior (estilo «noche»); se conservan por si se recuperan.

## Reglas

- No se ponen en pantalla los valores de «confianza» del perfil (son supuestos del equipo).
- Sin logos de terceros: solo los nombres (ElevenLabs, Claude, MyInvestor, GPTadvisor).
- Carmen y todos sus datos son **simulados**, y así se dice.
- Ningún precio: idóneo se presenta como una función integrada en la app de la entidad. La diapositiva 7 enseña **costes** y una multa pública, no lo que cobraría idóneo.
