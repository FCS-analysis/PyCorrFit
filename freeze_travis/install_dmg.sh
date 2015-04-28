#!/bin/sh
# packages.sh from
# https://github.com/ayufan/travis-osx-vm-templates/blob/master/scripts/packages.sh

set -eo pipefail
shopt -s nullglob

install_dmg() {
    declare dmg="$1" target="${2:-/}"
    echo "Installing $dmg..."
    TMPMOUNT=`/usr/bin/mktemp -d /tmp/dmg.XXXX`
    hdiutil attach "$dmg" -mountpoint "$TMPMOUNT"
    for app in $TMPMOUNT/*.app; do
        app_name="$(basename "$app")"
        echo "Installing application $app_name..."
        rm -rf "/Applications/$app_name"
        cp -a "$app" "/Applications/"
    done
    find "$TMPMOUNT" -name '*.pkg' -exec installer -target "$target" -pkg "{}" \;
    hdiutil detach "$TMPMOUNT"
    rm -rf "$TMPMOUNT"
    rm -f "$dmg"
}

install_dmg_url() {
    declare url="$1" target="$2"
    local dmg="${dmg:-$(basename "$url")}"
    echo "Downloading $url..."
    curl --retry 3 -o "$dmg" "$url"
    install_dmg "$dmg" "$target"
}

# install packages
for package in ./*.dmg; do
    install_dmg "$package"
done
