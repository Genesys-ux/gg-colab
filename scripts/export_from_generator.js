/**
 * Export neutral humanoid character design presets (.json) and self-contained Python components (.py)
 * directly using C:\Users\lutfi\Downloads\122\generator.html's engine
 * (character-engine.js + python-engine-core.js + python-exporter.js).
 *
 * Catatan: Semua preset didesain dalam pose & ekspresi NETRAL (defaultAnimation: 'static')
 * agar rigging TIDAK terkunci dan bebas disesuaikan untuk setiap adegan.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const GEN_DIR = 'C:\\Users\\lutfi\\Downloads\\122';
const PROJECT_DIR = 'C:\\Users\\lutfi\\Downloads\\py nem';
const CHAR_DIR = path.join(PROJECT_DIR, 'characters');
const PRESET_DIR = path.join(CHAR_DIR, 'presets');

fs.mkdirSync(PRESET_DIR, { recursive: true });

function loadScript(file) {
  const code = fs.readFileSync(path.join(GEN_DIR, file), 'utf8');
  vm.runInThisContext(code, { filename: file });
}

loadScript('character-engine.js');
loadScript('prompt-engine.js');
loadScript('python-engine-core.js');
loadScript('python-exporter.js');

const { DEFAULT_CONFIG } = globalThis.CharacterEngine;
const { generatePythonComponent } = globalThis.PythonExporter;

// 1. BIMA — Protagonis (Magang Tukang Jam, 13 tahun) — Desain Dasar Netral
const BIMA_CONFIG = {
  ...DEFAULT_CONFIG,
  name: 'Bima',
  prompt:
    'Bima bocah magang tukang jam 13 tahun, jaket parka pendek kanvas kuning kunyit #F2B705 dengan 4 saku kargo, kacamata loupe kuningan #B8860B tali kulit bertengger di dahi, syal merah bata #C84B31 menjuntai, sabuk kulit kantong alat, celana kargo biru dongker #2B3A55, rambut cokelat tua chunky',
  headShape: 'potato',
  skinColor: '#F5D6BA',
  blushColor: '#DFA88E',
  eyes: 'focused',
  eyebrows: 'raised',
  mouth: 'smirk',
  beard: 'none',
  faceAccessory: 'goggles',
  sweatDrop: false,
  blush: false,
  angerVein: false,
  eyeGazeX: 0.0,
  eyeGazeY: 0.0,
  hat: 'none',
  hatPrimary: '#4A2C1D',
  hatAccent: '#B8860B',
  hatTilt: 0,
  hatLiftY: 0,
  backHair: 'spiky',
  hairColor: '#4A2C1D',
  outfit: 'safari_explorer',
  robeColor: '#F2B705',
  innerColor: '#EFE4CC',
  sashColor: '#5B3822',
  trimColor: '#B8860B',
  beltStyle: 'utility_belt',
  cape: 'scarf',
  capeColor: '#C84B31',
  emblem: 'none',
  pose: 'ready',
  prop: 'none',
  limbColor: '#2B3A55',
  groundShadow: true,
  outlineShadow: 1.0,
  outlineLit: 0.9,
  rimIntensity: 1.15,
  shadowDepth: 1.08,
  customLayers: [],
};

// 2. PEDAGANG REMPAH — Figuran Pasar Bertingkat (Lokasi 2) — Desain Dasar Netral
// Aturan: Siluet bulat/gempal, apron kain goni, topi jerami lebar, DILARANG kuning saffron!
const PEDAGANG_REMPAH_CONFIG = {
  ...DEFAULT_CONFIG,
  name: 'Pedagang Rempah',
  prompt:
    'Pedagang rempah pasar bertingkat berbadan bulat gempal, topi jerami lebar, apron kain goni krem, baju teal pasar, sabuk marun, kumis tebal, pose desain netral',
  headShape: 'pear',
  skinColor: '#DFB086',
  blushColor: '#C98A68',
  eyes: 'chill',
  eyebrows: 'happy',
  mouth: 'smirk',
  beard: 'handlebar',
  faceAccessory: 'none',
  sweatDrop: false,
  blush: false,
  angerVein: false,
  eyeGazeX: 0.0,
  eyeGazeY: 0.0,
  hat: 'cowboy',
  hatPrimary: '#C5A265',
  hatAccent: '#7C2B36',
  hatTilt: 0,
  hatLiftY: 0,
  backHair: 'curly',
  hairColor: '#36261E',
  outfit: 'chef_apron',
  robeColor: '#2A6A6C',
  innerColor: '#D6C098',
  sashColor: '#7C2B36',
  trimColor: '#9E7442',
  beltStyle: 'knot',
  cape: 'none',
  capeColor: '#7C2B36',
  emblem: 'none',
  pose: 'ready',
  prop: 'none',
  limbColor: '#3E2D24',
  groundShadow: true,
  outlineShadow: 1.0,
  outlineLit: 0.95,
  rimIntensity: 1.0,
  shadowDepth: 1.05,
  customLayers: [],
};

// 3. PENUMPANG TREM — Figuran Stasiun Trem Layang (Lokasi 5) — Desain Dasar Netral
// Aturan: Siluet jangkung, mantel klasik, topi baret, syal teal, DILARANG kuning saffron!
const PENUMPANG_TREM_CONFIG = {
  ...DEFAULT_CONFIG,
  name: 'Penumpang Trem',
  prompt:
    'Penumpang trem stasiun layang berbadan jangkung, mantel klasik hijau lumut, topi baret marun, syal teal, kacamata bulat, pose desain netral',
  headShape: 'tall',
  skinColor: '#F1D4BA',
  blushColor: '#D6A390',
  eyes: 'chill',
  eyebrows: 'flat',
  mouth: 'flat',
  beard: 'mustache',
  faceAccessory: 'round_glasses',
  sweatDrop: false,
  blush: false,
  angerVein: false,
  eyeGazeX: 0.0,
  eyeGazeY: 0.0,
  hat: 'beret',
  hatPrimary: '#762C3C',
  hatAccent: '#B58D54',
  hatTilt: -4,
  hatLiftY: 0,
  backHair: 'side_part',
  hairColor: '#3D312C',
  outfit: 'trench_coat',
  robeColor: '#465F4E',
  innerColor: '#DDD2BE',
  sashColor: '#5B3D2C',
  trimColor: '#A88958',
  beltStyle: 'buckle',
  cape: 'scarf',
  capeColor: '#346E75',
  emblem: 'none',
  pose: 'ready',
  prop: 'none',
  limbColor: '#2E2A33',
  groundShadow: true,
  outlineShadow: 1.0,
  outlineLit: 0.92,
  rimIntensity: 1.05,
  shadowDepth: 1.08,
  customLayers: [],
};

const CAST = [
  {
    presetFile: 'bima_preset.json',
    pyFile: 'bima_character.py',
    className: 'BimaCharacter',
    defaultAnimation: 'static',
    config: BIMA_CONFIG,
  },
  {
    presetFile: 'pedagang_rempah_preset.json',
    pyFile: 'pedagang_rempah_character.py',
    className: 'PedagangRempahCharacter',
    defaultAnimation: 'static',
    config: PEDAGANG_REMPAH_CONFIG,
  },
  {
    presetFile: 'penumpang_trem_preset.json',
    pyFile: 'penumpang_trem_character.py',
    className: 'PenumpangTremCharacter',
    defaultAnimation: 'static',
    config: PENUMPANG_TREM_CONFIG,
  },
];

for (const item of CAST) {
  const presetPath = path.join(PRESET_DIR, item.presetFile);
  fs.writeFileSync(presetPath, JSON.stringify(item.config, null, 2), 'utf8');

  const exported = generatePythonComponent(item.config, {
    className: item.className,
    mode: 'component',
    defaultAnimation: item.defaultAnimation,
    defaultAngle: 0,
    fps: 30,
    resolutionScale: 3,
    includeDemoScene: true,
    includeComments: true,
  });

  const pyPath = path.join(CHAR_DIR, item.pyFile);
  fs.writeFileSync(pyPath, exported.code, 'utf8');
  console.log(`Exported ${item.className} (neutral/unlocked): ${item.pyFile} (${exported.lineCount} lines)`);
}
