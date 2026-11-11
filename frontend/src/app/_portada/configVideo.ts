/**
 * Vídeo de presentación de la portada. Para publicarlo basta con rellenar UNA de las dos opciones:
 * - `mp4`: ruta de un archivo servido por el propio front (por ejemplo "/video/idoneo.mp4", en `public/video/`).
 * - `embed`: dirección de incrustación de una plataforma de vídeo (la que va en el `src` de un iframe).
 * Con las dos en `null`, la portada enseña un cartel que lleva a la demo guiada.
 */
export const VIDEO: { mp4: string | null; embed: string | null; poster: string | null } = {
  mp4: null,
  embed: null,
  poster: null,
};
