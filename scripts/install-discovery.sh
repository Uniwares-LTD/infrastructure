#!/bin/bash
# Run once from the existing trusted root session, after verifying this file's hash.
set -euo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $# -eq 0 && $EUID -eq 0 ]] || { echo 'Root session and no arguments required.' >&2; exit 1; }
target=/usr/local/sbin/uniwares-discovery
rule=/etc/sudoers.d/uniwares-discovery
[[ ! -e $target && ! -L $target && ! -e $rule && ! -L $rule ]] || {
    echo 'Existing installation detected; inspect before replacing.' >&2; exit 1;
}
for directory in /usr/local /usr/local/sbin /etc/sudoers.d; do
    [[ -d $directory && ! -L $directory && $(stat -c %u "$directory") == 0 ]] || exit 1
    mode=$(stat -c %a "$directory")
    (( (8#$mode & 0022) == 0 )) || { echo 'Unsafe parent permissions.' >&2; exit 1; }
done
getent passwd uniwares-ops-admin >/dev/null
work=$(mktemp -d /root/uniwares-discovery.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
cp -- /home/uniwares-ops-admin/srv1-discovery.py "$work/helper"
printf '%s  %s\n' d5e7d42f4097624043bf9471fab33d139aef2f1c02a780e8ad335d483244a0e3 "$work/helper" | sha256sum --check --status
printf '%s\n' 'uniwares-ops-admin ALL=(root) NOPASSWD: /usr/local/sbin/uniwares-discovery ""' > "$work/sudoers"
visudo -cf /etc/sudoers
visudo -cf "$work/sudoers"
install -o root -g root -m 0755 "$work/helper" "$target"
install -o root -g root -m 0440 "$work/sudoers" "$rule"
if ! visudo -cf /etc/sudoers; then
    rm -- "$rule"
    echo 'Validation failed; new sudo rule removed. Helper retained for inspection.' >&2
    exit 1
fi
echo 'Installed fixed discovery helper only. No services changed.'
