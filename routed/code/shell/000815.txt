#!/usr/bin/env bash

set -x
set -e

(cd base && docker build --rm  --pull  -t edispro/nginx-php-fpm:7.2-latest .)
