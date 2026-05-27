# formula-migration-tool

## Project Overview

This is an automated tool for one-click formula migration, making it easy to move formulas from the upstream [Homebrew/homebrew-core](https://github.com/homebrew/homebrew-core) repository to the downstream [Harmonybrew/homebrew-core](https://atomgit.com/Harmonybrew/homebrew-core) repository.

## Prerequisites

Please review [How to Contribute Formulas](https://atomgit.com/Harmonybrew/docs/blob/main/zh-CN/contributor/contribute-formula.md) and manually contribute a formula at least once. This automation tool is intended for experienced users only; those unfamiliar with the manual contribution process should not use it.

## Usage

**1\. Prerequisites**

You need to do the following two things on the AtomGit platform:
* Fork this repository: [Harmonybrew/homebrew-core](https://atomgit.com/Harmonybrew/homebrew-core).
* Go to the [Access Tokens](https://atomgit.com/setting/token-classic) page to generate an access token. The scope must include read and write permissions for pull requests.

<br>

**2. Pull the ci-runner Image**

This tool relies on the ci-runner container, so you must first pull the latest version of the ci-runner image

```sh
docker pull swr.cn-north-4.myhuaweicloud.com/harmonybrew/ci-runner:latest
```

> It is recommended to run `docker pull` before each use to ensure you are always using the latest version of the image.

**3\. Analyze formula dependencies and registration status**

Execute the `check-migration.py` script in the ci-runner container

```sh
git clone https://atomgit.com/Harmonybrew/formula-migration-tool.git
cd formula-migration-tool

# Replace the following parameters with your actual information
# <formula>:     The name of the formula you want to check
docker run \
  --rm \
  -it \
  -v “$PWD”:/workdir \
  -w /workdir \
  swr.cn-north-4.myhuaweicloud.com/harmonybrew/ci-runner:latest \
  python3 check-migration.py <formula>
```

Once the script finishes running, you can view the analysis results in the logs. The logs will detail the dependencies of this formula and indicate which packages have been migrated and which have not.

If the formula you need or its cascading dependencies have not yet been migrated, you need to proceed to the next step to migrate them.

**4\. Automating Formula Migration**

Execute the `auto-migrate.py` script in the ci-runner container

```sh
git clone https://atomgit.com/Harmonybrew/formula-migration-t
