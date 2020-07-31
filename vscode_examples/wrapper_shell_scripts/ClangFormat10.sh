#!/usr/bin/bash
/opt/ohpc/pub/apps/singularity/bin/singularity exec /opt/ohpc/pub/containers/spectre_ocean.sif bash -c "/usr/local/bin/clang-format ${@}"
