#!/usr/bin/env python3
"""Write stats.json for the downloads section of the website from Google Analytics.

Needs GA_PROPERTY_ID (the numeric property ID, not the G-… measurement ID) and
GA_SERVICE_ACCOUNT_JSON (the service account's key). Every run rebuilds the whole
file from Analytics, so a failed or partial day corrects itself on the next run.
"""
import datetime
import json
import os
import pathlib
import sys

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)

EVENT = "HeterraDownload"  # sent by the download buttons in index.html
ALL_TIME = DateRange(start_date="2015-08-14", end_date="today")  # the earliest date Analytics accepts
STATS = pathlib.Path(__file__).resolve().parents[2] / "stats.json"


def report(client, prop, dimension, metric, event=None):
    """[(dimension value, metric value)] over all the property's data."""
    request = RunReportRequest(
        property=f"properties/{prop}",
        dimensions=[Dimension(name=dimension)],
        metrics=[Metric(name=metric)],
        date_ranges=[ALL_TIME],
        limit=100000,
    )
    if event:
        request.dimension_filter = FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value=event, match_type=Filter.StringFilter.MatchType.EXACT),
            )
        )
    rows = client.run_report(request).rows
    return [(r.dimension_values[0].value, int(r.metric_values[0].value)) for r in rows]


def daily_counts(rows):
    """Analytics leaves out days with no events; they are put back as zeros so each day has a point."""
    counts = {datetime.datetime.strptime(d, "%Y%m%d").date(): n for d, n in rows if n > 0}
    day, last = min(counts), max(counts)
    days = []
    while day <= last:
        days.append({"date": day.isoformat(), "count": counts.get(day, 0)})
        day += datetime.timedelta(days=1)
    return days


def country_count(rows):
    """Every visitor to the site counts; "(not set)" is a visit whose country is unknown, not a country."""
    return sum(1 for name, users in rows if users > 0 and name != "(not set)")


def main():
    client = BetaAnalyticsDataClient.from_service_account_info(json.loads(os.environ["GA_SERVICE_ACCOUNT_JSON"]))
    prop = os.environ["GA_PROPERTY_ID"].strip()
    downloads = report(client, prop, "date", "eventCount", EVENT)
    countries = report(client, prop, "country", "totalUsers")
    # no data means something is wrong with the query or the access; keep the numbers already published
    if not any(n > 0 for _, n in downloads) or country_count(countries) == 0:
        sys.exit("Analytics returned no downloads or no countries; stats.json is unchanged")
    days = daily_counts(downloads)
    stats = {
        "updated": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        "countries": country_count(countries),
        "daily": days,
    }
    STATS.write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    print(f"{sum(d['count'] for d in days)} downloads, {stats['countries']} countries, {len(days)} days")


if __name__ == "__main__":
    main()
