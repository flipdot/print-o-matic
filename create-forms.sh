#!/bin/bash
# Converts spender.csv file to filled out spendenbescheinigungs in PDF format
cd "$(dirname "$0")"
while IFS=\; read name street city value date; do
	python3 spende.py "$name" "$street" "$city" "$value" "$date"
done <<< "$(tail -n+2 spender.csv)"
