# class book:
#     def __init__(self,title,author,price):
#         self.title = title
#         self.author = author
#         self.price = price 
#     def get_details(self):
#         print(f"{self.title} {self.author} {self.price}")
# b1 = book("book1","author1",100)
# b1.get_details()


class student:
    _name = ""
    _marks = ""

    def __init__(self,name,marks):
        self._name = name
        self._marks = marks

    def set_details(self,name,marks):
        self._name = name
        if marks >= 0:
            self._marks = marks
        else:
            print("marks cannot be negative")
    
    def get_details(self):
        print(f"{self._name} {self._marks}")

s1 = student("hemanth",100)
s1.get_details()
s1.set_details("mark",200)
s1.get_details()
      