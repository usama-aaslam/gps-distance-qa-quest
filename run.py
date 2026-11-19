"""One-command demonstration: regenerate, demonstrate old failure, show fixed pass, run tests."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(*args):
  p=subprocess.run([sys.executable,*args],cwd=ROOT)
  return p.returncode

if __name__=='__main__':
  assert run('generate_data.py')==0
  print('\n1) PROVE regression check FAILS on OLD behaviour:',flush=True)
  old=run('qa.py','--mode','old','--verify')
  assert old!=0,'Old behaviour unexpectedly passed; regression invalid'
  print('\n2) PROVE regression check PASSES on FIXED behaviour:',flush=True)
  assert run('qa.py','--mode','fixed','--verify')==0
  print('\n3) Run deterministic automated tests:',flush=True)
  assert run('-m','pytest','-q','tests')==0
  print('\nSUCCESS: old failed as expected; fixed passed; tests passed.',flush=True)
