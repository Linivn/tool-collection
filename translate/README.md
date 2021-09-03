# translate tool

### 安装依赖

> 理论上支持 `python3.0` 以上版本，[Gooey](https://github.com/chriskiehl/Gooey)

```bash
# 进入到 requirements.txt 文件所在目录，运行以下命令
pip install -r requirements.txt
```

---

### 使用

- 文件格式：新增翻译`add.json`

```text
# add.json
# 该文件用来保存新增翻译的内容
# 新增翻译时，需先在此文件中添加内容，再进行翻译
{
  "category1": {
    "group1": {
      "key1": "value",
      ...
    }
  },
  "category2": {
    ...
  }
}
```

- 配置
    - main_command-line.py
  ```python
  # 运行前需要先在代码中进行相关配置
  configure = {
      'translate': {  # 翻译工具配置项
          'service_urls': ('translate.google.cn',), # googletrans service_urls 如有科学上网可以不用配置
          # 'proxy': 'http://127.0.0.1:10809', # 代理
          'path': '',  # 翻译文件所在文件目录
      }
  }
  ```

    - main_command-line.py
  ```python
  # 在项目根目录创建 config.json 文件，用来配置代理、谷歌翻译源
  {
      "setting": {
        "service_urls": "translate.google.cn", # 谷歌翻译源
        "proxy": {
          "enable": false, # 代理开关
          "host": "http://127.0.0.1:10809" # 代理地址
        }
      }
  }
  ```

- 运行

```bash
# 基本用法参考 mian_xxx.py
# 需要使用什么功能，放开注释即可

# main_command-line.py => 命令行版本
# main_gooey_gui.py => 图形界面版本

# 运行
python mian_xxx.py
```

> translate.py: google翻译工具 <br/>
> ~~update.py: 某翻译系统相关工具，用于新增、删除、修改、查询翻译~~ 忽略

> 翻译多语言：读取 `add.json` 文件中内容，将其翻译成多语言并保存，每次仅翻译添加部分（会先比较 `add.json` 与 `zh_cns.json` 的差异）
>
> 使用步骤：
> 1. 在 `add.json` 中添加新增翻译内容
> 2. 调用 `Translate.translate` 翻译成其他语言（仅翻译添加部分），并将翻译结果保存到相应的文件中
> 3. 返回翻译结果（如无新增内容，则读取 `results` 文件夹下的所有文件内容返回）

---

### Note

- googletrans 不能直接使用，设置代理、超时时间等无效，需要修改源代码才能正常使用

```
// 修改 googletrans/client.py 的 __init__ 部分代码
# 注释以下代码
# if proxies is not None:  # pragma: nocover
#     self.client.proxies = proxies
# if timeout is not None:
#     self.client.timeout = timeout

# 初始化 httpx.Client 改为以下代码
self.client = httpx.Client(http2=http2, timeout=timeout, proxies=proxies)
```

- gooey打包成可执行程序

```shell
pyinstaller build.spec
```