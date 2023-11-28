#!/bin/bash
set -eux
set -o pipefail

SCRIPT_DIR=$(cd $(dirname $0); pwd)

cd "${SCRIPT_DIR}/../../"

export APPLICATION_ENV=${APPLICATION_ENV:-dev}
export AWS_REGION=${AWS_REGION:-ap-northeast-1}

docker-compose -f docker-compose.deploy-fastapi.yml build
