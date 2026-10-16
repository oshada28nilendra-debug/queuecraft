import copy
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from queuecraft import compare, simulate, render

ROOT=Path(__file__).resolve().parents[1]
def job(i,a=0,d=1,deadline=10):
    return dict(id=i,arrival=a,duration=d,deadline=deadline)

class Tests(unittest.TestCase):
    def test_expected_orders(self):
        jobs=json.loads((ROOT/'examples/workload.json').read_text())
        r=compare(jobs)
        self.assertEqual([[j['id'] for j in x['jobs']] for x in r], [list('ABCDE'),list('ACDBE'),list('ADCBE')])
        self.assertEqual([x['metrics']['mean_waiting'] for x in r],[4.4,3.0,3.2])
        self.assertEqual([x['metrics']['missed_deadlines'] for x in r],[2,2,3])
    def test_idle_and_deadline_equality(self):
        for r in compare([job('a',3,2,5),job('b',8,1,9)]):
            self.assertEqual(r['timeline'][0],dict(kind='idle',start=0,end=3))
            self.assertEqual(r['timeline'][2],dict(kind='idle',start=5,end=8))
            self.assertEqual(r['metrics']['missed_deadlines'],0)
            self.assertEqual(r['metrics']['utilization'],3/9)
    def test_ties_input_order(self):
        for r in compare([job('z'),job('a')]):self.assertEqual([x['id'] for x in r['jobs']],['z','a'])
    def test_nonpreemption(self):
        for r in compare([job('a',0,10),job('b',1,1,2)]):self.assertEqual(r['jobs'][1]['start'],10)
    def test_arrival_at_completion(self):
        r=simulate([job('a',0,2),job('b',1,5),job('c',2,1)],'SJF')
        self.assertEqual([j['id'] for j in r['jobs']],list('acb'))
    def test_invalid(self):
        for x in [[],{},[job('a'),job('a')],[job('')],[job('a',-1)],[job('a',d=0)],[job('a',d=True)],[job('a',d=1.5)],[dict(id='a')]]:
            with self.subTest(x=x),self.assertRaises(ValueError):compare(x)
        with self.assertRaises(ValueError):simulate([job('a')],'unknown')
    def test_input_unchanged(self):
        j=[job('a')];original=copy.deepcopy(j);compare(j);self.assertEqual(j,original)
    def test_past_deadline(self):
        self.assertEqual(simulate([job('a',5,1,2)],'EDF')['jobs'][0]['tardiness'],4)
    def test_escape(self):
        self.assertNotIn('<script>',render(compare([job('<script>')])) )
    def test_exhaustive_small_invariants(self):
        for arrivals in itertools.product(range(3),repeat=3):
            for durations in itertools.product([1,2],repeat=3):
                jobs=[job(str(i),arrivals[i],durations[i],i+2) for i in range(3)]
                for r in compare(jobs):
                    self.assertEqual(len(r['jobs']),3)
                    last=0
                    for j in r['jobs']:
                        self.assertGreaterEqual(j['start'],max(last,j['arrival']))
                        self.assertEqual(j['completion']-j['start'],j['duration'])
                        last=j['completion']
                    self.assertEqual(sum(t['end']-t['start'] for t in r['timeline']),last)
    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            cmd=[sys.executable,str(ROOT/'queuecraft.py'),str(ROOT/'examples/workload.json'),'--out',str(Path(d)/'out')]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertTrue((Path(d)/'out/index.html').exists())
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)

if __name__=='__main__':unittest.main()
