from apscheduler.schedulers.blocking import BlockingScheduler
import time

from functions import scrape_target_site, init_db, DB_NAME, store_data, detect_changes
from parsers import timetohire_parser, hackernews_parser


scheduler = BlockingScheduler()

init_db()

# Store this in DB at some point
jobs = {
    "Hackerrank": {
        "site": "hackerrank",
        "url": "https://news.ycombinator.com/newest",
        "parser": hackernews_parser       
    }

}

"""
    "TTH": {
        "site": "timetohire",  
        "url": "https://www.werkenbijtimetohire.nl",
        "parser": timetohire_parser       
    },   
"""


@scheduler.scheduled_job('interval', seconds=10)  # Run every X seconds
def scheduled_job():
    print(f"📅 Running {len(jobs)} job(s) at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    for job_name, job in jobs.items():
        print(f"Running job for: {job_name}")
        print(f"Site: {job['site']}, URL: {job['url']}")
    
        # Your scrape + store logic
        soup = scrape_target_site(job['site'], job['url'])
        results = job['parser'](soup, job['site'])

        #print(results)

        print("detecting changes")
        changes = detect_changes(results)

        print("storing data")
        store_data(results)

        print(f"🆕 New: {len(changes['new'])}, ♻️ Changed: {len(changes['changed'])}, ❌ Removed: {len(changes['removed'])}")

# Start the scheduler
scheduler.start()