# Our Day Mobil

Az asztali Our Day alkalmazás mellé készülő, mobilra optimalizált PWA.

## Jelenlegi állapot

- reszponzív mobilos kezdőlap
- működő alsó navigáció
- interaktív teendőlista-prototípus
- telepíthető PWA manifest
- Supabase alapmigráció esküvőkkel, tagokkal, vendégekkel, asztalokkal, feladatokkal és szolgáltatásokkal
- minden felhős adattáblán bekapcsolt Row Level Security

Az első felület szándékosan demóadatokat használ. A Supabase kliens bekötése a projekt URL-jének és publikus anon kulcsának megadása után következik.

## Helyi indítás

```powershell
pnpm install
pnpm dev
```

Ezután az alkalmazás a `http://localhost:3000` címen érhető el.
