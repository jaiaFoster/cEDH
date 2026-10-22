"""Run preserved/new tests plus byte reproduction; save actual deterministic results."""
import json,pathlib,re,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    commands=[
      ('preserved_batch_suites',[sys.executable,'-m','unittest','discover','-s','commander-doubles-deck-benchmarks/tests','-p','test_batch*.py','-v']),
      ('global_v3_suite',[sys.executable,'-m','unittest','discover','-s',str(HERE.relative_to(ROOT)),'-p','test_recalibration_v3.py','-v']),
      ('byte_reproduction',[sys.executable,str((HERE/'recalibration_v3.py').relative_to(ROOT)),'--check']),
    ]
    results=[]
    for name,cmd in commands:
        run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        output=run.stdout+run.stderr
        if run.returncode:
            print(output,file=sys.stderr);return run.returncode
        match=re.search(r'Ran (\d+) tests?',output)
        row={'check':name,'command':'python '+ ' '.join(cmd[1:]),'passed':True,'exit_code':run.returncode}
        if match:row['tests_run']=int(match[1])
        results.append(row)
        print(name+': passed'+(' ('+match[1]+' tests)' if match else ''))
    payload={'schedule_version':'season0-proposed-global-v3-2026-10-22','activated':False,
             'results':results,'total_tests_run':sum(r.get('tests_run',0) for r in results),
             'interpretation':'Passing construction, precedence and conditional-rules regressions does not validate point prices or win probabilities.'}
    (HERE/'validation_results_v3.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    return 0

if __name__=='__main__':sys.exit(main())
