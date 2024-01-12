lcb = 10305
pc1 = 1300
pc2 = 1067
tc = 50

mot_gio = lcb/26/8

mot_ngay = lcb/26

mot_gio_tang_ca = mot_gio * 1.5

mot_thang_tang_ca = mot_gio_tang_ca * 50

all = lcb + lcb/26/8*1.5*43.5 + pc1 + pc2 - lcb*0.105 - 170
print(all)
print(mot_gio, '1h')
print(mot_gio_tang_ca, 'tang ca 1h')
print(mot_gio_tang_ca*2.5, 'tang ca 1 ngay')
print(mot_ngay, 'luong 1 ngay')
print(mot_thang_tang_ca, 'luong 1 thang tang ca')
