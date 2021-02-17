#!/usr/bin/env bash
if [[ "$1" == "Password for"* ]]; then
	cat /run/secrets/password
else
	cat /run/secrets/username
fi
