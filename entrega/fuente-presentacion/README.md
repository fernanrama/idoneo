# Fuente de la presentación

Genera `../Idoneo_presentacion.pptx`: 8 diapositivas con el estilo «noche» de la web (fondo oscuro, brillos
azul-violeta-rosa, tarjetas de vidrio y la esfera 3D), notas del orador con el guion y fundido.
El texto hablado está en las notas del orador de cada diapositiva.

**Regla de diseño: solo el texto necesario.** Cada diapositiva lleva su mensaje (título), la imagen y los rótulos
que hacen falta para entenderla. Nada de pies de página, números, etiquetas decorativas ni párrafos. Lo que se
cuenta con detalle va a las notas. Antes de añadir una frase: ¿sin ella se entiende la diapositiva?

## Requisitos

Node 18 o superior. Una sola vez: `npm install` (pptxgenjs, sharp, react y react-icons).
Letras: Segoe UI y Consolas (vienen en Windows). En un Mac PowerPoint las cambia: **presentar desde Windows**
o exportar a PDF antes.

## Uso

```bash
node build.js ../Idoneo_presentacion.pptx --hecho=voz,extractor,mcp            # TRABAJO: notas con avisos «(Pendiente: …)»
node build.js ../Idoneo_presentacion.pptx --final --hecho=voz,extractor,mcp    # FINAL: notas limpias
```

`--hecho=` marca lo que **funciona de verdad** (a 10/11, comprobado en `docs/evaluacion/README.md`):

| Clave | Qué significa | Estado 10/11 |
|---|---|---|
| `voz` | Entrevista por voz con ElevenLabs de punta a punta | Hecho (E-03, una vez) |
| `extractor` | Claude rellena el perfil mientras el cliente habla | Hecho (E-04, E-05) |
| `mcp` | Claude lee el perfil por nuestro MCP | Hecho por túnel temporal el 9/11, antes de la PR 21 (el MCP exige ahora credencial: revisar la conexión) |
| `audio` | Al pulsar un dato suena su clip | Pendiente |

## Qué se edita a mano en `build.js`

- `EQUIPO`: nombre del equipo. No sale en la portada; solo en las notas («Somos …»).
- `METRICAS`: cifras medidas (de E-04 y E-05) con 2-3 palabras cada una. Si sale el laboratorio de ~20 clientes,
  cambiarlas aquí **y** la frase de las notas de la diapositiva 6. En pantalla va siempre «Clientes simulados».

## Recursos (`assets/`)

- `esfera_*.png`: la esfera 3D, pintada con **el mismo shader de la web** (`esfera.html`, copia de
  `frontend/src/components/Esfera3D.tsx`) con Edge sin ventana:
  `msedge --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --default-background-color=00000000 --window-size=1000,1000 --screenshot=esfera.png "file:///…/esfera.html?p=1f3bff,8a5cff,ff7fd1&t=7.3"`
- `entrevista_movil_noche.jpg`: demo guiada en el móvil (390×844), paso 14 de 19, la frase de Carmen.
- `entidad_carmen.jpg`: vista de la entidad (`/entidad/carmen-68`), perfil por validar con el aviso.

Si cambia el diseño de la web, **rehacer las capturas** para que el jurado vea lo mismo en la demo.

## Antes de la entrega (miércoles, congelar a las 18:00)

1. Revisar `--hecho=`, `EQUIPO` y `METRICAS`.
2. **Cerrar PowerPoint** antes de generar: Windows bloquea el archivo abierto.
3. Generar la versión final, abrirla y pasar las 8 diapositivas: **ninguna** dice algo que no funcione.

## Reglas

- No se ponen en pantalla los valores de «confianza» del perfil (son supuestos del equipo).
- Sin logos de terceros: solo los nombres (ElevenLabs, Claude, MyInvestor, GPTadvisor).
- Carmen y todos sus datos son **simulados** y así se dice en la presentación.
