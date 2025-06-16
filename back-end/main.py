from apscheduler.schedulers.blocking import BlockingScheduler
import time

from functions import scrape_target_site, timetohire_parser, init_db, DB_NAME, store_jobs, detect_job_changes

scheduler = BlockingScheduler()

init_db()

@scheduler.scheduled_job('interval', seconds=10)  # Run every 60 minutes
def scheduled_job():
    print(f"📅 Running job at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Your scrape + store logic
    site = "timetohire"
    url = "https://www.werkenbijtimetohire.nl"
    soup = scrape_target_site(site, url)
    results = timetohire_parser(soup, site)

    print(results)

    changes = detect_job_changes(results)
    store_jobs(results)

    print(f"🆕 New: {len(changes['new'])}, ♻️ Changed: {len(changes['changed'])}, ❌ Removed: {len(changes['removed'])}")

# Start the scheduler
scheduler.start()