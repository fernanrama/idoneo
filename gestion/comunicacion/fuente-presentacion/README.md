# Fuente de la presentación

Genera `../Idoneo_presentacion.pptx`: 8 diapositivas, notas del orador con el guion y transición de fundido.
El texto hablado vive en [`../PITCH_GUION.md`](../PITCH_GUION.md) y debe coincidir con las notas.

## Requisitos

Node 18 o superior. Una sola vez: `npm install` (instala pptxgenjs, sharp, react y react-icons).

## Uso

```bash
node build.js ../Idoneo_presentacion.pptx                 # VERSIÓN DE TRABAJO: etiquetas ámbar donde falta algo
node build.js ../Idoneo_presentacion.pptx --final         # VERSIÓN FINAL: sin etiquetas; lo pendiente pasa a «siguiente paso»
node build.js ../Idoneo_presentacion.pptx --final --hecho=voz,extractor,audio   # marca como hecho lo que ya funciona
```

## Antes de la entrega (miércoles, congelar a las 18:00)

1. Decidir para cada cosa si **funciona de verdad** y añadirla a `--hecho=`:
   - `voz`: la entrevista por voz con ElevenLabs funciona de punta a punta.
   - `extractor`: Claude rellena el perfil mientras el cliente habla.
   - `audio`: al pulsar un dato suena su clip.
2. Si hay **métricas medidas** (tiempo frente a un formulario, contradicciones detectadas, latencia), rellenar
   `METRICAS` en `build.js`. Sin datos, la versión final no enseña ese panel.
3. **Cerrar PowerPoint** antes de generar: Windows bloquea el archivo mientras está abierto.
4. Abrir el `.pptx` resultante, pasar las 8 diapositivas y comprobar que **ninguna** dice algo que no funcione.

## Reglas

- No se ponen en pantalla los valores de «confianza» del perfil: son de ejemplo (la rúbrica no está implementada).
- Sin logos de terceros: solo los nombres (ElevenLabs, Claude, MyInvestor, GPTadvisor).
- Carmen y todos sus datos son **simulados** y así se dice en la presentación.
- Colores del tema de la app (`frontend/src/tema/tema.css`).
