import spot


f = open("define/tiktok/LTL.txt",'r',encoding='utf-8')
lines=f.readlines()
f = open("define/tiktok/1_autumata.txt",'w',encoding='utf-8')
for line in lines:
    print("----------------")
    print(line)
    # print(spot.translate(line, 'det').to_str('HOA'))
    f.write("--START--\nProperty: "+line)
    f.writelines(spot.translate(line, 'det').to_str('HOA'))
    f.write("\n\n")
    f.flush()
f.close()