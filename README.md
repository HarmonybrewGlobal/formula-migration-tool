# formula-migration-tool

## 项目介绍

这是个一键搬运 formula 的自动化工具，可以很方便地将 formula 从上游 [Homebrew/homebrew-core](https://github.com/homebrew/homebrew-core) 仓库搬运到下游 [Harmonybrew/homebrew-core](https://atomgit.com/Harmonybrew/homebrew-core) 仓库中。

## 前置要求

请学习 [如何贡献 formula](https://atomgit.com/Harmonybrew/docs/blob/main/zh-CN/contributor/contribute-formula.md)，并至少手动完成一次 formula 贡献。此自动化工具仅供熟练用户使用，未掌握手动贡献流程者请勿使用。

## 使用方法

**1\. 前置准备**

需要在 AtomGit 平台上做这两件事
* Fork 这个仓库：[Harmonybrew/homebrew-core](https://atomgit.com/Harmonybrew/homebrew-core)。
* 去 [访问令牌](https://atomgit.com/setting/token-classic) 界面生成一个访问令牌（token），权限范围需要包含 PR 的读写权限。

<br>

**2\. 拉取 ci-runner 镜像**

本工具依赖 ci-runner 容器，需要先拉取一个最新版本的 ci-runner 镜像

```sh
docker pull swr.cn-north-4.myhuaweicloud.com/harmonybrew/ci-runner:latest
```

> 建议每次使用前都执行一遍 `docker pull`，以确保自己使用的镜像始终处于最新版本。

**3\. 分析 formula 依赖情况和录入情况**

在 ci-runner 容器中执行 `check-migration.py` 脚本

```sh
git clone https://atomgit.com/Harmonybrew/formula-migration-tool.git
cd formula-migration-tool

# 需要将下列参数替换成你的实际信息
# <formula>:     你要检查的 formula 名字
docker run \
  --rm \
  -it \
  -v "$PWD":/workdir \
  -w /workdir \
  swr.cn-north-4.myhuaweicloud.com/harmonybrew/ci-runner:latest \
  python3 check-migration.py <formula>
```

等待脚本运行结束后，你可以在日志中看到分析结果。日志会详细打印这个 formula 的依赖信息，并提示哪些包已经搬运过了、哪些包还没有搬运过。

如果你要的 formula 或者它的级联依赖还没有被搬运，你需要执行下一个步骤，对它们进行搬运。

**4\. 自动化搬运 formula**

在 ci-runner 容器中执行 `auto-migrate.py` 脚本

```sh
git clone https://atomgit.com/Harmonybrew/formula-migration-tool.git
cd formula-migration-tool

# 需要将下列参数替换成你的实际信息
# GITCODE_TOKEN: 第 1 步生成的访问令牌
# GITCODE_USER:  你的 AtomGit 用户名
# GITCODE_EMAIL: 你的 AtomGit 绑定邮箱
# <formula>:     你要搬运的 formula 名字
docker run \
  --rm \
  -it \
  -v "$PWD":/workdir \
  -w /workdir \
  -e GITCODE_TOKEN=xxx \
  -e GITCODE_USER=xxx \
  -e GITCODE_EMAIL=xxx \
  swr.cn-north-4.myhuaweicloud.com/harmonybrew/ci-runner:latest \
  python3 auto-migrate.py <formula>
```

等待脚本运行结束或报错退出
* 如果脚本没有报错，你可以在日志中看到有 PR 链接打印出来，在 [Harmonybrew/homebrew-core](https://atomgit.com/Harmonybrew/homebrew-core) 仓库中也能看到自动生成的 PR，等待维护者评审即可。
* 如果脚本报错了，这意味着这个包需要人工处理（改 formula 或者打补丁），本工具无法处理。
