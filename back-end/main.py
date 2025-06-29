from apscheduler.schedulers.blocking import BlockingScheduler
import time

from functions import scrape_target_site, init_db, store_data, detect_changes
from parsers import cegeka_articles_parser, cegeka_jobs_parser, ns_jobs_parser, hackernews_parser


scheduler = BlockingScheduler()

init_db()

# Store this in DB at some point
jobs = {
    "Cegeka1": {
        "site": "cegeka",
        "url": "https://www.cegeka.com/nl-nl/nieuws",
        "parser": cegeka_articles_parser       
    },
    "Cegeka2": {
        "site": "cegeka",
        "url": "https://www.cegeka.com/nl-be/jobs/vacatures?",
        "parser": cegeka_jobs_parser       
    },
    "Nederlandse Spoorwegen": {
        "site": "NS",
        "url": 'https://www.werkenbijns.nl/vacatures?o=0&n=10&of=1210275&hl=0&hh=40&f=507&f=7442&f=508#vacancy-overview',
        "parser": ns_jobs_parser       
    },
    "Hackernews": {
        "site": "hackernews",
        "url": "https://news.ycombinator.com/newest",
        "parser": hackernews_parser       
    }
}


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