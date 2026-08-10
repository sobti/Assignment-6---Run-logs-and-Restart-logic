#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 LOGS_PATH"
    exit -1
fi


BASE_DIR=$1
SEPARATOR="\\t"

total=$(grep -iE '\UE\[|\[UE' ./$BASE_DIR/full.log | sed 's/\[//g' | sed 's/.*UEimsi-20893\([0-9]\+\)[^0-9].*/\1/' | sort -nr | head -1)
i=1
echo "UE;Initial Time;End Time;Complete"
line=1
while [ $i -le $total ]; do
    infile=$(grep -rin 'REGISTRATION REQUEST' ./$BASE_DIR/UE_$i.log | wc -l)
    j=1
    while [ $j -le $infile ]; do
        init=$(awk "/REGISTRATION REQUEST/{i++}i==$j" ./$BASE_DIR/UE_$i.log | head -n 1 | sed 's/.*time="\([^"]\+\)".*/\1/')
        end=$(awk "/REGISTRATION REQUEST/{i++}i==$j" ./$BASE_DIR/UE_$i.log | tail -n 1 | sed 's/.*time="\([^"]\+\)".*/\1/')
        completed=$(awk "/REGISTRATION REQUEST/{i++}i==$j" ./$BASE_DIR/UE_$i.log | grep "REGISTRATION FINISHED" | wc -l)
        echo -e "$line$SEPARATOR$init$SEPARATOR$end$SEPARATOR$completed"
        line=$((line+1))
        j=$((j+1))
    done
    i=$((i+1))
done
