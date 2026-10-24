#!/usr/bin/python3 -I
"""Fixed read-only probes. Install root-owned; never grant sudo to the source copy."""
import glob
import json
import os
import subprocess
import sys

ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", "LC_ALL": "C"}
PROBES = (
    ("containers", ("/usr/bin/docker", "--host=unix:///var/run/docker.sock", "ps", "-a", "--format", "{{json .Names}}\t{{json .Image}}\t{{json .Status}}\t{{json .Ports}}")),
    ("network_ids", ("/usr/bin/docker", "--host=unix:///var/run/docker.sock", "network", "ls", "--quiet", "--no-trunc")),
    ("ufw", ("/usr/sbin/ufw", "status")),
)


def probe(command):
    try:
        result = subprocess.run(command, cwd="/", env=ENV, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=20, check=False, text=True)
        if result.returncode:
            return {"error": "command failed", "exit_code": result.returncode}
        if len(result.stdout) > 131072:
            return {"error": "output limit exceeded"}
        return {"output": result.stdout.strip()}
    except (OSError, subprocess.TimeoutExpired):
        return {"error": "command unavailable or timed out"}


def collect():
    report = {name: probe(command) for name, command in PROBES}
    ids = report.pop("network_ids")
    report["networks"] = []
    if "error" in ids:
        report["networks"] = ids
    else:
        for network_id in ids["output"].splitlines()[:128]:
            if len(network_id) != 64 or any(c not in "0123456789abcdef" for c in network_id):
                report["networks"].append({"error": "invalid network ID"})
                continue
            report["networks"].append(probe((
                "/usr/bin/docker", "--host=unix:///var/run/docker.sock", "network", "inspect",
                "--format", "{{json .Name}} {{json .IPAM.Config}}", network_id)))
    # Names only: never print cron commands, environment, logs or container config.
    report["schedule_files"] = sorted(glob.glob("/etc/cron.d/*") +
                                      glob.glob("/var/spool/cron/crontabs/*"))
    report["limitations"] = ["Provider firewall and effective packet filtering unverified",
                              "Schedule contents and application health unverified"]
    return report


def main():
    if len(sys.argv) != 1:
        print("No arguments accepted.", file=sys.stderr)
        return 2
    if os.geteuid() != 0:
        print("Run the installed helper through scoped sudo.", file=sys.stderr)
        return 1
    print(json.dumps(collect(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
