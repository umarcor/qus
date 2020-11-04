<p align="center">
  <a title="dbhi.github.io/qus" href="https://dbhi.github.io/qus"><img src="./docs/logo/logo_blur.png" width="550"/></a>
</p>

<p align="center">
  <a title="dbhi.github.io/qus" href="https://dbhi.github.io/qus"><img src="https://img.shields.io/website.svg?label=dbhi.github.io%2Fqus&longCache=true&style=flat-square&url=http%3A%2F%2Fdbhi.github.io%2Fqus%2Findex.html"></a><!--
  -->
  <a title="Docker Hub" href="https://hub.docker.com/r/aptman/qus/"><img src="https://img.shields.io/docker/pulls/aptman/qus.svg?longCache=true&style=flat-square&logo=docker&logoColor=fff&label=aptman%2Fqus"></a><!--
  -->
  <a title="Releases" href="https://github.com/dbhi/qus/releases"><img src="https://img.shields.io/github/commits-since/dbhi/qus/latest.svg?longCache=true&style=flat-square"></a><!--
  -->
  <a title="Build Status" href="https://travis-ci.com/dbhi/qus/builds"><img src="https://img.shields.io/travis/com/dbhi/qus/main.svg?longCache=true&style=flat-square&logo=travis-ci&logoColor=fff&label=travis"></a><!--
  -->
  <a title="'Test' workflow Status" href="https://github.com/dbhi/qus/actions?query=workflow%3ATest"><img alt="'Test' workflow Status" src="https://img.shields.io/github/workflow/status/dbhi/qus/Test/main?longCache=true&style=flat-square&logo=github&label=Test"></a>
</p>

*qemu-user-static* (**qus**) is a compilation of utilities, examples and references to build and execute OCI images (aka [docker](https://www.docker.com/) images) for foreign architectures using [QEMU](https://www.qemu.org/)'s user-mode emulation.

- Ready-to-use docker images are provided for each of eight host architectures officially supported by Docker, Inc. or built by official images ([docker-library/official-images: Architectures other than amd64?](https://github.com/docker-library/official-images#architectures-other-than-amd64)): `amd64`, `i386`, `arm64v8`, `arm32v7`, `arm32v6`, `s390x`, `ppc64le` and `mips64le`.
- Multiple minimal working setups to build and execute `arm64v8` containers on `amd64` are configured and tested on [GitHub Actions](https://github.com/dbhi/qus/actions) and on [Travis CI](https://travis-ci.com/dbhi/qus/builds). The full flow is public, for other users to learn and adapt these resources to their needs.
- These resources are tested on GNU/Linux and Windows 10 (Docker Desktop). Contributions to test them on other host OSs are welcome!

Find further details at [dbhi.github.io/qus](https://dbhi.github.io/qus).

# Usage

> NOTE: Although `docker` is used in these examples, users have reported that other engines such as [podman](https://podman.io/) can also be used. See also [kata-containers/runtime#1280](https://github.com/kata-containers/runtime/issues/1280).

## Setup

The recommended approach is to run the following container:

``` bash
docker run --rm --privileged aptman/qus -s -- -p [TARGET_ARCH]
```

> NOTE: since `aptman/qus` is a manifest, this command works on `amd64`, `arm64v8`, `arm32v7`, `arm32v6`, `i386`, `s390x` or `ppc64le` hosts.

The required `qemu-*-static` binaries (which are all included in the image) will be loaded and registered. The container will then exit. From there on, images and/or binaries for foreign architectures can be executed.

Optional argument `TARGET_ARCH` is the target architecture to be translated through QEMU. If it is omitted, all available targets will be registered and loaded. The supported values are the following:

```
i386 i486 alpha arm armeb sparc32plus ppc ppc64 ppc64le m68k mips mipsel mipsn32 mipsn32el mips64 mips64el sh4 sh4eb s390x aarch64 aarch64_be hppa riscv32 riscv64 xtensa xtensaeb microblaze microblazeel or1k x86_64
```

> NOTE: sudo privileges on the host are required in order to register `binfmt` formats.
> On GNU/Linux, it is possible to execute `register.sh` directly.
> On Windows, a container must be used, so that changes are applied to the underlying VM, since no kernel is available on the host.
> I.e., from the [test list](https://dbhi.github.io/qus/#tests), only `C`, `V`, `I` or `D` will work on Windows.

## Reset

In order to unset the registered formats, and unload the binaries, run:

``` bash
docker run --rm --privileged aptman/qus -- -r
```

## Bandwidth-efficient procedure

In contexts such as CI pipelines it might be desirable to reduce the required bandwidth. Hence, instead of using `aptman/qus` images —which include all the binaries for all the supported target architectures—, individual tarballs are available through GitHub Releases. These can be used along with `aptman/qus:register` images or with [`register.sh`](./register.sh) (without an OCI runtime). See either `f`, `F`, `c`, `C`, `v` or `V` in [Tests](https://dbhi.github.io/qus/#tests) for examples of these use cases.
