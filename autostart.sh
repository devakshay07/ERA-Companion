#!/bin/bash
WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
"$WORKSPACE/start_era.sh"
"$WORKSPACE/start_avatar.sh"
