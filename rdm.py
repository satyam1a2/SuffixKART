sum = 0
num1 = 0
while num1 != -1:
    num1 = int(input())
    if num1 == -1:
        print("Exiting the program...")
    else:
        sum += num1
        print(sum)
        with open("output.txt", "a") as file:
            file.write(str(sum)+"\n")


