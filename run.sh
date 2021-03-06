#!/usr/bin/env bash

# Copyright 2019-2021 Unai Martinez-Corral <unai.martinezcorral@ehu.eus>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

cd $(dirname $0)

export DOCKER_BUILDKIT=1

. ./utils.sh

#--

pkg_arch () {
  case "$BUILD_ARCH" in
    fedora)
      case "$1" in
        amd64)
          echo x86_64 ;;
        i386)
          echo i686 ;;
        arm64v8)
          echo aarch64 ;;
        arm32v7)
          echo armv7hl ;;
        ppc64*)
          echo ppc64le ;;
        *)
          echo "$1"
      esac
    ;;
    debian)
      case "$1" in
        x86_64)
          echo amd64 ;;
        arm64v8)
          echo arm64 ;;
        arm32v7)
          echo armhf ;;
        arm32v6|arm32v5)
          echo armel ;;
        ppc64*)
          echo ppc64el ;;
        *)
          echo "$1"
      esac
    ;;
  esac
}

guest_arch() {
  case "$1" in
   amd64)
     echo x86_64 ;;
   arm64)
     echo aarch64 ;;
   armhf|armel|armv7hl)
     echo arm ;;
   ppc64*)
     echo ppc64le ;;
   *)
     echo "$1"
  esac
}

#--

getSingleQemuUserStatic () {
  case "$BUILD_ARCH" in
    fedora)
      URL="https://kojipkgs.fedoraproject.org/packages/qemu/${VERSION}/${FEDORA_VERSION}/$(pkg_arch ${HOST_ARCH})/qemu-user-static-${VERSION}-${FEDORA_VERSION}.$(pkg_arch ${HOST_ARCH}).rpm"
      echo "$URL"
      curl -fsSL "$URL" | rpm2cpio - | zstdcat | cpio -dimv "*usr/bin*qemu-$(guest_arch $(pkg_arch ${BASE_ARCH}))-static"
      mv ./usr/bin/qemu-$(guest_arch $(pkg_arch ${BASE_ARCH}))-static ./
      rm -rf ./usr/bin
    ;;
    debian)
      URL="http://ftp.debian.org/debian/pool/main/q/qemu/qemu-user-static_${VERSION}${DEBIAN_VERSION}_$(pkg_arch ${HOST_ARCH}).deb"
      echo "$URL"
      curl -fsSL "$URL" \
      | dpkg --fsys-tarfile - \
      | tar xvf - --wildcards ./usr/bin/qemu-$(guest_arch $(pkg_arch ${BASE_ARCH}))-static --strip-components=3
    ;;
  esac
}

getAndRegisterSingleQemuUserStatic () {
  print_start "Get single qemu-user-static"
  getSingleQemuUserStatic

  print_start "Register binfmt interpreter for single qemu-user-static"
  $(command -v sudo) QEMU_BIN_DIR="$(pwd)" ./register.sh -- -r
  $(command -v sudo) QEMU_BIN_DIR="$(pwd)" ./register.sh -s -- -p "$(guest_arch $(pkg_arch $BASE_ARCH))"

  print_start "List binfmt interpreters"
  $(command -v sudo) ./register.sh -l -- -t
}

build_register () {
  case "$BASE_ARCH" in
    amd64|arm64v8|arm32v7|arm32v6|i386|ppc64le|s390x)
      HOST_LIB="${BASE_ARCH}/"
    ;;
    *)
      HOST_LIB="skip"
  esac

  if [ -n "$CI" ]; then
    case "$BASE_ARCH" in
      arm64v8|arm32v7|arm32v6|ppc64le|s390x)
        getAndRegisterSingleQemuUserStatic
    esac
  fi

  [ "$HOST_LIB" = "skip" ] && {
    printf "$ANSI_YELLOW! Skipping creation of $IMG[-register] because HOST_LIB <$HOST_LIB>.$ANSI_NOCOLOR\n"
  } || {
    print_start "Build $IMG-register"
    docker build -t $IMG-register . -f-<<EOF
FROM ${HOST_LIB}busybox
#RUN mkdir /qus
ENV QEMU_BIN_DIR=/qus/bin
COPY ./register.sh /qus/register
ADD https://raw.githubusercontent.com/umarcor/qemu/series-qemu-binfmt-conf/scripts/qemu-binfmt-conf.sh /qus/qemu-binfmt-conf.sh
RUN chmod +x /qus/qemu-binfmt-conf.sh
ENTRYPOINT ["/qus/register"]
EOF

    print_start "Build $IMG"
    docker build -t $IMG . -f-<<EOF
FROM $IMG-register
COPY --from="$IMG"-pkg /usr/bin/qemu-* /qus/bin/
VOLUME /qus
EOF
  }
}

#--

build () {
  [ -d releases ] && rm -rf releases
  mkdir -p releases

  [ -d bin-static ] && rm -rf bin-static
  mkdir -p bin-static

  cd bin-static

  case "$BUILD_ARCH" in
    fedora)
      PACKAGE_URI=${PACKAGE_URI:-https://kojipkgs.fedoraproject.org/packages/qemu/${VERSION}/${FEDORA_VERSION}/$(pkg_arch $BASE_ARCH)/qemu-user-static-${VERSION}-${FEDORA_VERSION}.$(pkg_arch $BASE_ARCH).rpm}
      print_start "Extract $PACKAGE_URI"

      # https://bugzilla.redhat.com/show_bug.cgi?id=837945
      curl -fsSL "$PACKAGE_URI" | rpm2cpio - | zstdcat | cpio -dimv "*usr/bin*qemu-*-static"

      mv ./usr/bin/* ./
      rm -rf ./usr/bin
    ;;
    debian)
      PACKAGE_URI=${PACKAGE_URI:-http://ftp.debian.org/debian/pool/main/q/qemu/qemu-user-static_${VERSION}${DEBIAN_VERSION}_$(pkg_arch $BASE_ARCH).deb}
      print_start "Extract $PACKAGE_URI"
      curl -fsSL "$PACKAGE_URI" | dpkg --fsys-tarfile - | tar xvf - --wildcards ./usr/bin/qemu-*-static --strip-components=3
    ;;
  esac

  for F in $(ls); do
    tar -czf "../releases/${F}_${BASE_ARCH}.tgz" "$F"
  done

  case "$BUILD_ARCH" in
    fedora)
      IMG="${REPO}:${BASE_ARCH}-f${VERSION}"
    ;;
    debian)
      IMG="${REPO}:${BASE_ARCH}-d${VERSION}"
    ;;
  esac

  cd ..

  if [ -z "$QUS_RELEASE" ]; then
    print_start "Build $IMG-pkg"
    docker build -t "$IMG"-pkg ./bin-static -f-<<EOF
FROM scratch
COPY ./* /usr/bin/
EOF
    build_register
  fi
}

#--

manifests () {
  for BUILD in latest debian fedora; do

    MAN_ARCH_LIST="amd64 arm64v8 arm32v7 i386 s390x ppc64le"
    case "$BUILD" in
      fedora)
        MAN_VERSION="f${DEF_FEDORA_VERSION}"
      ;;
      debian|latest)
        MAN_VERSION="d${DEF_DEBIAN_VERSION}"
        MAN_ARCH_LIST="$MAN_ARCH_LIST arm32v6"
      ;;
    esac
    case "$BUILD" in
      latest)
        unset MAN_IMG_VERSION
      ;;
      debian|fedora)
        MAN_IMG_VERSION="$MAN_VERSION"
      ;;
    esac

    for i in latest pkg register; do
      #[ "$i" == "latest" ] && p="latest" || p="$i"

      [ "x$MAN_IMG_VERSION" != "x" ] && p="-$i" || p="$i"
      if [ "x$MAN_IMG_VERSION" != "x" ] && [ "x$i" = "xlatest" ]; then
        p=""
      fi

      MAN_IMG="${REPO}:${MAN_IMG_VERSION}${p}"

      [ "$i" == "latest" ] && p="" || p="-$i"
      unset cmd
      for arch in $MAN_ARCH_LIST; do
        cmd="$cmd ${REPO}:${arch}-${MAN_VERSION}${p}"
      done

      print_start "Docker manifest create $MAN_IMG"
      docker manifest create -a $MAN_IMG $cmd

      print_start "Docker manifest push $MAN_IMG"
      docker manifest push --purge "$MAN_IMG"
    done

  done
}

#--

assets() {
  ARCH_LIST="x86_64 i686 aarch64 ppc64le s390x"
  case "$BUILD" in
    fedora)
      ARCH_LIST="$ARCH_LIST armv7hl"
    ;;
    debian)
      ARCH_LIST="$ARCH_LIST armhf armel mipsel mips64el"
    ;;
  esac
  mkdir -p ../releases
  for BASE_ARCH in $ARCH_LIST; do
    print_start "Build $BASE_ARCH" "$ANSI_MAGENTA"
    unset PACKAGE_URI
    build_cfg
    build
    print_start "Copy $BASE_ARCH" "$ANSI_MAGENTA"
    cp -vr releases/* ../releases/
  done
  rm -rf releases
  mv ../releases ./
}

#--

build_cfg () {
  BUILD_ARCH=${BUILD:-debian}

  FEDORA_VERSION="4.fc34"
  DEF_FEDORA_VERSION="5.2.0"

  DEBIAN_VERSION="+dfsg-3"
  DEF_DEBIAN_VERSION="5.2"

  case "$BUILD_ARCH" in
    fedora)
      DEF_VERSION="$DEF_FEDORA_VERSION"
    ;;
    debian)
      DEF_VERSION="$DEF_DEBIAN_VERSION"
    ;;
  esac
  VERSION=${VERSION:-$DEF_VERSION}

  REPO=${REPO:-aptman/qus}
  HOST_ARCH=${HOST_ARCH:-x86_64}
  BASE_ARCH=${BASE_ARCH:-x86_64}

  PRINT_BASE_ARCH="$BASE_ARCH"
  case "$BASE_ARCH" in
    x86_64|x86-64|amd64|AMD64)
      BASE_ARCH=amd64 ;;
    aarch64|armv8|ARMv8|arm64v8)
      BASE_ARCH=arm64v8 ;;
    aarch32|armv8l|armv7|armv7l|ARMv7|arm32v7|armhf|armv7hl)
      BASE_ARCH=arm32v7 ;;
    arm32v6|ARMv6|armel)
      BASE_ARCH=arm32v6 ;;
    arm32v5|ARMv5)
      BASE_ARCH=arm32v5 ;;
    i686|i386|x86)
      BASE_ARCH=i386 ;;
    ppc64*|POWER8)
      BASE_ARCH=ppc64le ;;
    s390x)
      BASE_ARCH=s390x ;;
    mips|mipsel)
      BASE_ARCH=mipsel ;;
    mips64*)
      BASE_ARCH=mips64el ;;
    *)
      echo "Invalid BASE_ARCH <${BASE_ARCH}>."
      exit 1
  esac

  [ -n "$PRINT_BASE_ARCH" ] && PRINT_BASE_ARCH="$BASE_ARCH [$PRINT_BASE_ARCH]" || PRINT_BASE_ARCH="$BASE_ARCH"

  echo "VERSION: $VERSION $DEF_VERSION"
  echo "REPO: $REPO"
  echo "BASE_ARCH: $PRINT_BASE_ARCH"; unset PRINT_BASE_ARCH
  echo "HOST_ARCH: $HOST_ARCH";
  echo "BUILD_ARCH: $BUILD_ARCH";
}

#--

case "$1" in
  -b|-m)
    build_cfg
    case "$1" in
      -m) manifests ;;
      *)  build
    esac
  ;;
  -a)
    assets;
  ;;
  *)
    printf "${ANSI_RED}Unknown option '$1'!${ANSI_NOCOLOR}\n"
    exit 1
esac
