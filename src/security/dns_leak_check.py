"""DNS leak detection."""

from __future__ import annotations

import socket
from typing import Dict, List, Optional


class DNSLeakCheck:
    TEST_DOMAINS = ["whoami.akamai.net", "myip.opendns.com"]

    def __init__(self, expected_dns: Optional[List[str]] = None):
        self.expected_dns = expected_dns or ["1.1.1.1", "8.8.8.8"]

    def check_resolver(self) -> Dict[str, object]:
        results: Dict[str, object] = {"leaked": False, "resolvers": [], "details": []}
        for domain in self.TEST_DOMAINS:
            try:
                answers = socket.getaddrinfo(domain, None)
                ips = list({item[4][0] for item in answers})
                results["resolvers"].extend(ips)
                results["details"].append({"domain": domain, "resolved": ips})
            except socket.gaierror as exc:
                results["details"].append({"domain": domain, "error": str(exc)})

        unique = set(results["resolvers"])
        if unique and not unique.issubset(set(self.expected_dns)):
            results["leaked"] = True
        return results

    def is_clean(self) -> bool:
        return not self.check_resolver()["leaked"]
