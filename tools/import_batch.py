"""Importa en lote varias URLs de Amazon y devuelve datos COMPACTOS.

Uso:
    python tools/import_batch.py <target.html> <url1> <url2> ...

- Ejecuta tools/amazon_import.py para cada URL (con reintento y UTF-8),
  descargando imagen y datos crudos.
- Guarda el JSON completo en `_imp.json` (lo usa insert_products.py para
  sacar imagen/url sin que el asistente tenga que copiarlas).
- Imprime en stdout un JSON COMPACTO por producto (titulo recortado,
  bullets recortados, valoracion, nº valoraciones) — suficiente para
  redactar la ficha sin volcar el JSON gigante al contexto.

Reduce tokens: el asistente lee solo la salida compacta, no el JSON entero.
"""
import subprocess, json, os, sys

def main():
    if len(sys.argv) < 3:
        print("uso: python tools/import_batch.py <target.html> <url...>"); sys.exit(2)
    target = sys.argv[1]
    urls = sys.argv[2:]
    env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
    full, compact, failed = {}, {}, []
    for url in urls:
        asin = url.rstrip("/").split("/dp/")[-1].split("/")[0]
        data = None
        for attempt in range(2):
            try:
                out = subprocess.run(
                    ["python", "tools/amazon_import.py", url, "--target", target],
                    capture_output=True, text=True, timeout=150,
                    encoding="utf-8", errors="replace", env=env)
                s = out.stdout.strip()
                if not s:
                    raise ValueError((out.stderr or "no output")[-400:])
                data = json.loads(s)
                break
            except Exception as e:
                err = str(e)
        if data is None:
            failed.append(asin); full[asin] = {"error": err}; continue
        if data.get("ya_existe"):
            compact[asin] = {"ya_existe": True}
        full[asin] = data
        compact[asin] = {
            "t": data["titulo"][:90],
            "b": [b[:95] for b in (data.get("bullets") or [])[:5]],
            "r": data.get("valoracion"),
            "n": data.get("num_valoraciones"),
            "img": data.get("imagen"),
            "url": data.get("url"),
            "ya_existe": data.get("ya_existe", False),
        }
    with open("_imp.json", "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False)
    print(json.dumps(compact, ensure_ascii=False, indent=1))
    print(f"=== {len(urls)-len(failed)} ok, {len(failed)} failed"
          + (f" :: {failed}" if failed else ""))

if __name__ == "__main__":
    main()
