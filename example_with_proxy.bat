@echo off
echo 使用代理地址运行音频分类器示例
echo 请将YOUR_API_KEY替换为您的实际Gemini API密钥
echo 请将AUDIO_DIRECTORY替换为您的音频文件目录

python audio_classifier.py --directory AUDIO_DIRECTORY --api_key YOUR_API_KEY --proxy http://127.0.0.1:10809

pause