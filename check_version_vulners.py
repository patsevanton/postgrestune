#!/usr/bin/env python3

import vulners
vulners_api = vulners.Vulners()
results = vulners_api.softwareVulnerabilities("httpd", "1.5")
exploit_list = results.get('exploit')
vulnerabilities_list = [results.get(key) for key in results if key not in ['info', 'blog', 'bugbounty']]