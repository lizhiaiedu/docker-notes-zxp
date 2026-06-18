# docker\-vllm\-教学讲义

# Docker 与 vLLM 部署教学讲义（详细原理版）

> 适用对象：有基本 Linux 命令行经验、想真正理解容器底层原理并能上手部署 LLM 推理服务的学生
学习路径：基础概念 → 核心对象 → 实操命令 → Dockerfile → 编排 → **内部原理（重点）** → vLLM 实战与原理

> **关于图**：本讲义中的原理图使用 Mermaid 绘制，可在 GitHub、Typora、Obsidian、VS Code（装 Mermaid 插件）等环境直接渲染。若你的查看器不支持，可把代码块贴到 [mermaid\.live](https://mermaid.live) 在线查看。

---

## 第一部分　为什么需要 Docker

### 1\.1 一个真实的痛点

你写好一段代码，在自己电脑上跑得好好的。交给同学，他报错；部署到服务器，又报错。原因往往不是代码本身，而是**环境不一致**：Python 版本不同、依赖库版本冲突、系统缺少某个底层库、环境变量没配……这就是经典的「在我机器上能跑」问题。

Docker 的核心价值就是把**应用 \+ 它需要的所有依赖 \+ 运行环境**打包成一个标准化的单元，让它在任何装了 Docker 的机器上都以完全相同的方式运行。

### 1\.2 什么是容器

容器（Container）是一个**轻量级、可移植、自包含**的软件运行单元。可以把它理解为：一个被隔离起来的进程，它拥有自己看起来独立的文件系统、网络和进程空间，但又共享宿主机的操作系统内核。

一句话类比：集装箱（Container 本意就是集装箱）。不管箱子里装的是衣服还是机器，码头的吊车、货轮、卡车都用同一套标准来搬运。Docker 就是「集装箱标准 \+ 搬运工具」。

\!\[image\-20260531100633726\]\(/Users/zhangxiaopa/Library/Application Support/typora\-user\-images/image\-20260531100633726\.png\)

### 1\.3 容器 vs 虚拟机（架构对比图）

这是最常被问到的问题，必须讲清楚。先看两者的架构差异：

```Plaintext
flowchart TB
  subgraph VM["虚拟机 (VM) 架构"]
    direction TB
    VH["物理硬件"]
    VHV["Hypervisor 虚拟机管理程序"]
    VG1["Guest OS 1<br/>(完整操作系统内核)"]
    VG2["Guest OS 2<br/>(完整操作系统内核)"]
    VA1["App A + 依赖"]
    VA2["App B + 依赖"]
    VH --> VHV
    VHV --> VG1 --> VA1
    VHV --> VG2 --> VA2
  end

  subgraph CT["容器 (Container) 架构"]
    direction TB
    CH["物理硬件"]
    COS["宿主机操作系统<br/>(一个共享内核)"]
    CD["Docker Engine"]
    CC1["容器1<br/>App A + 依赖"]
    CC2["容器2<br/>App B + 依赖"]
    CH --> COS --> CD
    CD --> CC1
    CD --> CC2
  end
```

看图说话：**虚拟机里每个应用都背着一整套操作系统**，所以又大又慢；**容器共享宿主机的同一个内核**，只打包应用和依赖，所以又小又快。

|对比项|虚拟机（VM）|容器（Container）|
|---|---|---|
|隔离层级|模拟整套硬件，运行完整的 Guest OS|共享宿主机内核，只隔离进程|
|启动速度|分钟级|秒级甚至毫秒级|
|资源占用|每台 VM 都要一份完整 OS，GB 级|只打包应用和依赖，MB 级常见|
|性能|有 Hypervisor 开销|接近原生|
|隔离强度|强（硬件级）|较弱（内核级，靠 namespace/cgroups）|

记住关键差异：**虚拟机虚拟化的是硬件，容器虚拟化的是操作系统。** 容器没有自己的内核，所以才这么轻、这么快。代价是隔离性不如虚拟机，且容器只能跑和宿主机内核兼容的系统（Linux 容器需要 Linux 内核）。

### 📝 第一部分小测

**单选题**

1. 容器与虚拟机最核心的区别是？

    - A\. 容器更贵，虚拟机更便宜

    - B\. 容器虚拟化操作系统、共享宿主机内核；虚拟机虚拟化硬件、各带完整 OS

    - C\. 容器只能跑 Python，虚拟机什么都能跑

    - D\. 两者没有本质区别，只是名字不同

2. 容器启动通常是秒级甚至毫秒级，最主要的原因是？

    - A\. 容器用了更快的硬盘

    - B\. 容器不需要启动一整套独立的操作系统内核，直接共享宿主机内核

    - C\. 容器把代码编译成了机器码

    - D\. 容器运行在内存里不落盘

3. 下列说法正确的是？

    - A\. Linux 容器可以直接在没有 Linux 内核的环境里裸跑

    - B\. 虚拟机的隔离强度通常弱于容器

    - C\. 容器隔离性不如虚拟机，是共享内核换来轻量的代价

    - D\. 容器一定比虚拟机更安全

**解答题**

4. 用你自己的话解释「在我机器上能跑」问题为什么会发生，以及 Docker 是怎么解决它的。

📖 参考答案

1. **B**　2\. **B**　3\. **C**

4. 该问题源于**环境不一致**：不同机器的语言版本、依赖库版本、系统底层库、环境变量等存在差异，导致同一份代码行为不同。Docker 把**应用 \+ 全部依赖 \+ 运行环境**一起打包成标准化的镜像，在任何装了 Docker 的机器上都以相同方式运行，从而消除环境差异。

---

## 第二部分　核心概念（必须烂熟）

理解 Docker 只需抓住几个对象，它们之间的关系是整个体系的骨架。

### 2\.1 镜像 Image

镜像是一个**只读的模板**，包含运行某个应用所需的一切：代码、运行时、库、环境变量、配置。它是「类」，是静态的。镜像由**多个只读层（layer）叠加**而成，每一层对应构建过程中的一步操作。这种分层设计是 Docker 高效的关键。

### 2\.2 容器 Container

容器是**镜像的运行实例**。它是「对象」，是动态的。同一个镜像可以同时跑出多个容器，彼此隔离。
容器 = 镜像（只读层）\+ 一个可写层。你在容器里产生的所有改动都写在这个可写层里，删除容器时这一层默认也消失（所以需要数据卷来持久化）。

### 2\.3 仓库 Registry / Repository

仓库是存放镜像的地方，类似 GitHub 之于代码。

- **Docker Hub**：官方公共仓库，`docker pull nginx` 默认就从这里拉。

- **私有仓库**：企业内部常自建（如 Harbor），或用云厂商的镜像服务。

- 镜像命名规则：`[仓库地址/]命名空间/镜像名:标签`，例如 `vllm/vllm-openai:latest`。

### 2\.4 Dockerfile

Dockerfile 是一个**文本文件**，里面是一条条指令，描述「如何一步步构建出一个镜像」。它是镜像的「源代码」。`docker build` 读取它，生成镜像。

### 2\.5 数据卷 Volume

需要持久化的数据（数据库文件、模型权重、日志）必须放在**数据卷**里。卷独立于容器生命周期，挂载到容器内的指定路径。

### 2\.6 网络 Network

Docker 为容器提供虚拟网络。默认是 `bridge` 模式，端口需要用 `-p 宿主机端口:容器端口` 映射出来才能从外部访问。

### 核心对象关系图

```Plaintext
flowchart LR
  DF["Dockerfile<br/>(构建说明)"] -->|docker build| IMG["镜像 Image<br/>(只读模板)"]
  IMG -->|docker run| CON["容器 Container<br/>(运行实例)"]
  IMG -->|docker push| REG["仓库 Registry<br/>(Docker Hub 等)"]
  REG -->|docker pull| IMG
  VOL["数据卷 Volume"] -.挂载.-> CON
  NET["网络 Network"] -.连接.-> CON
```

### 📝 第二部分小测

**单选题**

1. 关于镜像（Image）和容器（Container）的关系，正确的是？

    - A\. 镜像是动态运行的，容器是静态模板

    - B\. 一个镜像只能运行出一个容器

    - C\. 镜像是只读模板（像「类」），容器是它的运行实例（像「对象」），一个镜像可跑出多个容器

    - D\. 容器和镜像是完全独立、互不相关的两个东西

2. 你在运行中的容器里新建了一个文件，然后把容器删除（`docker rm`）。这个文件会怎样？

    - A\. 自动保存到镜像里

    - B\. 默认随容器的可写层一起消失

    - C\. 自动上传到 Docker Hub

    - D\. 永久保存在宿主机任意位置

3. 镜像名 `vllm/vllm-openai:latest` 中的 `latest` 是？

    - A\. 仓库地址

    - B\. 命名空间

    - C\. 标签（tag）

    - D\. 容器 ID

**解答题**

4. 用一两句话描述 Dockerfile、镜像、容器、仓库四者之间的转换关系（即哪个命令把什么变成什么）。

📖 参考答案

1. **C**　2\. **B**（这正是需要数据卷 Volume 来持久化的原因）　3\. **C**

4. **Dockerfile** 经 `docker build` 构建成**镜像**；**镜像**经 `docker run` 运行成**容器**；**镜像**可经 `docker push` 推送到**仓库**，也可经 `docker pull` 从仓库拉取下来。

---

## 第三部分　安装与基本操作

### 3\.1 安装

- **Linux 服务器**：

```Bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # 加入 docker 组免 sudo，需重新登录
```

- **Windows / macOS**：安装 Docker Desktop（自带一个轻量 Linux 虚拟机，因为容器本质要跑在 Linux 内核上）。

验证：`docker version`、`docker run hello-world`。

### 3\.2 镜像命令

```Bash
docker pull nginx:1.27 
docker images
docker rmi nginx:1.27
docker build -t myapp:v1 .
docker tag myapp:v1 user/myapp:v1
docker push user/myapp:v1
```

### 3\.3 容器命令（最常用）

```Bash
docker run -d -p 8080:80 --name web nginx
docker ps                # 运行中；-a 看全部
docker stop/start/restart web
docker rm web
docker logs -f web       # 排错第一步：看日志
docker exec -it web bash # 进入容器内部调试
docker inspect web       # 查看详细元数据
docker stats             # 实时资源占用
```

### 3\.4 常用运行参数速查

|参数|作用|
|---|---|
|`-d`|后台运行|
|`-it`|交互式 \+ 终端|
|`-p 主机:容器`|端口映射|
|`-v 主机路径:容器路径`|挂载卷|
|`-e KEY=VALUE`|环境变量|
|`--name`|容器名|
|`--rm`|退出即删|
|`--restart`|重启策略|
|`--gpus all`|暴露 GPU（部署 LLM 必用）|

### 📝 第三部分小测

**单选题**

1. `docker run -d -p 8080:80 --name web nginx` 中，`-p 8080:80` 的含义是？

    - A\. 容器用 8080 端口，宿主机用 80 端口

    - B\. 把宿主机的 8080 端口映射到容器内的 80 端口

    - C\. 限制容器只能用 80MB 内存

    - D\. 容器运行 8080 秒后自动退出

2. 容器跑起来后行为异常，排错的第一步通常是？

    - A\. 立刻删除容器重建

    - B\. `docker logs` 查看容器日志

    - C\. 重启宿主机

    - D\. 重装 Docker

3. 想进入一个正在运行的容器内部、像 ssh 一样执行命令调试，应该用？

    - A\. `docker logs -f`

    - B\. `docker inspect`

    - C\. `docker exec -it <容器> bash`

    - D\. `docker stats`

**解答题**

4. 写出一组命令，完成：拉取 `nginx`，以后台方式运行并把容器 80 端口映射到宿主机 8080、命名为 `web`，查看运行状态，进入容器内部，最后停止并删除它。

📖 参考答案

1. **B**　2\. **B**　3\. **C**

4. 参考命令序列：

```Bash
docker pull nginx
docker run -d -p 8080:80 --name web nginx
docker ps
docker exec -it web bash      # 调试完 exit 退出
docker stop web
docker rm web
```

---

## 第四部分　Dockerfile 编写

### 4\.1 常用指令

```Dockerfile
FROM python:3.12-slim       # 基础镜像
WORKDIR /app                # 工作目录
ENV PYTHONUNBUFFERED=1      # 环境变量
COPY requirements.txt .     # 先拷依赖清单（利用缓存）
RUN pip install --no-cache-dir -r requirements.txt
COPY . .                    # 再拷源码
EXPOSE 8000                 # 声明端口（文档作用）
CMD ["python", "app.py"]    # 启动命令
```

指令辨析：`ENTRYPOINT` 定义固定程序、`CMD` 给默认参数；优先用 `COPY` 而非 `ADD`。

### 4\.2 分层缓存：为什么指令顺序很重要

Docker 构建**逐层缓存**：某层与上次相同就复用，**一旦某层变化，其后所有层都要重建**。

```Plaintext
flowchart TB
  subgraph 好的顺序["✅ 依赖在前，源码在后"]
    G1["FROM python (几乎不变 → 命中缓存)"]
    G2["COPY requirements.txt (很少变 → 命中缓存)"]
    G3["RUN pip install (很少变 → 命中缓存)"]
    G4["COPY . . (源码常变 → 只重建这层)"]
    G1 --> G2 --> G3 --> G4
  end
  subgraph 坏的顺序["❌ 源码在前"]
    B1["FROM python"]
    B2["COPY . . (源码一改 → 这层失效)"]
    B3["RUN pip install (被迫重装全部依赖！)"]
    B1 --> B2 --> B3
  end
```

原则：**变化越少的越往前放，变化越频繁的越往后放。**

### 4\.3 多阶段构建（瘦身镜像）

```Dockerfile
FROM golang:1.22 AS builder
WORKDIR /src
COPY . .
RUN go build -o myapp

FROM alpine:3.20            # 最终镜像只含可执行文件
COPY --from=builder /src/myapp /usr/local/bin/myapp
CMD ["myapp"]
```

### 4\.4 最佳实践

选小基础镜像；合并 RUN、清理缓存；用 `.dockerignore`；别把密钥写进镜像；以非 root 运行；一个容器只做一件事。

### 📝 第四部分小测

**单选题**

1. 为什么 Dockerfile 推荐「先 `COPY requirements.txt` 装依赖，再 `COPY . .` 拷源码」？

    - A\. 这样写代码更整洁

    - B\. 依赖层很少变可命中缓存；源码常变放最后，改代码时不必重装全部依赖

    - C\. 否则镜像无法构建

    - D\. 这样能让容器跑得更快

2. Docker 镜像分层缓存的关键规则是？

    - A\. 任何一层变化都不影响其他层

    - B\. 只有第一层变化才会重建

    - C\. 某一层变化后，它之后的所有层都要重建

    - D\. 缓存与指令顺序无关

3. 多阶段构建（multi\-stage build）的主要目的是？

    - A\. 让构建速度变慢但更安全

    - B\. 把编译工具链留在最终镜像里

    - C\. 只把构建产物拷进干净的运行镜像，显著缩小最终镜像体积

    - D\. 支持多个人同时构建

**解答题**

4. 一句话概括 Dockerfile 指令排序的核心原则，并说明它和分层缓存的关系。

📖 参考答案

1. **B**　2\. **C**　3\. **C**

4. 核心原则：**变化越少的指令越往前放，变化越频繁的越往后放。** 因为 Docker 逐层缓存、且某层一变其后所有层都要重建；把稳定的（如装依赖）放前面能长期命中缓存，把易变的（如源码）放后面则只重建最后几层，大幅加快构建。

---

## 第五部分　Docker Compose（多容器编排）

```YAML
services:
  web:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgres://db:5432/app
    depends_on: [db]
  db:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=secret
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

命令：`docker compose up -d` / `ps` / `logs -f` / `down`。

### demo1代码案例

```Bash
# 后台运行
docker compose -f demo1/docker-compose.yml up -d --build

# 看日志
docker compose -f demo1/docker-compose.yml logs -f --tail=200

# 停止并删除容器（保留数据卷）
docker compose -f demo1/docker-compose.yml down

# 连数据也一起删（会清空 Postgres 数据）
docker compose -f demo1/docker-compose.yml down -v
```

### 📝 第五部分小测

**单选题**

1. Docker Compose 主要解决什么问题？

    - A\. 让单个容器跑得更快

    - B\. 用一个 YAML 文件统一定义并一键启停多个相互关联的容器服务

    - C\. 替代 Dockerfile 构建镜像

    - D\. 给容器加密

2. Compose 文件里 `depends_on` 的作用是？

    - A\. 限制容器内存

    - B\. 声明服务之间的启动依赖关系

    - C\. 指定镜像版本

    - D\. 设置端口映射

**解答题**

3. 一个「Web \+ 数据库」的应用，用手工 `docker run` 和用 Compose 部署相比，Compose 的优势体现在哪里（说出至少两点）？

📖 参考答案

1. **B**　2\. **B**

3. 优势例如：① 一个 YAML 把所有服务、端口、卷、环境变量、依赖关系集中描述，`docker compose up` 一条命令全部拉起，无需逐个敲长命令；② 配置可纳入版本管理、便于团队协作和复现；③ 统一管理服务的启停、日志、网络，可声明依赖顺序。（答出其中两点即可）

---

## 第六部分　内部原理（核心重点）

这一部分是本讲义的灵魂。很多人会用 Docker，但说不清它凭什么能隔离。先给出**贯穿全章的一句话**：

> **Docker 不是黑魔法。它没有发明新东西，只是把 Linux 内核里早已存在的几项能力组合了起来。容器，本质上就是一个被特殊「布置」过的普通 Linux 进程。**

这些能力主要是三件套：**Namespace（隔离视图）、Cgroups（限制资源）、UnionFS（分层存储）**，再加上把它们组装起来的**容器运行时**。下面逐一拆解。

### 6\.1 Namespace —— 解决「看得见什么」（隔离视图）

#### 它在做什么

普通进程能看到整台机器：所有进程、所有网卡、整个文件系统。Namespace（命名空间）的作用是给一组进程**蒙上眼罩**，让它们只能看到被分配的那一部分资源，误以为自己独占整台机器。

Linux 内核通过 `clone()` / `unshare()` / `setns()` 这几个系统调用来创建和加入 namespace。创建容器时，runc 就是用带 `CLONE_NEWPID`、`CLONE_NEWNET` 等标志的 `clone()` 把新进程放进一组全新的 namespace。

#### 六类主要 namespace

|类型|隔离的东西|容器里的效果|
|---|---|---|
|**PID**|进程号|容器内进程从 1 号开始编号，看不到宿主机和别的容器的进程|
|**NET**|网络栈|独立的网卡、IP、端口、路由表|
|**MNT**|挂载点|独立的文件系统视图，这是容器有「自己的根目录」的基础|
|**UTS**|主机名/域名|容器可有独立 hostname|
|**IPC**|进程间通信|独立的信号量、消息队列、共享内存|
|**USER**|用户/组 ID|容器内的 root 可映射成宿主机的普通用户，增强安全|

```Bash
#现在的发现：但在 expensehub-mariadb 容器的 ps aux 结果里，一个也看不见。这就是隔离
docker exec -it demo1-db-1 ps aux  
#一个类似 172.18.0.x 的 IP。
docker inspect demo1-backend-1 | grep IPAddress
# 挂载点 看看是不是有 /bin, /etc, /var, /lib 这些文件夹。
docker exec -it demo1-backend-1 ls /
#3. UTS Namespace (主机名) —— 看看它叫什么
docker exec -it expensehub-mariadb hostname
#4. USER Namespace (用户隔离) —— 看看它是谁
docker exec -it expensehub-mariadb id
#5. IPC Namespace (进程间通信) —— 看看它的私密对话
docker exec -it demo1-backend-1 ipcs -a
# 挂载点
docker exec -it expensehub-mariadb mount
```

#### 关键图示：同一个内核，不同的视图

```Plaintext
flowchart TB
  subgraph HOST["宿主机（所有容器共享同一个 Linux 内核）"]
    direction TB
    KERNEL["Linux Kernel"]
    subgraph NSA["容器 A 的 namespace 集合"]
      PA["进程视图: PID 1, 2, 3<br/>独立网卡 eth0 / 独立挂载 / 独立主机名"]
    end
    subgraph NSB["容器 B 的 namespace 集合"]
      PB["进程视图: PID 1, 2<br/>独立网卡 eth0 / 独立挂载 / 独立主机名"]
    end
    HOSTV["宿主机自身视图: 能看到全部真实进程<br/>(容器A/B 在这里只是普通的高编号进程)"]
  end
  NSA -.系统调用.-> KERNEL
  NSB -.系统调用.-> KERNEL
  HOSTV -.系统调用.-> KERNEL
```

#### 一个能亲手验证的例子

在容器里 `ps aux`，你看到自己的主进程是 PID 1，像个老大。但在**宿主机**上 `ps aux | grep` 同一个进程，它只是个编号很大的普通进程。**同一个进程，两个 namespace 里看到两个不同的 PID**——这就是 PID namespace 在起作用，是「容器只是进程」最直观的证据。

一句话：**Namespace 负责「隔离」——决定容器能看到什么。**

### 6\.2 Cgroups —— 解决「能用多少」（资源限制）

#### 它在做什么

光隔离视图还不够。如果一个容器疯狂申请内存，把宿主机吃光，其他容器会一起崩。**Control Groups（cgroups）负责限制、统计、隔离**一组进程的资源用量：CPU、内存、磁盘 IO、网络、可创建的进程数等。

cgroups 把进程组织成树状层级，每个节点挂上不同的「控制器（controller）」来管不同资源。现代系统多用 **cgroups v2**（统一层级）。

#### 限制是怎么生效的

- **内存**：设上限后，容器内存超限会触发内核的 **OOM Killer**（Out\-Of\-Memory，杀掉进程）。这就是为什么模型太大、显存/内存不够时容器会被「干掉」。

- **CPU**：通过 CFS（完全公平调度器）的配额机制，限制每个调度周期内能用的 CPU 时间，实现「最多 1\.5 个核」这种效果。

- **PID**：限制最多能创建多少进程，防 fork 炸弹。

```Bash
docker run -m 512m --cpus 1.5 --pids-limit 100 myapp
# 最多 512MB 内存、1.5 个 CPU、100 个进程
```

```Bash
backend:
    build: ./backend
    deploy:
      resources:
        limits:
          cpus: '1.5'      # 强制上限，绝对不能超过 1.5 核
          memory: 1G       # 内存上限
        reservations:
          cpus: '0.2'      # 预留配额，最起码保证我有 0.2 核可用
```

```Plaintext
flowchart TB
  ROOT["cgroup 根 (宿主机全部资源)"]
  ROOT --> C1["容器A 的 cgroup<br/>mem ≤ 512M / cpu ≤ 1.5核"]
  ROOT --> C2["容器B 的 cgroup<br/>mem ≤ 2G / cpu ≤ 4核"]
  ROOT --> OTHER["宿主机其他进程"]
  C1 --> P1["容器A 内的所有进程<br/>(用量超限 → OOM/限流)"]
  C2 --> P2["容器B 内的所有进程"]
```

一句话：**Cgroups 负责「限制」——决定容器能用多少。**

### 6\.3 UnionFS / OverlayFS —— 解决「文件怎么存」（分层 \+ 写时复制）

#### 分层从哪来

还记得镜像是「一层层」的吗？这就是联合文件系统（UnionFS，现代 Docker 默认实现是 **OverlayFS**）的功劳。Dockerfile 里**每一条会改变文件系统的指令，就生成一个只读层**。

OverlayFS 把这些目录叠成一个统一视图，术语：

- **lowerdir**：底下的只读层（镜像层，可多层、可被多个容器共享）只读 \(不能改\)。

- **upperdir**：最上面的可写层（每个容器独有）可读写，独占 \(隔离\)。

- **merged**：容器实际看到的、合并后的统一文件系统。

#### 写时复制（Copy\-on\-Write, COW）

容器启动时只在顶上加一个空的可写层。规则是：

- **读**：从上往下找文件，找到就用。

- **改/删**：要修改某个只读层里的文件时，先把它**复制一份到可写层**再改，**原始只读层永远不动**。删除则在可写层做一个「白障（whiteout）」标记把它遮住。
为什么我们要懂这个？
懂了这三层，你就明白了 Docker 的三个关键行为：
1、为什么容器删了数据就丢了？
因为你的数据全写在 upperdir（那张临时的空白板）上。容器一删，这张板就被扔进垃圾桶了。
解决： 所以我们要用 Volumes，它相当于在桌子上挖个洞，直接把画笔写在桌面上（宿主机硬盘），不写在玻璃板上。
2、为什么构建镜像要尽量减少层数？
因为每多一个 RUN 指令，就多一张玻璃板。叠得太厚（层数太多），内核计算 merged 画面时的性能就会下降。
3、为什么拉取镜像时会显示 Already exists？
因为 Docker 发现你本地已经有这一层 lowerdir（玻璃板）了，就不用再从网上下载一遍了，直接拿来叠加就行。

```Plaintext
flowchart TB
  MERGED["容器看到的统一视图 (merged)"]
  subgraph UPPER["可写层 upperdir（每个容器独有，容器删除即丢失）"]
    W["运行时新增/修改的文件<br/>写时复制 (Copy-on-Write)"]
  end
  subgraph LOWER["镜像只读层 lowerdir（多个容器共享，永不修改）"]
    L3["层3: COPY . . 的产物"]
    L2["层2: RUN pip install 的产物"]
    L1["层1: FROM python:3.12 基础层"]
  end
  MERGED --> UPPER
  UPPER --> L3 --> L2 --> L1
```

#### 为什么镜像能共享、容器能秒起

因为底层只读层是共享的：从同一个镜像启动 100 个容器，**并不会占用 100 份磁盘**，大家共用同一份只读层，各自只多一个很小的可写层。

```Plaintext
flowchart TB
  IMG["同一份镜像的只读层<br/>(磁盘上只存一份)"]
  IMG --> CA["容器A: 自己的可写层"]
  IMG --> CB["容器B: 自己的可写层"]
  IMG --> CC["容器C: 自己的可写层"]
```

这一下解释了三件事：① 镜像分层复用省空间；② 容器启动快（不用拷贝整个文件系统，只加一个空可写层）；③ 容器内的改动默认不持久（都在会被销毁的可写层里，所以重要数据要挂 Volume）。
省空间是因为：大家都看同一本书（只读层共享）。
启动快是因为：看书不用复印，直接翻开就能看（只加一层薄薄的可写层）。
不持久是因为：你的笔记写在了书外面的透明膜上，膜是临时的。

可写层（Writable Layer）到底写了什么？
虽然我们强调重要数据要挂载 Volume，但容器在运行过程中，可写层依然会产生很多东西。你可以把它理解为容器的\*\*“临时草稿纸”**。**
**常见的内容包括：**
**日志文件：如果你的程序把日志写到了容器内的某个文件（比如 /var/log/app\.log），而没有重定向到控制台，这些日志就存在可写层。**
**临时文件 \(/tmp\)：很多程序运行过程中产生的临时缓存、Socket 文件、锁文件。**
**配置文件微调：比如你进容器执行了 vi /etc/nginx/nginx\.conf 改了一行配置。**
**运行时安装的包：比如你临时在容器里执行了 apt\-get install vim，新装的编辑器就在可写层。**
**应用生成的缓存：比如前端打包时产生的 \.cache 文件夹，或后端生成的图片缩略图（如果没有指定存储路径）。**
**结论：可写层存的是**“不打算长久保存、随用随丢”\*\*的所有变动。

一句话：**UnionFS 负责「分层存储 \+ 写时复制」——决定文件怎么存、怎么共享。**

### 6\.4 容器运行时与架构分层（OCI 标准）

很多人以为「Docker」是一个东西，其实它是一摞分层组件：

```Plaintext
flowchart TB
  CLI["docker (命令行客户端)"] -->|REST API| D["dockerd (守护进程)<br/>管理镜像/网络/卷/构建"]
  D --> C["containerd (容器运行时)<br/>管理容器生命周期、拉取镜像"]
  C --> SHIM["containerd-shim<br/>(每个容器一个，托管其进程)"]
  SHIM --> RUNC["runc (OCI 底层运行时)<br/>真正调用内核 namespace/cgroups"]
  RUNC --> K["Linux 内核<br/>namespaces · cgroups · OverlayFS"]
```

- **runc**：符合 **OCI（开放容器倡议）运行时规范**的底层工具，真正去操作内核把容器创建出来。

- **containerd**：高一层运行时，被 Kubernetes 等直接调用。

- **dockerd \+ CLI**：我们日常交互的部分。

- **OCI 标准**分两块：镜像规范（镜像长什么样）和运行时规范（怎么把它跑起来）。正因为有标准，Kubernetes 后来「不再需要 Docker」其实是不再需要最上面那层，底下照样用 containerd / runc。

类比：角色分工（餐厅模型）：
CLI \(你敲的命令\)：是顾客。你点了一道菜：docker run 鱼香肉丝。
dockerd \(管家\)：是大堂经理。他负责收钱、查菜单（管理镜像）、看有没有空位（网络/卷管理）。他穿得西装革履，但不下厨。
containerd \(领班\)：是后厨负责人。他不关心顾客是谁，他只管备料（拉取镜像）、盯着厨师干活（管理容器生命周期）。
containerd\-shim \(保姆\)：是专门伺候这道菜的服务员。即使经理（dockerd）请假了，领班（containerd）去开会了，只要这个服务员还在，这道菜（容器进程）就能继续在桌上摆着，不会被收走。
runc \(厨师\)：是真正掌勺的人。他只干一件事：开火、放油、炒菜（调用内核 Namespace/Cgroups）。菜一炒好，他就立刻去休息了（进程启动完 runc 就退出）。
Linux 内核 \(大地\)：是火、水、灶台。没有这些基础资源，谁也别想做饭。

架构分层 \(6\.4\) 是为了\*\*“模块化”\*\*。你可以像拼乐高一样换掉底层的工具，而不影响上层的操作。

### 6\.5 安全边界（补充，理解容器隔离的局限）

容器隔离不只靠 namespace \+ cgroups，还叠了几层防护：

- **Capabilities**：把 root 的「超级权限」拆成几十个小权限，容器默认只给一个安全子集。\(特权拆分\)

- **Seccomp**：过滤容器能调用的系统调用，封掉危险的。\(系统调用过滤\)

- **AppArmor / SELinux**：强制访问控制，进一步约束容器行为。\(行为准则\)

但要清醒认识：**容器共享内核，隔离强度天生不如虚拟机**。内核一旦有漏洞，理论上可能「逃逸」。所以强隔离/多租户场景会用更重的方案（如轻量虚拟机 Kata、gVisor）。

### 6\.6 把原理串起来：`docker run` 全流程

```Plaintext
sequenceDiagram
  participant U as 用户
  participant D as dockerd
  participant R as Registry 仓库
  participant F as OverlayFS
  participant K as Linux 内核 (runc)
  U->>D: docker run --gpus all ... 镜像
  D->>D: 检查本地是否有镜像
  D->>R: 本地没有 → 逐层拉取只读层
  R-->>D: 返回各只读镜像层
  D->>F: 叠加只读层 + 新建可写层 → merged
  D->>K: runc 创建一组 namespace（隔离视图）
  D->>K: 配置 cgroups（限制 CPU/内存/GPU 等）
  K->>K: 在隔离环境中启动 CMD/ENTRYPOINT 进程
  K-->>U: 容器运行中（其实是被布置过的普通进程）
```

**结论（请记一辈子）**：容器 = 一个被 **Namespace 隔离了视图**、被 **Cgroups 限制了资源**、跑在 **UnionFS 分层文件系统**上的、由 **runc** 启动的**普通 Linux 进程**。

### 📝 第六部分小测（核心，建议全做）

**单选题**

1. Namespace（命名空间）在容器中扮演的角色是？

    - A\. 限制容器能用多少 CPU 和内存

    - B\. 隔离视图——让容器只能看到分配给它的进程、网络、挂载点等

    - C\. 把镜像分层存储

    - D\. 加密容器内的数据

2. 你在容器内 `ps` 看到主进程是 PID 1，但在宿主机上它是个大编号普通进程。这体现了哪种 namespace？

    - A\. NET namespace

    - B\. MNT namespace

    - C\. PID namespace

    - D\. USER namespace

3. Cgroups 的核心作用是？

    - A\. 决定容器能「看到」什么

    - B\. 限制和统计一组进程能「使用」多少 CPU、内存、IO 等资源

    - C\. 负责镜像的分层

    - D\. 负责容器间网络通信

4. 容器内存超过 cgroups 设定的上限时，通常会发生什么？

    - A\. 自动扩容内存

    - B\. 触发内核 OOM Killer，进程被杀掉

    - C\. 容器自动迁移到别的机器

    - D\. 什么都不会发生

5. 关于 OverlayFS 的「写时复制（Copy\-on\-Write）」，正确的是？

    - A\. 修改只读层的文件时直接改原层

    - B\. 修改时先把文件复制到可写层再改，原始只读层不动

    - C\. 每个容器都要复制一份完整镜像

    - D\. 可写层是只读的

6. 从同一个镜像启动 100 个容器，磁盘占用情况大致是？

    - A\. 占用 100 份完整镜像的空间

    - B\. 共享同一份只读镜像层，各自只额外加一个很小的可写层

    - C\. 完全不占用磁盘

    - D\. 占用 100 份但会自动压缩

7. 真正调用内核 namespace / cgroups 把容器创建出来的最底层组件是？

    - A\. docker CLI

    - B\. dockerd

    - C\. containerd

    - D\. runc

**解答题**

8. 用一句话概括「容器的本质是什么」。

9. 解释为什么从同一镜像启动多个容器既省磁盘、启动又快，又为什么容器里的改动默认不会持久化——把这三件事用同一个机制串起来说明。

📖 参考答案

1. **B**　2\. **C**　3\. **B**　4\. **B**　5\. **B**　6\. **B**　7\. **D**

8. 容器是**一个被 Namespace 隔离了视图、被 Cgroups 限制了资源、跑在 UnionFS 分层文件系统上、由 runc 启动的普通 Linux 进程**。

9. 三件事的共同机制是**联合文件系统的分层 \+ 写时复制**：镜像的只读层是**共享**的，多个容器共用同一份，所以不占多份磁盘（省空间）；启动容器只需在顶部加一个**空的可写层**，不必拷贝整个文件系统，所以快；而容器运行时的所有改动都写在这个**会随容器删除而销毁的可写层**里，只读镜像层不变，所以改动默认不持久（需要 Volume 持久化）。

---

## 第七部分　vLLM 的 Docker 部署（实战 \+ 原理）

ollama，vllm两种部署方式

### 7\.1 vLLM 是什么，解决什么问题

vLLM 是一个**高吞吐、内存高效的大语言模型推理与服务引擎**，最初由加州大学伯克利分校团队提出。朴素地跑 LLM 往往 GPU 利用率低、并发差。vLLM 靠两项核心创新解决——下面把原理讲透，并各配一张图。

#### 原理一：PagedAttention（借鉴操作系统的「虚拟内存分页」）

**背景**：LLM 生成文字时，需要把已经算过的 token 的 Key/Value 缓存起来复用，这叫 **KV Cache**，它很吃显存。传统做法是给每个请求预先分配一大块**连续**显存来放 KV Cache。问题来了：

- 你不知道一个回答会多长，只能按最大长度预留 → 大量显存**预留了却没用上**（内部碎片）。

- 不同请求长度不一，连续块之间留下用不上的空隙（外部碎片）。

- 结果：显存利用率常常只有 20%\~40%，浪费惊人。

**PagedAttention 的思路**：完全照搬操作系统管理内存的办法。操作系统不要求进程的内存物理连续，而是切成固定大小的「页」，用「页表」做逻辑地址到物理地址的映射。vLLM 把 KV Cache 切成固定大小的**块（block）**，用一张**块表（block table）记录「逻辑块 → 物理块」的映射。物理块在显存里可以不连续**，哪里有空放哪里，用多少分多少。

效果：几乎消除碎片，显存利用率大幅提升，同样的卡能装下更多并发请求；还能让相同前缀（如相同的 system prompt）的多个请求**共享**同一批物理块，进一步省显存。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MWU3MGI4OWRmN2M3MjI5ODFkYmYyNTQ0Y2U3YTc5NmJfZWI0NWQwZTlhNmU1MTA2NzU1NjJiNGE0MGZhZDkwMGNfSUQ6NzY0ODIyOTIxODgwNzA5MDQxOV8xNzgxNzU5NjI3OjE3ODE4NDYwMjdfVjM)

#### 原理二：Continuous Batching（连续批处理）

**传统静态批处理**：把若干请求凑成一批一起算，必须**等整批里最慢的那个算完**，才能处理下一批。短请求被长请求拖着干等，GPU 空转。

**连续批处理**：以「每生成一个 token」为粒度调度。某个请求一旦生成完毕就立刻离开，腾出的位置**马上**让排队的新请求补进来，GPU 始终满载。吞吐量因此大幅提升。

```Plaintext
flowchart TB
  subgraph STATIC["❌ 静态批处理：等最慢的，GPU 空转"]
    direction LR
    S1["请求A 已完成 → 干等 ⌛"]
    S2["请求B 已完成 → 干等 ⌛"]
    S3["请求C 仍在生成…（拖住整批）"]
    S4["新请求 → 必须等本批全部结束"]
  end
  subgraph CONT["✅ 连续批处理：完成即走，新请求即时补位"]
    direction LR
    C1["请求A 完成 → 立刻离开"]
    C2["空位 → 新请求D 立即补入"]
    C3["请求B/C 继续，GPU 始终满载"]
  end
  STATIC --> CONT
```

#### 对我们最友好的一点

vLLM 提供一个**与 OpenAI API 兼容**的服务端，已有的、调用 OpenAI 接口的代码几乎不用改，把地址指向你自建的 vLLM 服务即可。

> 版本说明：截至 2026 年 5 月，vLLM 已迭代到 0\.22\.x，更新很快（近期常见每一两周一个版本）。教学/生产建议固定版本号而非一直用 `latest`，保证可复现。

### 7\.2 前置条件与部署架构

vLLM 主要面向 **NVIDIA GPU**。部署需要：带 NVIDIA GPU 的 Linux 机器、显卡驱动、Docker，以及关键的 **NVIDIA Container Toolkit**（让容器能访问宿主机 GPU 的桥梁）。整体架构：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OGRjZjhjZTBhYTUyOTRmYjAxZTBkMWViYzNmMWRjODVfODk1OWE4ZWIxMDA5YzBiYzMwYzA4MmE0NmVkNjEyZGVfSUQ6NzY0ODIyOTU1ODczODU1MzgzOF8xNzgxNzU5NjI3OjE3ODE4NDYwMjdfVjM)

先验证容器能否看到 GPU：

```Bash
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi
```

能打印显卡信息即成功；否则先排查 NVIDIA Container Toolkit。

### 7\.3 用官方镜像一行命令起服务

官方地址：https://modelscope\.cn/models/Qwen/Qwen3\-0\.6B

```Bash
docker run --gpus all \
  --name vllm-qwen3-0_6b \
  --memory=10g --memory-swap=10g \
  --shm-size=8g \
  -p 8000:8000 \
  -v /Users/zhangxiaopa/模型目录/Qwen3-0.6B:/models/Qwen3-0.6B:ro \
  vllm/vllm-openai:latest \
  --model /models/Qwen3-0.6B \
  --served-model-name Qwen3-0.6B \
  --gpu-memory-utilization 0.2 \
  --max-model-len 4096
```

参数说明（把命令分成「Docker 参数」和「vLLM 参数」两部分记）：

- `--gpus all`：启用 GPU

- `--name vllm-qwen3-0_6b`：容器命名，后续 `docker logs/stop/rm` 好用

- `--memory=10g --memory-swap=10g`：限制容器内存（避免把宿主机内存吃爆）

- `--shm-size=8g`：调大共享内存（PyTorch/vLLM 进程间通信可能需要）

- `-p 800``0``:8000`：宿主机到容器端口映射（外部访问 API）

- `-v ``Users/zhangxiaopa/模型目录/Qwen3-0.6B:/models/Qwen3-0.6B:ro `：挂载本地模型目录（只读）

- `--model /models/Qwen3-0.6B`：从本地路径加载模型（离线可复现）

- `--served-model-name Qwen3-0.6B`：对外暴露的模型名（请求里的 `model` 用它）

- `--gpu-memory-utilization 0.85`：显存上限（显存紧张时调低更稳）

- `--max-model-len 4096`：最大上下文（过大更容易 OOM）

> 如果你只有 6GB 显存（例如 GTX 1060 6GB），建议把 `--gpu-memory-utilization` 先调到 `0.75~0.85`，并把 `--max-model-len` 降到 `2048~4096`，更稳。

#### 7\.3\.1 用魔搭（ModelScope）把模型下载到本地文件夹并挂载（推荐可复现）

很多课堂/内网环境会更习惯用魔搭下载模型，并把模型权重**固定落盘**到项目目录或专门的模型盘里。思路是：

- **本地先下载**：把 `Qwen3-0.6B` 下载到一个固定目录（例如 `D:\hpf-learning\models\Qwen3-0.6B`）

- **容器只读挂载**：用 `-v` 把这个目录挂到容器里

- **vLLM 用本地路径加载**：`--model /models/Qwen3-0.6B`

在宿主机先安装并下载（以魔搭实际模型 ID 为准，常见写法类似 `Qwen/Qwen3-0.6B`）：

```Bash
pip install -U modelscope

python -c "from modelscope.hub.snapshot_download import snapshot_download; snapshot_download('Qwen/Qwen3-0.6B', local_dir='/Users/zhangxiaopa/模型目录/Qwen3-0.6B')"
```

```Python
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download(
    model_id='Qwen/Qwen3-0.6B',
    local_dir='/Users/zhangxiaopa/模型目录/Qwen3-0.6B'
)
```

说明：

- 第一行安装魔搭 SDK（ModelScope）

- 第二行把模型下载到 `/Users/zhangxiaopa/模型目录/Qwen3-0.6B`（路径可自行替换；模型 ID 以魔搭实际为准）

然后用 Docker 跑（Windows PowerShell 示例，把本地目录挂到容器 `/models`，并限制内存 \+ 起个名字）：

```Bash
docker run --runtime nvidia --gpus all `
  --name vllm-qwen3-0_6b `
  --memory=10g --memory-swap=10g `
  --shm-size=8g `
  -p 8000:8000 `
  -e VLLM_USE_MODELSCOPE=true `
  -v D:\hpf-learning\models:/root/.cache/modelscope `
  vllm/vllm-openai:latest `
  --model Qwen/Qwen3-0.6B `
  --served-model-name Qwen3-0.6B `
  --gpu-memory-utilization 0.85 `
  --max-model-len 4096
```

说明：这是 Windows PowerShell 写法，用反引号 ``` 只是为了换行排版，效果等同于上一段 bash 命令。

> `:ro` 表示只读挂载，避免容器误写本地模型目录。

逐行拆解（把第三、五部分学的与这里对应）：

|片段|含义（背后的原理）|
|---|---|
|`--gpus all`|经 NVIDIA Container Toolkit 把 GPU 暴露给容器|
|`-v 本地模型目录:/models/...:ro`|把模型权重**固定落盘**并挂到容器里，做到可复现/可离线（呼应 6\.3：容器可写层会丢）|
|`--name ...`|给容器起个名字，后面 `docker logs/stop/rm` 不用记容器 ID|
|`--memory ...`|限制容器可用内存（防止把宿主机内存吃爆）；`--memory-swap` 建议和 `--memory` 一样表示不额外借 swap|
|`-p 8000:8000`|端口映射，外部才能访问（呼应 NET namespace \+ bridge 网络）|
|`--shm-size=8g`|调大共享内存（替代 `--ipc=host`）。vLLM 底层 PyTorch 用共享内存在进程间传数据，默认太小会报错（呼应 IPC namespace）|
|`vllm/vllm-openai:latest`|镜像|
|`--model ...`|模型（本地路径）。配合 `-v` 可做到完全离线可复现|
|`--served-model-name ...`|对外暴露的模型名（你在 `/v1/chat/completions` 里传的 `model` 字段）|
|`--gpu-memory-utilization ...`|显存占用上限（0\~1），显存紧张时调低更稳|

> 共享内存：`--ipc=host` 与 `--shm-size=8g` 二选一即可；课堂建议用 `--shm-size`，更直观也更“容器化”。
安全：较新版本提供 `vllm-openai-nonroot`（非 root 运行），生产更稳妥（呼应 6\.5）。

#### 7\.3\.2一个重要限制:Mac 上的 vLLM 不能用 Docker 跑

在 Mac 上这条走不通——Metal GPU 访问需要直接的硬件访问,而容器里没有 Metal 的 GPU 透传。所以 vLLM\-Metal 是直接跑在宿主机上的,而不是在容器里。也就是说,那套 `docker run --gpus all` 命令是 NVIDIA 显卡专用的,在 Mac 上不适用。

### 7\.4 用 Docker Compose 部署（推荐长期运行）

```YAML
services:
  vllm:
    image: vllm/vllm-openai:latest           # vLLM 官方镜像
    runtime: nvidia                          # 使用 NVIDIA runtime
    ports: ["8000:8000"]                     # 宿主机:容器 端口映射
    volumes:
      - D:\hpf-learning\models\Qwen3-0.6B:/models/Qwen3-0.6B:ro  # 挂载本地模型目录（只读）
    ipc: host                               # 或改用 shm_size（看你习惯；这里沿用 ipc: host）
    command:
      - "--model"                            # vLLM 参数：模型路径
      - "/models/Qwen3-0.6B"
      - "--served-model-name"                # vLLM 参数：对外模型名
      - "Qwen3-0.6B"
      - "--gpu-memory-utilization"           # vLLM 参数：显存上限
      - "0.85"
      - "--max-model-len"                    # vLLM 参数：最大上下文
      - "4096"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

启动：`docker compose up -d`

### 7\.5 验证服务

```Bash
curl http://localhost:8000/v1/models

curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen3-0.6B","messages":[{"role":"user","content":"你好"}]}'
```

说明：

- 第一条列出服务端可用的模型（看 `served_model_name` 是否出现）

- 第二条做一次最小对话请求，验证推理链路已跑通

Python（OpenAI SDK），关键是 `base_url` 指向本地：

```Python
from openai import OpenAI
# base_url 改成本地 vLLM 服务；api_key 随便填（vLLM 默认不校验）
client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
resp = client.chat.completions.create(
    model="Qwen3-0.6B",  # 必须与 --served-model-name 一致
    messages=[{"role": "user", "content": "用一句话解释 PagedAttention"}],
)
print(resp.choices[0].message.content)
```

### 7\.6 常用引擎参数（按需调优）

|参数|作用|
|---|---|
|`--model`|模型（本地路径）|
|`--gpu-memory-utilization`|显存使用上限 0\~1，吃紧时调低（如 0\.85）|
|`--max-model-len`|最大上下文长度，过大易 OOM|
|`--tensor-parallel-size`|张量并行的 GPU 数（多卡跑大模型）|
|`--dtype`|精度，如 `bfloat16`|
|`--served-model-name`|对外暴露的模型名|

### 7\.7 常见问题排查

- **OOM/显存不足**：调低 `--gpu-memory-utilization`、调小 `--max-model-len`、或换小模型。

- **共享内存报错**：加 `--ipc=host` 或 `--shm-size`。

- **模型加载失败**：检查本地模型目录是否下载完整、挂载路径是否写对（Windows 注意盘符与反斜杠）。

- **容器看不到 GPU**：回 7\.2 用 `nvidia-smi` 验证 Toolkit。

- **通用三板斧**：`docker logs -f` 看日志、`docker exec -it ... bash` 进容器、`docker stats` 看资源。

### 📝 第七部分小测

**单选题**

1. vLLM 的 PagedAttention 主要借鉴了操作系统的哪种思想来管理 KV Cache？

    - A\. 进程调度

    - B\. 虚拟内存分页（页 \+ 页表映射）

    - C\. 文件压缩

    - D\. 中断处理

2. 传统给每个请求预分配一大块连续显存来存 KV Cache，主要问题是？

    - A\. 速度太快

    - B\. 显存碎片严重、大量预留却用不上，利用率低

    - C\. 不支持 GPU

    - D\. 无法对外提供 API

3. 「连续批处理（Continuous Batching）」相比静态批处理的优势是？

    - A\. 必须等整批最慢的请求结束才处理下一批

    - B\. 请求一完成就立刻离开、新请求即时补位，GPU 始终满载、吞吐更高

    - C\. 只能串行处理请求

    - D\. 不需要 GPU

4. 部署命令里 `-v 本地模型目录:/models/...:ro` 的主要目的是？

    - A\. 限制显存

    - B\. 持久化模型权重，避免每次重启容器都重新下载几个 GB 的模型

    - C\. 映射网络端口

    - D\. 设置环境变量

5. `--ipc=host` 的作用是？

    - A\. 暴露 GPU

    - B\. 让容器使用宿主机共享内存，满足 vLLM/PyTorch 进程间通信需求

    - C\. 指定模型名

    - D\. 限制 CPU

6. 显存不足、容器报 OOM 时，下列哪种调整最直接有效？

    - A\. 调高 `--max-model-len`

    - B\. 调低 `--gpu-memory-utilization` 或调小 `--max-model-len`，或换更小的模型

    - C\. 删除 `-v` 挂载

    - D\. 去掉 `--gpus all`

**解答题**

7. vLLM 提供「OpenAI 兼容接口」，这对已有项目的迁移意味着什么好处？

8. 把下面这条命令逐段说明含义：

```Plaintext
docker run --gpus all -v D:\hpf-learning\models\Qwen3-0.6B:/models/Qwen3-0.6B:ro \
  -p 8000:8000 --shm-size=8g \
  vllm/vllm-openai:latest --model /models/Qwen3-0.6B --served-model-name Qwen3-0.6B
```

📖 参考答案

1. **B**　2\. **B**　3\. **B**　4\. **B**　5\. **B**　6\. **B**

7. 意味着原本调用 OpenAI API 的代码**几乎无需改动**，只要把 `base_url` 指向自建的 vLLM 服务地址即可，迁移成本极低。

8. 逐段：

- `--gpus all`：把宿主机所有 NVIDIA GPU 暴露给容器；

- `-v D:\hpf-learning\models\Qwen3-0.6B:/models/Qwen3-0.6B:ro`：挂载本地模型目录（只读），实现离线、可复现；

- `-p 8000:8000`：把容器 8000 端口映射到宿主机，供外部访问 API；

- `--shm-size=8g`：调大共享内存，满足 PyTorch 进程间通信；

- `vllm/vllm-openai:latest`：使用的镜像；

- `--model /models/Qwen3-0.6B`：指定从容器内路径加载模型；

- `--served-model-name Qwen3-0.6B`：对外暴露的模型名（请求里 `model` 字段用它）。

---



