#!/bin/bash
cd `dirname $0`
num=0
num_repeats=2
while [ $num -lt $num_repeats ]
do
    echo "loop = "$num
    python capture_x8_test.py --result-dir=proc_0 --capture-module=0 --num-tests=5 --ipaddr=127.0.0.1 > result_0.txt 2>&1 &
    pid0=$!
    python capture_x8_test.py --result-dir=proc_1 --capture-module=1 --num-tests=5 --ipaddr=127.0.0.1  > result_1.txt 2>&1 &
    pid1=$!
    python capture_x8_test.py --result-dir=proc_2 --capture-module=2 --num-tests=5 --ipaddr=127.0.0.1  > result_2.txt 2>&1 &
    pid2=$!
    python capture_x8_test.py --result-dir=proc_3 --capture-module=3 --num-tests=5 --ipaddr=127.0.0.1  > result_3.txt 2>&1 &
    pid3=$!
    wait $pid0
    res0=$?
    wait $pid1
    res1=$?
    wait $pid2
    res2=$?
    wait $pid3
    res3=$?

    if [ "$res0" -ne 0 ] || [ "$res1" -ne 0 ] || [ "$res2" -ne 0 ] || [ "$res3" -ne 0 ]; then
        echo "-- error --"
        echo "  res 0 = "$res0
        echo "  res 1 = "$res1
        echo "  res 2 = "$res2
        echo "  res 3 = "$res3
        exit 1
    fi
    let num++
done

echo "success"
exit 0
