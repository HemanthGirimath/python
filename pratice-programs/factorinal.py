
# num = int(input("Enter a int number: "))

# factorial=1
# if num<0:
#     print("cant find fact for 0")
# elif num==0:
#     print("factorial of 0 is 1")
# else:
#     for i in range(1,num+1):
#         factorial *= i
#     print(factorial)


# numb = int(input("Enter a int number: "))
# i=1
# fact = 1
# while i<=numb:
#     fact = fact * i
#     i=i+1
# print(fact)


def fact(numb):
    if numb ==0 or numb ==1:
        return 1
    else:
        return (numb * fact(numb-1))

print(fact(5))