# numb = (int(input("Enter a number: ")))

# n1,n2= 0,1
# count = 0
# if numb <= 0:
#     print("enter +ve number please: ")
# elif numb == 1:
#     print(n1)
# else:
#     while count < numb :
#         print(n1)
#         n3 = n1 + n2
#         n1 = n2
#         n2 = n3
#         count += 1
       
# Recurssion 

def rec_fib(n):
    if n <= 1:
        return n
    else:
        return rec_fib(n-1) + rec_fib(n-2)
    
ntherm = int(input("Enter a number: "))

if ntherm <= 0 :
    print("enter a postive number: ")
else:
    for i in range(ntherm):
        print("I values are ",i)
        print(rec_fib(i))