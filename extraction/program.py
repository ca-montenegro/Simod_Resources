def SeatingStudents(arr):
    amount = arr[0]
    students = arr[1:]
    relation = dict()
    for i in range(1, amount):
        if i not in students:
            if i % 2 == 0:
                if i + 2 <= amount and i + 2 not in students:
                    next_num = i + 2
                    if i not in relation:
                        relation[i] = [next_num]
                    else:
                        relation[i].append(next_num)
                else:
                    continue
            else:
                if i + 2 < amount and i + 2 not in students:
                    next_num1 = i + 2
                    if i not in relation:
                        relation[i] = [next_num1]
                    else:
                        relation[i].append(next_num1)
                if i + 1 < amount and i + 1 not in students:
                    next_num2 = i + 1
                    if i not in relation:
                        relation[i] = [next_num2]
                    else:
                        relation[i].append(next_num2)
                else:
                    continue
    print(len(relation.values())+1)

    # code goes here
    return arr


# keep this function call here

import string


def SimplePassword(str):

    if (any(s.isupper() for s in str)
        and any(s.isdigit() for s in str)
        and (len(str) > 7 and len(str) < 31)
        and (s in string.punctuation for s in str)
        and "password" not in str.lower()):
        return True

    # code goes here
    return False


# keep this function call here



def main(argv):
    # keep this function call here
    print(SimplePassword(argv))

if __name__ == "__main__":
    main("turkey90AAA=")