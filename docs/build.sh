#!/bin/bash

# See http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail
IFS=$'\n\t'

project_dir="$(git rev-parse --show-toplevel)"

function docker_asciidoctor() {
    docker run --rm --user "$(id -u):$(id -g)" --volume "${project_dir}:/project/" asciidoctor/docker-asciidoctor "$@"
}

docker_asciidoctor asciidoctor -a linkcss /project/docs/index.adoc -D /project/build/gh-pages/
docker_asciidoctor asciidoctor-pdf /project/docs/index.adoc -o /project/build/gh-pages/ue4-docker.pdf
docker_asciidoctor asciidoctor-epub3 /project/docs/index.adoc -o /project/build/gh-pages/ue4-docker.epub
