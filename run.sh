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

manifests () {
  for BUILD in latest debian fedora; do

    MAN_ARCH_LIST="amd64 arm64v8 arm32v7 i386 s390x ppc64le"
    case "$BUILD" in
      fedora)
        MAN_VERSION="f${DEF_FEDORA_VERSION}"
      ;;
      debian|latest)
        MAN_VERSION="d${DEF_DEBIAN_VERSION}"
        MAN_ARCH_LIST="$MAN_ARCH_LIST arm32v6 mips64el"
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
    ./cli/cli.py build -s debian $BASE_ARCH
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
  -m)
    build_cfg
    manifests
  ;;
  -a)
    assets;
  ;;
  *)
    printf "${ANSI_RED}Unknown option '$1'!${ANSI_NOCOLOR}\n"
    exit 1
esac
