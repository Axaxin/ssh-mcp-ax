# 使用官方的 Python 3.13 slim 镜像作为基础
# slim 变体包含运行 Python 所需的最少组件，减小镜像大小。
FROM python:3.13-slim-bookworm

# 设置容器内部的工作目录
WORKDIR /app

# 将 requirements.txt 复制到工作目录
# 这一步放在代码复制之前，以便 Docker 可以缓存依赖安装层。
# 如果 requirements.txt 不变，即使代码变了，也不用重新安装依赖。
COPY app/requirements.txt .

# 安装 Python 依赖
# --no-cache-dir 参数在构建时可以减少最终镜像层的大小，因为它不保留 pip 的下载缓存。
# 这只影响构建过程，不影响运行时的依赖下载。
RUN pip install --no-cache-dir -r requirements.txt

# 将整个 'app' 目录下的所有文件复制到容器的 /app 目录
#COPY app/ .

# 暴露应用程序可能监听的端口
# 如果你的 Python 应用（例如 Flask）监听特定端口，这里需要声明。
#EXPOSE 8000

# 定义容器启动时默认执行的命令
# 这是容器启动后要运行的应用程序入口。
#CMD ["python", "main.py"]