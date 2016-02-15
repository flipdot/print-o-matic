#!/bin/bash
# Converts spender.csv file to filled out spendenbescheinigungs in PDF format

csv_dir=batch
config=geldzuwendung
csv="$csv_dir/$config.csv"

echo $csv
cat $csv

exit 23

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

