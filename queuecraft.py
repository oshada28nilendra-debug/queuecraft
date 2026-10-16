"""Deterministic, single-worker, non-preemptive scheduling simulator."""
import argparse
import heapq
import html
import json
from pathlib import Path


def validate(jobs):
    if not isinstance(jobs, list) or not jobs:
        raise ValueError('workload must be a nonempty list')
    seen = set()
    for j in jobs:
        if not isinstance(j, dict) or set(j) != {'id', 'arrival', 'duration', 'deadline'}:
            raise ValueError('each job needs exactly id, arrival, duration, deadline')
        if not isinstance(j['id'], str) or not j['id'].strip() or j['id'] in seen:
            raise ValueError('job IDs must be unique nonempty strings')
        seen.add(j['id'])
        for k in ('arrival', 'duration', 'deadline'):
            if type(j[k]) is not int or j[k] < 0:
                raise ValueError(f'{k} must be a nonnegative integer tick')
        if j['duration'] == 0:
            raise ValueError('duration must be positive')
    return jobs


def simulate(jobs, policy):
    validate(jobs)
    if policy not in ('FIFO', 'SJF', 'EDF'):
        raise ValueError('policy must be FIFO, SJF or EDF')
    pending = sorted(enumerate(jobs), key=lambda x: (x[1]['arrival'], x[0]))
    ready, timeline, results = [], [], []
    time = i = 0
    while i < len(pending) or ready:
        if not ready and time < pending[i][1]['arrival']:
            nxt = pending[i][1]['arrival']
            timeline.append(dict(kind='idle', start=time, end=nxt))
            time = nxt
        while i < len(pending) and pending[i][1]['arrival'] <= time:
            index, j = pending[i]
            priority = j[{'FIFO': 'arrival', 'SJF': 'duration', 'EDF': 'deadline'}[policy]]
            heapq.heappush(ready, (priority, j['arrival'], index, j))
            i += 1
        _, _, _, j = heapq.heappop(ready)
        finish = time + j['duration']
        results.append(dict(**j, start=time, completion=finish, waiting=time-j['arrival'],
                            turnaround=finish-j['arrival'], tardiness=max(0, finish-j['deadline']),
                            deadline_missed=finish > j['deadline']))
        timeline.append(dict(kind='job', id=j['id'], start=time, end=finish))
        time = finish
    return dict(policy=policy, jobs=results, timeline=timeline, metrics=dict(
        mean_waiting=sum(j['waiting'] for j in results)/len(results),
        mean_turnaround=sum(j['turnaround'] for j in results)/len(results),
        mean_tardiness=sum(j['tardiness'] for j in results)/len(results),
        missed_deadlines=sum(j['deadline_missed'] for j in results),
        makespan=time, busy_ticks=sum(j['duration'] for j in jobs),
        utilization=sum(j['duration'] for j in jobs)/time))


def compare(jobs):
    return [simulate(jobs, p) for p in ('FIFO', 'SJF', 'EDF')]


def render(reports):
    out = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QueueCraft</title><style>body{font:16px system-ui;background:#f5f2ea;color:#252a24;max-width:1100px;margin:32px auto;padding:16px}section{background:white;padding:20px;margin:20px 0;border-radius:12px}table{border-collapse:collapse;width:100%}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd}.scroll{overflow:auto}.timeline{display:flex;min-width:650px;height:58px}.block{background:#c65d3a;color:white;border-right:2px solid white;overflow:hidden;font-size:12px;padding:4px}.idle{background:#687569}</style><h1>QueueCraft</h1><p>Single worker · non-preemptive · identical workload · integer ticks</p><p>Timeline labels show start–end. Hover for job details. Idle time starts at tick zero.</p>']
    for r in reports:
        out.append('<section><h2>'+r['policy']+'</h2><div class="scroll"><div class="timeline">')
        for t in r['timeline']:
            label = html.escape(t.get('id', 'Idle'), quote=True)
            out.append(f'<div class="block {"idle" if t["kind"]=="idle" else ""}" style="flex:{t["end"]-t["start"]}" title="{label}: {t["start"]}–{t["end"]}">{label}<br>{t["start"]}–{t["end"]}</div>')
        out.append('</div></div><p>'+html.escape(json.dumps(r['metrics']))+'</p><div class="scroll"><table><tr>')
        keys = ['id', 'arrival', 'duration', 'deadline', 'start', 'completion', 'waiting', 'turnaround', 'tardiness', 'deadline_missed']
        out.extend('<th>'+k+'</th>' for k in keys)
        out.append('</tr>')
        for j in r['jobs']:
            out.append('<tr>'+''.join('<td>'+html.escape(str(j[k]))+'</td>' for k in keys)+'</tr>')
        out.append('</table></div></section>')
    return ''.join(out)+'</html>'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workload', type=Path)
    p.add_argument('--out', type=Path, required=True, help='new output directory')
    a = p.parse_args()
    try:
        reports = compare(json.loads(a.workload.read_text()))
        a.out.mkdir(parents=True, exist_ok=False)
        (a.out/'results.json').write_text(json.dumps(reports, indent=2))
        (a.out/'index.html').write_text(render(reports))
        print(json.dumps({r['policy']:r['metrics'] for r in reports}, indent=2))
    except (ValueError, OSError) as e:
        p.exit(2, f'Error: {e}\n')


if __name__ == '__main__':
    main()
