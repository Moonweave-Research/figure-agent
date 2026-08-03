import OCL from "openchemlib";

async function readJsonStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const text = chunks.join("").trim();
  return text ? JSON.parse(text) : {};
}

const payload = await readJsonStdin();
const width = Number(payload.width ?? 260);
const height = Number(payload.height ?? 120);
const smiles = String(payload.smiles ?? "CCSCCSCC");
const id = String(payload.id ?? "molecule");

const molecule = OCL.Molecule.fromSmiles(smiles);
molecule.inventCoordinates();

const svg = molecule.toSVG(width, height, id, {
  autoCrop: false,
  factorTextSize: 1.1,
  fontWeight: 700,
  strokeWidth: 1.4,
  suppressChiralText: true,
});

process.stdout.write(svg);
