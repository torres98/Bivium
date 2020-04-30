import re
from file_handler import open_file, close_file

total_time = 0.

for i in range(1, 9):

    file = open(f"test_result/top{i}.txt", "r")

    for line in file.readlines():

        user_time = re.match("^user\s(\d+)m(\d+,\d+)s$", line)

        if user_time:
            total_time += float(user_time.group(1)) * 60. + float(user_time.group(2).replace(",", "."))
            break

    file.close()

file = open_file("test_result/performance")
print(f"Avg Time: {total_time / 8}")
close_file(file)