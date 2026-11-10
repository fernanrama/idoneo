"use client";

import { useEffect, useRef } from "react";

/**
 * Esfera de plasma en 3D dibujada con un shader (WebGL, sin librerías ni imágenes).
 * Es la pieza visual común del producto: el aura del entrevistador, la esfera del perfil del cliente
 * y la de la vista de la entidad. La energía, la velocidad y los colores cambian con suavidad.
 * Se detiene fuera de pantalla y, con «reducir movimiento», pinta un único fotograma.
 * Si el navegador no tiene WebGL no pinta nada y se ve el respaldo en CSS que haya debajo.
 */
export type Paleta = [string, string, string];
export interface AjustesEsfera {
  paleta: Paleta;
  /** Velocidad del remolino (1 = normal). */
  velocidad?: number;
  /** Cuánto se retuerce el plasma (0 a 1,5). */
  energia?: number;
  /** 0 = gris, 1 = color pleno. */
  color?: number;
  /** Late con el ritmo de la voz. */
  pulso?: number;
}

const VERT = "attribute vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }";

const FRAG = `
precision highp float;
uniform vec2 uRes; uniform float uT; uniform float uAmp; uniform float uSat; uniform float uPulso;
uniform vec3 uA; uniform vec3 uB; uniform vec3 uC; uniform vec2 uRaton;

vec4 perm(vec4 x){ return mod(((x * 34.0) + 1.0) * x, 289.0); }
float ruido(vec3 p){
  vec3 a = floor(p); vec3 d = p - a; d = d * d * (3.0 - 2.0 * d);
  vec4 b = a.xxyy + vec4(0.0, 1.0, 0.0, 1.0);
  vec4 k1 = perm(b.xyxy); vec4 k2 = perm(k1.xyxy + b.zzww);
  vec4 c = k2 + a.zzzz; vec4 k3 = perm(c); vec4 k4 = perm(c + 1.0);
  vec4 o1 = fract(k3 / 41.0); vec4 o2 = fract(k4 / 41.0);
  vec4 o3 = o2 * d.z + o1 * (1.0 - d.z);
  vec2 o4 = o3.yw * d.x + o3.xz * (1.0 - d.x);
  return o4.y * d.y + o4.x * (1.0 - d.y);
}
float fbm(vec3 p){
  float v = 0.0; float a = 0.5;
  for (int i = 0; i < 4; i++) { v += a * ruido(p); p = p * 2.03 + vec3(11.3, 4.7, 7.1); a *= 0.5; }
  return v;
}
mat2 giro(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }

void main(){
  vec2 p = (gl_FragCoord.xy * 2.0 - uRes) / min(uRes.x, uRes.y);
  p *= 1.04 + 0.02 * uPulso * sin(uT * 9.0);
  float r = length(p);
  if (r > 1.0) { gl_FragColor = vec4(0.0); return; }
  float z = sqrt(1.0 - r * r);
  vec3 n = vec3(p, z);
  vec3 q = n;
  q.xz = giro(uT * 0.22 + uRaton.x * 0.5) * q.xz;
  q.yz = giro(0.35 + uRaton.y * 0.4) * q.yz;
  q *= 0.95;

  // Remolino: el ruido se deforma a sí mismo dos veces
  vec3 w1 = vec3(fbm(q + vec3(0.0, 0.0, uT * 0.30)), fbm(q + vec3(5.2, 1.3, -uT * 0.26)), fbm(q + vec3(2.1, 7.7, uT * 0.22)));
  vec3 q2 = q + uAmp * 2.4 * (w1 - 0.5);
  float f = fbm(q2 * 1.25 + vec3(0.0, uT * 0.12, 0.0));
  float g = fbm(q2 * 2.0 - vec3(uT * 0.18, 0.0, 0.0));

  vec3 col = mix(uA, uB, smoothstep(0.22, 0.74, f));
  col = mix(col, uC, smoothstep(0.42, 0.9, g) * 0.8);
  // Filamentos de luz donde el remolino se pliega
  float hilo = pow(1.0 - abs(f - 0.5) * 2.0, 7.0);
  col += hilo * 0.28 * mix(uC, vec3(1.0), 0.5);
  // Profundidad: centro más denso, borde encendido (fresnel)
  float fres = pow(1.0 - z, 2.2);
  col *= 0.7 + 0.3 * z + 0.25 * uPulso * (0.5 + 0.5 * sin(uT * 9.0));
  col += fres * mix(uB, vec3(1.0), 0.35) * 0.8;
  // Brillos de cristal
  vec3 luz = normalize(vec3(-0.55, 0.62, 0.56));
  float e = max(dot(n, luz), 0.0);
  col += pow(e, 48.0) * 0.95 + pow(e, 7.0) * 0.16;
  float abajo = max(dot(n, normalize(vec3(0.5, -0.7, 0.5))), 0.0);
  col += pow(abajo, 14.0) * 0.18 * uC;

  float gris = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gris) * 0.75, col, uSat);
  float alfa = smoothstep(1.0, 0.975, r);
  gl_FragColor = vec4(col * alfa, alfa);
}`;

const rgb = (hex: string): [number, number, number] => {
  const n = parseInt(hex.slice(1), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
};

export function Esfera3D({ paleta, velocidad = 1, energia = 0.6, color = 1, pulso = 0, className, style }: AjustesEsfera & { className?: string; style?: React.CSSProperties }) {
  const lienzo = useRef<HTMLCanvasElement>(null);
  // El objetivo se lee en cada fotograma; así los cambios de estado se funden sin reiniciar el shader.
  const objetivo = useRef({ paleta, velocidad, energia, color, pulso });
  useEffect(() => {
    objetivo.current = { paleta, velocidad, energia, color, pulso };
  }, [paleta, velocidad, energia, color, pulso]);

  useEffect(() => {
    const c = lienzo.current;
    if (!c) return;
    const gl = c.getContext("webgl", { premultipliedAlpha: true, antialias: false, powerPreference: "low-power" });
    if (!gl) return;
    const compilar = (tipo: number, codigo: string) => {
      const sh = gl.createShader(tipo)!;
      gl.shaderSource(sh, codigo);
      gl.compileShader(sh);
      return sh;
    };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, compilar(gl.VERTEX_SHADER, VERT));
    gl.attachShader(prog, compilar(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(prog, "p");
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);
    const u = (n: string) => gl.getUniformLocation(prog, n);
    const U = { res: u("uRes"), t: u("uT"), amp: u("uAmp"), sat: u("uSat"), pulso: u("uPulso"), a: u("uA"), b: u("uB"), c: u("uC"), raton: u("uRaton") };
    c.dataset.listo = "1";

    const o = objetivo.current;
    const v = { vel: o.velocidad, amp: o.energia, sat: o.color, pulso: o.pulso, col: o.paleta.map(rgb), mx: 0, my: 0 };
    const raton = { x: 0, y: 0 };
    let t = Math.random() * 40;
    let antes = 0;
    let marco = 0;
    let visible = true;
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const medir = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.round(c.clientWidth * dpr));
      const h = Math.max(1, Math.round(c.clientHeight * dpr));
      if (c.width !== w || c.height !== h) {
        c.width = w;
        c.height = h;
        gl.viewport(0, 0, w, h);
      }
    };
    const pintar = (ahora: number) => {
      const dt = Math.min((ahora - antes) / 1000 || 0, 0.05);
      antes = ahora;
      const ob = objetivo.current;
      const k = 1 - Math.exp(-dt * 4); // suavizado independiente de los fotogramas
      v.vel += (ob.velocidad - v.vel) * k;
      v.amp += (ob.energia - v.amp) * k;
      v.sat += (ob.color - v.sat) * k;
      v.pulso += (ob.pulso - v.pulso) * k;
      ob.paleta.map(rgb).forEach((d, i) => d.forEach((x, j) => (v.col[i][j] += (x - v.col[i][j]) * k)));
      v.mx += (raton.x - v.mx) * k;
      v.my += (raton.y - v.my) * k;
      t += dt * v.vel;
      medir();
      gl.uniform2f(U.res, c.width, c.height);
      gl.uniform1f(U.t, t);
      gl.uniform1f(U.amp, v.amp);
      gl.uniform1f(U.sat, v.sat);
      gl.uniform1f(U.pulso, v.pulso);
      gl.uniform3fv(U.a, v.col[0]);
      gl.uniform3fv(U.b, v.col[1]);
      gl.uniform3fv(U.c, v.col[2]);
      gl.uniform2f(U.raton, v.mx, v.my);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (visible && !quieto) marco = requestAnimationFrame(pintar);
    };
    const arrancar = () => {
      cancelAnimationFrame(marco);
      antes = performance.now();
      marco = requestAnimationFrame(pintar);
    };

    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible) arrancar();
      else cancelAnimationFrame(marco);
    });
    io.observe(c);
    const mover = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      raton.x = (e.clientX / window.innerWidth) * 2 - 1;
      raton.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener("pointermove", mover, { passive: true });
    arrancar();
    return () => {
      cancelAnimationFrame(marco);
      io.disconnect();
      window.removeEventListener("pointermove", mover);
    };
  }, []);

  return <canvas ref={lienzo} className={className} style={{ display: "block", width: "100%", height: "100%", ...style }} aria-hidden="true" />;
}
