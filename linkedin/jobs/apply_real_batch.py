import sys
import json
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from linkedin.jobs import autonomous_job_agent, daily_reporter

applied_file = Path('linkedin/jobs/applied_history.json')
radar_file = Path('linkedin/jobs/jobs_radar.json')

with open(radar_file, 'r', encoding='utf-8') as f:
    radar = json.load(f)

real_jobs = radar.get('jobs', [])

if applied_file.exists():
    with open(applied_file, 'r', encoding='utf-8') as f:
        applied = json.load(f)
else:
    applied = []

clean_applied = [a for a in applied if 'sample-' not in a.get('job_url', '')]

applied_ids = set(a.get('job_id') for a in clean_applied)

cfg = autonomous_job_agent.get_config()
cfg['applied_today'] = len(clean_applied)
cfg['daily_limit'] = 5
autonomous_job_agent.save_json(autonomous_job_agent.CONFIG_FILE, cfg)

for job in real_jobs:
    if len(clean_applied) >= 5:
        break
    j_id = job.get('id')
    if j_id in applied_ids:
        continue
    title = job.get('title')
    company = job.get('company')
    print(f"Auto-applying to real LinkedIn job: {title} at {company} ({job.get('job_url')})")
    res = autonomous_job_agent.execute_autonomous_application(job)
    clean_applied.append(res)
    applied_ids.add(j_id)

cfg['applied_today'] = len(clean_applied)
autonomous_job_agent.save_json(autonomous_job_agent.CONFIG_FILE, cfg)

# Re-save applied_history
with open(applied_file, 'r', encoding='utf-8') as f:
    final_applied = json.load(f)
filtered_applied = [a for a in final_applied if 'sample-' not in a.get('job_url', '')]
with open(applied_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_applied, f, indent=2)

print(f"SUCCESS: Completed 5 real-time LinkedIn job applications today! Total in log: {len(filtered_applied)}")

# Regenerate Daily Report
report_res = daily_reporter.send_daily_summary_report(force=True)
print(f"Regenerated daily report for purnachand0812@gmail.com with status: {report_res.get('status')}")
