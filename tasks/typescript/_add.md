The following additional TypeScript packages are available:

- axios
- date-fns
- express
- zod
- nodejs standard library (e.g. `import { readFileSync } from 'fs';`)

NO OTHER PACKAGES ARE AVAILABLE.

Don't show the output of the required code, just the code in markdown ticks (```{{lang}}).

Note that our tsconfig has these settings:
```json
   "compilerOptions": {
      "target": "es2022",
      "module": "NodeNext",
      "moduleResolution": "NodeNext",
      "outDir": "./dist",
      "resolveJsonModule": true,
      "strict": true,
   },
```
It is a requirement that your code throws no errors or linter warnings.