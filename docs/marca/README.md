# Identidad de marca de idóneo

idóneo se integra dentro de la app de cada entidad, así que se presenta como un sello: **Powered by idóneo**. Dentro de la app anfitriona mandan sus colores y su tipografía; idóneo firma pequeño, al pie del módulo.

Guía completa en una página: [guia-de-marca.pdf](guia-de-marca.pdf).

## Archivos

| Uso | SVG (web) | PNG (presentaciones) |
|---|---|---|
| Logo sobre fondo oscuro | [`idoneo-logo-sobre-oscuro.svg`](../../frontend/public/marca/idoneo-logo-sobre-oscuro.svg) | [`idoneo-logo-sobre-oscuro.png`](idoneo-logo-sobre-oscuro.png) |
| Logo sobre fondo claro | [`idoneo-logo-sobre-claro.svg`](../../frontend/public/marca/idoneo-logo-sobre-claro.svg) | [`idoneo-logo-sobre-claro.png`](idoneo-logo-sobre-claro.png) |
| Logo a una tinta (negro o blanco) | [`idoneo-logo-negro.svg`](../../frontend/public/marca/idoneo-logo-negro.svg), [`idoneo-logo-blanco.svg`](../../frontend/public/marca/idoneo-logo-blanco.svg) | [`idoneo-logo-negro.png`](idoneo-logo-negro.png), [`idoneo-logo-blanco.png`](idoneo-logo-blanco.png) |
| Icono (favicon, avatar) | [`idoneo-icono-app.svg`](../../frontend/public/marca/idoneo-icono-app.svg) | [512](idoneo-icono-app-512.png), [180](idoneo-icono-app-180.png), [32](idoneo-icono-app-32.png) |
| Sello «Powered by idóneo» | [`powered-by-idoneo-claro.svg`](../../frontend/public/marca/powered-by-idoneo-claro.svg), [`-oscuro`](../../frontend/public/marca/powered-by-idoneo-oscuro.svg), [`-gris`](../../frontend/public/marca/powered-by-idoneo-gris.svg) | [`powered-by-idoneo-claro.png`](powered-by-idoneo-claro.png) |

En la web, los SVG se sirven desde `/marca/…` (por ejemplo, `<img src="/marca/powered-by-idoneo-claro.svg">`). Las letras están convertidas a trazos: no hace falta tener la tipografía instalada.

## Color

| Nombre | Valor | Uso |
|---|---|---|
| Noche | `#0C1A1F` | Fondos oscuros y texto principal |
| Turquesa | `#2BB3C0` | Color de marca sobre fondo claro (botones, enlaces) |
| Menta | `#7CE7C4` | Solo sobre fondo oscuro y en el degradado |
| Blanco niebla | `#F7FBFA` | Fondos claros |
| Degradado Aurora | `#7CE7C4 → #2BB3C0` | Acentos |

Verde `#1F9D6B`, ámbar `#D99A1E` y rojo `#D64545` quedan **reservados para estados** (encaja, revisar, no encaja); nunca como color de marca.

## Tipografía

[Sora](https://fonts.google.com/specimen/Sora) (Google Fonts, licencia OFL): 600 en titulares, 400 en texto. IBM Plex Mono para etiquetas técnicas.

## Reglas

- El logo va siempre en minúsculas. El acento de la «ó» es una onda de audio (la IA que escucha); no se sustituye por una tilde normal.
- Margen libre alrededor: como mínimo, la altura de la «o». Por debajo de 80 px de ancho, usar el icono.
- No deformar, rotar ni recolorear el logo. No usar la menta como texto sobre blanco.
