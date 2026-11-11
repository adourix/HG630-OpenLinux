#!/usr/bin/env bash
set -euo pipefail

# Build historical mksquashfs binaries in a caller-selected temporary/work
# directory. Sources and patches are never placed in the repository.
work=${1:?usage: $0 WORK_DIRECTORY}
mkdir -p "$work"
xz_archive="$work/xz-5.2.5.tar.gz"
if [[ ! -e "$xz_archive" ]]; then
  curl -L --fail --silent --show-error 'https://sourceforge.net/projects/lzmautils/files/xz-5.2.5.tar.gz/download' -o "$xz_archive"
fi
tar -xf "$xz_archive" -C "$work"
xz_src=$(find "$work" -maxdepth 1 -type d -name 'xz-5.2.5' -print -quit)
prefix="$work/xz-prefix"
if [[ ! -e "$prefix/include/lzma.h" ]]; then
  (cd "$xz_src" && ./configure --prefix="$prefix" --disable-shared --disable-doc --disable-scripts --disable-symbols --disable-nls && make -j2 && make install)
fi
declare -A urls=(
  [4.2]='https://sourceforge.net/projects/squashfs/files/squashfs/squashfs4.2/squashfs4.2.tar.gz/download'
  [4.3]='https://sourceforge.net/projects/squashfs/files/squashfs/squashfs4.3/squashfs4.3.tar.gz/download'
  [4.4]='https://sourceforge.net/projects/squashfs/files/squashfs/squashfs4.4/squashfs4.4.tar.gz/download'
)
for version in 4.2 4.3 4.4; do
  archive="$work/squashfs${version}.tar.gz"
  [[ -e "$archive" ]] || curl -L --fail --silent --show-error "${urls[$version]}" -o "$archive"
  dest="$work/squashfs-$version"
  [[ -e "$dest" ]] || { mkdir -p "$dest"; tar -xf "$archive" -C "$dest" --strip-components=1; }
  source="$dest/squashfs-tools"
  if [[ "$version" == 4.2 || "$version" == 4.3 ]]; then
    sed -i -E 's/unsigned int major = major\(([^)]*)\);/unsigned int major_num = major(\1);/; s/unsigned int minor = minor\(([^)]*)\);/unsigned int minor_num = minor(\1);/' "$source/mksquashfs.c"
    sed -i -E 's/if\(major > /if(major_num > /; s/if\(minor > /if(minor_num > /; s/major, filename/major_num, filename/g; s/minor, filename/minor_num, filename/g; s/major &/major_num \&/g; s/minor &/minor_num \&/g; s/major <</major_num <</g' "$source/mksquashfs.c"
  fi
  [[ "$version" == 4.2 ]] && sed -i 's/^inline void add_dir_entry/void add_dir_entry/' "$source/mksquashfs.c"
  make -C "$source" clean >/dev/null 2>&1 || true
  flags="-I$prefix/include -include sys/sysmacros.h -fcommon"
  [[ "$version" == 4.2 ]] && flags="$flags -fgnu89-inline"
  make -C "$source" -j2 XZ_SUPPORT=1 EXTRA_CFLAGS="$flags" EXTRA_LDFLAGS="-L$prefix/lib"
done
git clone -q --depth 1 --branch 4.6.1 https://github.com/plougher/squashfs-tools.git "$work/squashfs-4.6.1"
make -C "$work/squashfs-4.6.1/squashfs-tools" -j2 XZ_SUPPORT=1 EXTRA_CFLAGS="-I$prefix/include -include sys/sysmacros.h -fcommon" EXTRA_LDFLAGS="-L$prefix/lib"
echo "Tools are under $work/squashfs-*/squashfs-tools/mksquashfs"
