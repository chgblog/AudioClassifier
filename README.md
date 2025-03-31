# 音频分类器 (Audio Classifier)

这是一个使用Google Gemini API对音频文件进行分析和分类的工具。

中文 | [English](README_EN.md)

## 功能

- 扫描指定目录及其子目录中的所有支持的音频文件
- 使用Gemini AI分析每个音频文件的内容
- 为每个音频生成内容描述、使用场景和标签
- 将分析结果保存到Excel文件中
- 支持API请求限制处理，自动等待并重试

## 支持的音频格式

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- FLAC (.flac)
- AAC (.aac)
- OGG (.ogg)

## 安装依赖

你可以使用以下命令一次性安装所有依赖：

```bash
pip install -r requirements.txt
```

或者手动安装各个依赖：

```bash
pip install pandas google-generativeai tqdm openpyxl
```

## 使用方法

```bash
python audio_classifier.py --directory "音频文件目录" --api_key "您的Gemini API密钥" [--output "输出文件路径"] [--max_retries 重试次数] [--retry_delay 等待秒数] [--proxy "代理服务器地址"]
```

### 参数说明

- `--directory`, `-d`: 音频文件目录路径（必需）
- `--api_key`, `-k`: Gemini API密钥（必需）
- `--output`, `-o`: 输出Excel文件路径（可选，默认为当前目录下的audio_classification_results.xlsx）
- `--max_retries`, `-r`: API请求失败时的最大重试次数（可选，默认为60）
- `--retry_delay`, `-t`: API请求失败后重试的等待时间，单位为秒（可选，默认为60）
- `--category_dir`, `-c`: 分类后的音频文件存放目录（可选，默认为当前目录下的"分类音频"文件夹）
- `--proxy`, `-p`: HTTP/HTTPS代理服务器地址（可选，格式如：http://127.0.0.1:7890）
- `--model`, `-m`: 使用的Gemini模型名称（可选，默认为gemini-2.0-flash-001）

### 代理设置说明

如果您在访问Gemini API时需要使用代理，可以通过`--proxy`参数指定代理服务器地址。代理地址格式应为完整的URL，包括协议（http或https）、主机名和端口号，例如：

```bash
python audio_classifier.py --directory "音频文件目录" --api_key "您的Gemini API密钥" --proxy "http://127.0.0.1:7890"
```

该设置将同时应用于HTTP和HTTPS请求。

## 输出文件

程序会在指定的输出路径（或默认路径）生成一个Excel文件，包含以下信息：

- 音频文件路径
- 分类后路径（音频文件分类后的新位置）
- 主分类（从标签中提取的主要分类）
- 音频内容描述
- 使用场景建议
- 标签列表
- 失败原因（如果有）

**注意**：如果未指定输出文件的绝对路径，Excel文件将保存在当前工作目录下。程序运行完成后会在控制台显示输出文件的完整路径。

## 错误处理

- 当API请求超出配额限制时，程序会自动等待指定时间后重试
- 如果重试后仍然失败，会继续等待并重试，直到成功或达到最大重试次数
- 所有错误和警告都会记录在`audio_classifier.log`文件中