![](.github/banner.png)

[[About project](https://jwizard.pl/about)]

JWizard is an open-source Discord music bot handling audio content from various multimedia sources
with innovative web player. This repository contains scripts that automate operations in the CI/CD
pipelines of other JWizard projects, as well as standalone scripts used in various JWizard projects.

## Table of content

* [Project modules](#project-modules)
* [Clone and install](#clone-and-install)
* [Create migration](#create-migration)
* [Project arguments](#project-arguments)
* [License](#license)

## Project modules

| Name             | Description                                                                                |
|------------------|--------------------------------------------------------------------------------------------|
| packages_grabber | Parsing and persisting packages used in all JWizard projects.                              |
| db_migrator      | Database migrator framework, modifying structure and data via YAML files with SQL content. |
| cache_version    | Update deployment cache (project version and time) in DB.                                  |

## Clone and install

1. Make sure you have at least Python 3 (tested on 3.14) at your machine.
2. Clone this repository via:

```bash
$ git clone https://github.com/jwizard-bot/jwizard-tools
```

3. Create `.env` file based `example.env` with following properties:

```properties
JWIZARD_VAULT_TOKEN=<token>
JWIZARD_PROXY_VERIFICATION_TOKEN=<proxy server verification token (prevent JS challenge)>
# only for remote_invoker.py script
JWIZARD_SSH_HOST=<SSH host (or ip address)>
JWIZARD_SSH_PORT=<SSH port>
JWIZARD_SSH_USERNAME=<SSH username>
JWIZARD_SSH_KEY=<SSH private key, as raw string without any \n or \r characters>
JWIZARD_SSH_PASSPHRASE=<SSH key passphrase (required keys with passphrase)>
JWIZARD_SSH_OUTPUT_PATH_PREFIX=<prefix, where located artifacts on remote server>
```

4. Prepare Python virtual environment via:

```bash
$ python -m venv .venv
```

5. Activate environment via:

* for UNIX environments:

```bash
$ source .venv/bin/activate
```

* for Windows environments:

```cmd
.\.venv\bin\Activate.ps1
```

> [!TIP]
> If you have an execution policy error, try to execute
> `Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser` in PowerShell.

> [!TIP]
> If you don't have `bin` directory, change path to `.venv/Scripts/activate` and
> `.\.venv\Scripts\Activate.ps1` for UNIX and Windows environments respectively.

6. Install project-related dependencies via:

```bash
$ (venv) pip install -r requirements.txt
```

7. Run script via:

```bash
$ (venv) python src/<project name>.py <arguments>
```

Where `<project name>` is name of the project (defined in *name* column in **Project modules**
table).

> [!TIP]
> If `python` command not working in UNIX-like shells (ex. ZSH), try run via `python3` command.

### Alternative, only for UNIX environments:

Make sure you have required permissions:

```bash
$ sudo chmod +x exec/prepare
$ sudo chmod +x exec/run
```

1. Prepare virtual environment and install dependencies via:

```bash
$ exec/prepare
```

2. Run via:

```bash
$ exec/run <project name> <additional arguments>
```

Where `<project name>` is name of the project (defined in *name* column in **Project modules**
table).

## Create migration

To create migration template file (in UNIX environments), type:

```bash
$ sudo chmod +x exec/create-migration
$ exec/create-migration <migration name> <pipeline> <author>
```

where:

* `<migration name>` is the self descriptive name of the migration file,
* `<pipeline>` is one of the migration base directory (see `--pipeline` argument for `db_migrator`
  project),
* `<author` is migration author persisted in DB. By default, gets author from git property
  `user.name`. Not required.

This script will automatically created new migration template with current date, incremented
migration number and base migration script copied from `migrations/template.yml` file.

## Project arguments

* For `packages_grabber` project:

```
--repo      (required)     // Github repository name and organization: owner/name.
```

* For `db_migrator` project:

```
--pipeline  (required)    // Determine from which directory migrator execute migrations (take: 'infra'
                          // and 'self'). Used for separate migration executions for JWizard Tools and
                          // JWizard Infra (Core and API).
```

* For `cache_version` project:

```
--repo      (required)    // Github repository name and organization: owner/name.
```

* For `project_analyzer` project:

```
--repo      (required)    // Github repository name and organization: owner/name.
```

* For `remote_invoker` project:

```
--name      (required)    // Project identificator (without "jwizard" prefix).
--inputDir  (required)    // Input directory with pre-compiled files.
```

## License

This project is licensed under the AGPL-3.0 License - see the LICENSE file for details.
