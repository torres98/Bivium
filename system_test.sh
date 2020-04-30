python3 system_test.py

for i in {1..8}
do
   (time ./cryptominisat5-linux-amd64-gauss --verb 0 test_cnf/top$i.cnf) > test_result/top$i.txt 2>&1
   #(time ./cryptominisat5-linux-amd64-nogauss --verb 0 test_cnf/top$i.cnf) >> test_result/top$i.txt 2>&1
done

python3 performance.py
