"""Package outputs, executable sources and cached research data, excluding environments/Git history."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).parent
files=[p for p in root.iterdir() if p.is_file() and p.suffix in ['.py','.js','.md','.json','.csv','.png','.html','.txt']]
files+=list((root/'data/raw').glob('*'))+list((root/'data/clean').glob('*'))
files+=[root/'data/taw/decks_v2.json',root/'data/taw/README.md',root/'data/taw_commit.txt']
with ZipFile(root/'commander_calibration_bundle.zip','w',ZIP_DEFLATED,compresslevel=6) as out:
 for p in sorted(set(files)):
  if p.is_file():out.write(p,p.relative_to(root))
with ZipFile(root/'commander_calibration_bundle.zip') as out:
 assert out.testzip() is None
 print(f'{len(out.namelist())} files; {Path(out.filename).stat().st_size/1024**2:.1f} MiB; archive integrity passed')
