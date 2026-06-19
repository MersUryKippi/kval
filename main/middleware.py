from collections import Counter

from django.conf import settings


class RequestStatsMiddleware:
    counter = Counter()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.counter["total"] += 1
        self.counter[f"{response.status_code // 100}xx"] += 1

        c = self.counter
        report = f"requests={c['total']} 2xx={c['2xx']} 4xx={c['4xx']} 5xx={c['5xx']}"
        print("[stats]", report)

        log_path = getattr(settings, "STATS_LOG", None)
        if log_path:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(report + "\n")
        return response
