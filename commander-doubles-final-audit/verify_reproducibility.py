"""Check committed generated artifacts against two deterministic regenerations.
Historical execution logs and manually authored source files are not regenerated.
"""
import json,pathlib
from audit_pipeline import generate
HERE=pathlib.Path(__file__).resolve().parent
inputs=json.loads((HERE/"audit_inputs.json").read_text())
a,_=generate(HERE.parent,inputs)
b,_=generate(HERE.parent,inputs)
mismatch=[name for name in a if a[name]!=b.get(name)]
saved=[name for name in a if not (HERE/name).is_file() or (HERE/name).read_text()!=a[name]]
result={"generated_files_compared":len(a),"mismatches":mismatch,"saved_artifact_mismatches":saved,"successful":not mismatch and not saved}
print(json.dumps(result,indent=2))
assert result["successful"]
