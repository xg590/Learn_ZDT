* Clone the repo
  ```sh
  git clone https://github.com/xg590/Learn_ZDT
  ```
* Use it 
  ```py
  import sys
  sys.path.append('/var/www/html/Learn_ZDT')
  from zdt import ZDTv13
  sMot = ZDTv13()
  _ , sMot.pul_cnt = sMot.getPulCnt(0x03)
  ```
* Pinout
  * <img src="./Docs/pinout.png"></img>
* 7.3 多圈有限位开关回零操作说明
  * O_Mode : EndStop # 多圈有限位开关回零
  * O_POT_En: Enable # 上电自动触发回零功能
<img src="./Docs/o_mode.jpg"></img>
* 如何知道是否是光耦隔离版本: 光耦版本少三个元件</br>
  <img src="./Docs/PLCvsOpti.png"></img>
