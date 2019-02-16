#!/bin/env sh

function test_is_number()
{
    re='^[0-9]+$'
    if ! [[ $1 =~ $re ]] ; then
       echo "$1 is not a number" >&2; exit 2
    fi
}

if [ -z "$1" ]; then
    echo "missing argument: file to dump content" >&2; exit 1
fi

FILE_PATH=$1
LOOP=$2
SLEEP=$3
EXIT_CODE=$4

if [ -z "$LOOP" ]; then
    LOOP="default"
fi

if [ "$LOOP" = "default" ]; then
    LOOP=10
fi

if [ -z "$SLEEP" ]; then
    SLEEP=0
fi

if [ -z "$EXIT_CODE" ]; then
    EXIT_CODE=0
fi

test_is_number $LOOP
test_is_number $SLEEP
test_is_number $EXIT_CODE

CONTENT=""
i=0
while [ $i -lt $LOOP ]
do
    CONTENT="${CONTENT}$i"
    echo $i
    sleep $SLEEP
    i=`expr $i + 1`
done

echo "$CONTENT" > $FILE_PATH

exit $EXIT_CODE
