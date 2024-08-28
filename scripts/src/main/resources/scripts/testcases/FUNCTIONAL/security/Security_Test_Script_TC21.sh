set -x

for (( i=1; i<10002; i++ )); do
time litpcrypt set key-for-me$i user$i password$i
done;
