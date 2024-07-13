ls = [[('2021/321', 'sadas'), ('2021/232', 'rasas'), (['2021/323', 'aaasds'], ['dasdasdas', 'adsdasda'])], [('2021/321', 'sadas'), ('2021/232', 'rasas'), (['2021/323', 'aaasds'], ['dasdasdas', 'adsdasda'])]]
for i in ls:
    print(i[0])
    print(i[1])
    for j in i[2]:
        print(j)

