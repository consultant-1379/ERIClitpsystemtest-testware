set -x

for (( i=1; i<10002; i++ )); do
time litpcrypt delete key-for-me$i user$i
done;

