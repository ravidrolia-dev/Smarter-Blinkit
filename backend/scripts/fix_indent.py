lines = open("scripts/import_products.py").read().split("\n")
out = []
for i, l in enumerate(lines):
    if 234 <= i <= 316 and l.startswith("    "):
        out.append(l[4:])
    else:
        out.append(l)
open("scripts/import_products.py", "w").write("\n".join(out))
