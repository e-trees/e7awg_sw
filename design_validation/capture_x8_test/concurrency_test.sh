#!/bin/sh
cd `dirname $0`
num=0
num_repeats=2
while [ $num -lt $num_repeats ]
do
    echo "loop = "$num
    python capture_x8_test.py --result-dir=proc_0 --capture-module=0 --num-tests=10 > result_0.txt 2>&1 &
    pid0=$!
    python capture_x8_test.py --result-dir=proc_1 --capture-module=1 --num-tests=10 > result_1.txt 2>&1 &
    pid1=$!
    wait $pid0
    res0=$?
    wait $pid1
    res1=$?

    if [ "$res0" -ne 0 ] || [ "$res0" -ne 0 ]; then
        echo "-- error --"
        echo "  res 0 = "$res0
        echo "  res 1 = "$res1
        exit 1
    fi
    let num++
done

echo "success"
exit 0
