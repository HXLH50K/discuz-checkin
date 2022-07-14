# Discuz Checkin
## 项目简介
用于 **Discuz!** 论坛签到的自动化工具，没有经过任何测试，请凑合着用。  

## 简易指北
1. 首次使用前需要在对应论坛手动签到，并使用F12抓包，将所需信息填入**config.json**。
2. 推荐配合 [**server酱turbo**](https://sct.ftqq.com/) 食用报错推送功能。如果不需要，删除对应代码即可。  
3. 最常见的错误是 cookies 或 formhash 到期，需要手动抓包更新。  
4. 其他意外情况自己改代码。

## 抓包注意事项
1. 部分论坛的签到请求可能很快会被刷新掉，所以要及时停止recording。
2. 抓取的内容为
    1. 请求方式（post/get）
    2. request headers中的cookie
    3. query string parameters
    4. form data（get请求没有此项）
3. 2中会变的为cookie和form data中的formhash。

## 其他说明
1. 代码已重构，去掉了之前没什么用还难调试的一批的多线程。
2. 杂项功能不全。
3. 尽量不要使用proxy功能，目前只能支持本地代理端口。如果硬要使用，`config.json`中把`proxy=true`的网站放在`proxy=false`网站的后面。

## TODO
1. 目前获取签到结果是直接在`response.text`内匹配关键词，错误率太高（具体在函数跳转表那块），需要一种聪明的方法，但是没有思路。路过的大佬请提issue指点。
2. 读取log进行当日已签到检查的功能重构没了，等闲了写。
3. proxy实现方法粗暴，等改。
4. 进去就给个弹窗的网站可能没有搞定，不知道哪有问题，样本太少不好测试。

## 参考内容
* 部分代码参考自 [**wzdnzd/ssr-checkin**](https://github.com/wzdnzd/ssr-checkin)
