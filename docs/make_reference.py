"""Build docs/api-reference.html: one self-contained page with the OpenAPI spec embedded."""
import json
from pathlib import Path


def inline_refs(node, spec):
    """Replace every {"$ref": "#/a/b"} with a copy of what it points to.
    Swagger UI cannot resolve refs in a spec embedded in a page, so none may be left.
    Assumes no circular references, which is true for this API."""
    if isinstance(node, list):
        return [inline_refs(item, spec) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        target = spec
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        extras = {key: value for key, value in node.items() if key != "$ref"}
        return inline_refs({**target, **extras}, spec)
    return {key: inline_refs(value, spec) for key, value in node.items()}


docs = Path(__file__).parent
spec = json.loads((docs / "openapi.json").read_text(encoding="utf-8"))
spec = inline_refs(spec, spec)
spec_js = json.dumps(spec).replace("</", "<\\/")  # keep "</script>" out of the page

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{spec['info']['title']} reference</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <style>
    .note {{ font-size: 14px; margin: 0; padding: 12px 20px; font-family: sans-serif; background: #fff8e1;
             border-bottom: 1px solid #f5a623; color: #333; }}
    .swagger-ui .scheme-container {{ display: none; }}  /* Authorize box: useless without Try it out */
    .swagger-ui .info {{ margin: 20px 0 10px; }}  /* default is 50px above and below */
  </style>
</head>
<body>
  <div class="note">
    <strong>Static reference.</strong> The API isn’t hosted, so the “Try it out” buttons are disabled.
    To call the API yourself, run it locally in mock mode and follow the getting-started tutorial in the repository.
  </div>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({{
      spec: {spec_js},
      dom_id: "#swagger-ui",
      supportedSubmitMethods: []  // an empty list hides "Try it out"
    }});
  </script>
</body>
</html>
"""
(docs / "api-reference.html").write_text(html, encoding="utf-8")
print("Wrote", docs / "api-reference.html")