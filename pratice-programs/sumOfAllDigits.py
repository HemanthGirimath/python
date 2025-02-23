def sum_of_digits(n,sum =0):
    if n == 0:
        return 0 
    else:
        for i in str(n):
            sum += int(i)
        return sum

print(sum_of_digits(123))