import { existsSync } from 'node:fs'
import { writeFile, mkdir } from 'node:fs/promises'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import openapiTS, { astToString } from 'openapi-typescript'

const root = fileURLToPath(new URL('../../', import.meta.url))
const venv = fileURLToPath(new URL('../../.venv/bin/python', import.meta.url))
const python = process.env.PYTHON || (existsSync(venv) ? venv : 'python3')
const exported = spawnSync(python, ['scripts/export_openapi.py'], { cwd: root, stdio: 'inherit' })
if (exported.error || exported.status !== 0) {
  console.error('Install the Python backend dependencies or set PYTHON to its interpreter.')
  process.exit(1)
}
const destination = new URL('../src/lib/api/schema.d.ts', import.meta.url)
await mkdir(new URL('../src/lib/api/', import.meta.url), { recursive: true })
const ast = await openapiTS(new URL('../openapi.json', import.meta.url))
await writeFile(destination, astToString(ast))
console.log('Generated src/lib/api/schema.d.ts')
