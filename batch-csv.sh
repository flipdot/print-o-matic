#!/bin/bash
# Converts spender.csv file to filled out spendenbescheinigungs in PDF format
csv=spender.csv
config=geldzuwendung

cd "$(dirname "$0")"
IFS=';' read -ra k <<< "$(head -n1 $csv)"

while read line; do
	a="$config "
	IFS=';' read -ra v <<< "$line"
	for i in $(seq 0 $((${#k[@]}-1))); do
		a+="${k[$i]}=\"${v[$i]}\" "
	done
	eval ./fill-form.py $a
done <<< "$(tail -n+2 $csv)"

